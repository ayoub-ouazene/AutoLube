import json
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools import tool

from app.agents.search_agent.tools import ddgs_Search, tavily_Search
from app.agents.prompts import SEARCH_AGENT_SYSTEM_PROMPT
from app.agents.schemas import SearchInput
from app.core.llm_pool import load_keys_from_env, run_with_failover

_pool = load_keys_from_env()

_STRUCT_OUTPUT_INSTRUCTION = (
    "\n\n=== OUTPUT ===\n"
    "You have completed all your searches. You now have NO tools available. "
    "Reply with ONLY the final JSON object described in the RETURN FORMAT "
    "section above. Do not call any tool. Do not write code fences. "
    "Output the raw JSON object as your message content."
)


def _parse_json(raw: str) -> dict:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].lstrip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass
    return {
        "status": "error",
        "reason": "Search agent did not return valid JSON.",
        "raw": raw[:500],
    }


def _to_canonical_specs(specs: dict) -> dict:
    def to_nested(value):
        if value is None:
            return {"primary": [], "alternatives": []}
        if isinstance(value, str):
            return {"primary": [value] if value else [], "alternatives": []}
        if isinstance(value, list):
            return {"primary": value, "alternatives": []}
        if isinstance(value, dict) and "primary" in value:
            return {
                "primary": value.get("primary") or [],
                "alternatives": value.get("alternatives") or [],
            }
        return {"primary": [], "alternatives": []}

    return {
        "oem_specification": to_nested(specs.get("oem_specification")),
        "capacity_liters": to_nested(specs.get("capacity_liters")),
        "viscosity": to_nested(specs.get("viscosity")),
    }


def _all_three_present(payload: dict) -> bool:
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        return False
    specs = payload.get("specs") or {}
    for key in ("oem_specification", "capacity_liters", "viscosity"):
        value = specs.get(key) or {}
        if not (value.get("primary") or []):
            return False
    return True


def _downgrade_if_unusable(payload: dict) -> dict:
    """Downgrade an ok result when stock matching has no usable key."""
    if payload.get("status") != "ok":
        return payload
    specs = payload.get("specs") or {}
    oem_primary = (specs.get("oem_specification") or {}).get("primary") or []
    visc_primary = (specs.get("viscosity") or {}).get("primary") or []
    if not oem_primary and not visc_primary:
        return {
            "status": "no_data",
            "reason": (
                "Aucune spécification OEM ni viscosité fiable n'a pu être extraite "
                "des sources pour ce véhicule. Nous ne pouvons pas garantir un "
                "produit compatible."
            ),
        }
    return payload


def _llm_structure(vehicle_block: str, sources_text: str) -> dict:
    user_message = (
        f"{vehicle_block}\n"
        f"--- SEARCH RESULTS ---\n{sources_text[:9000]}\n--- END SEARCH RESULTS ---"
    )
    messages = [
        SystemMessage(content=SEARCH_AGENT_SYSTEM_PROMPT + _STRUCT_OUTPUT_INSTRUCTION),
        HumanMessage(content=user_message),
    ]

    def _run(model):
        return model.invoke(messages)

    response = run_with_failover(_pool, _run)
    content = response.content
    if isinstance(content, list):
        content = "".join(block.get("text", "") for block in content if isinstance(block, dict))
    return _parse_json(content)


@tool("use_search_agent", args_schema=SearchInput)
def use_search_agent(
    brand: str,
    model: str,
    year: int,
    fluid_type: str,
    engine: str = "",
    gearbox_ref: str = "",
    transmission_type: str = "",
) -> dict:
    """Deterministic search sub-agent.

    Runs DDGS once, structures it with the full search prompt without tools,
    then runs Tavily only when the first structured result is incomplete.
    """
    t0 = time.perf_counter()
    vehicle_block = (
        "Vehicle parameters:\n"
        f"- Brand: {brand}\n"
        f"- Model: {model}\n"
        f"- Year: {year}\n"
        f"- Engine: {engine or '(not provided)'}\n"
        f"- Gearbox reference: {gearbox_ref or '(not provided)'}\n"
        f"- Transmission type: {transmission_type or '(not provided)'}\n"
        f"- Fluid type: {fluid_type}"
    )
    query = {
        "brand": brand,
        "model": model,
        "year": year,
        "fluid_type": fluid_type,
        "engine": engine,
        "gearbox_ref": gearbox_ref,
        "transmission_type": transmission_type,
    }

    t_ddgs = time.perf_counter()
    ddgs_text = ddgs_Search.invoke(query)
    if not isinstance(ddgs_text, str):
        ddgs_text = str(ddgs_text)
    print(f"[TIMING] ddgs: {time.perf_counter() - t_ddgs:.2f}s")

    ddgs_failed = ddgs_text.startswith(("DDGS_ERROR:", "DDGS_NO_RESULTS", "DDGS_NO_CONTENT"))
    first_payload = None
    if not ddgs_failed:
        t_llm1 = time.perf_counter()
        try:
            first_payload = _llm_structure(vehicle_block, ddgs_text)
        except Exception as error:
            print(f"[search_agent] first LLM call failed: {error}")
        print(f"[TIMING] structuring LLM #1: {time.perf_counter() - t_llm1:.2f}s")
        if first_payload and _all_three_present(first_payload):
            first_payload["specs"] = _to_canonical_specs(first_payload.get("specs") or {})
            first_payload.setdefault("warnings", [])
            first_payload.setdefault("clarifications", [])
            first_payload.setdefault("rationale", "")
            first_payload.setdefault("verification", None)
            first_payload.setdefault("confidence", "medium")
            print(f"[TIMING] search_agent total: {time.perf_counter() - t0:.2f}s (DDGS-only)")
            return _downgrade_if_unusable(first_payload)

    t_tav = time.perf_counter()
    tavily_text = tavily_Search.invoke(query)
    if not isinstance(tavily_text, str):
        tavily_text = str(tavily_text)
    print(f"[TIMING] tavily: {time.perf_counter() - t_tav:.2f}s")

    merged = ddgs_text if not ddgs_failed else ""
    if tavily_text and not tavily_text.startswith(("TAVILY_ERROR", "TAVILY_NO_RESULTS")):
        merged = (merged + "\n\n=== SECONDARY SOURCE (TAVILY) ===\n" + tavily_text).strip()
    if not merged:
        return {"status": "error", "reason": "Aucune source n'a répondu pour ce véhicule."}

    t_llm2 = time.perf_counter()
    try:
        second_payload = _llm_structure(vehicle_block, merged)
    except Exception as error:
        print(f"[search_agent] second LLM call failed: {error}")
        return {"status": "error", "reason": f"Structureur indisponible: {error}"}
    print(f"[TIMING] structuring LLM #2: {time.perf_counter() - t_llm2:.2f}s")

    if second_payload.get("status") == "ok":
        second_payload["specs"] = _to_canonical_specs(second_payload.get("specs") or {})
        second_payload.setdefault("warnings", [])
        second_payload.setdefault("clarifications", [])
        second_payload.setdefault("rationale", "")
        second_payload.setdefault("verification", None)
        second_payload.setdefault("confidence", "medium")

    print(f"[TIMING] search_agent total: {time.perf_counter() - t0:.2f}s")
    return _downgrade_if_unusable(second_payload)


Use_Search_Agent = use_search_agent
