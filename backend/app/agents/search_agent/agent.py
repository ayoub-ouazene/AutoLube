import json
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools import tool

from app.agents.search_agent.tools import firecrawl_Search, tavily_Search
from app.agents.prompts import SEARCH_SYNTHESIS_SYSTEM_PROMPT
from app.agents.schemas import SearchInput
from app.core.llm_pool import load_keys_from_env, run_with_failover

_pool = load_keys_from_env()


def _parse_json(raw: str) -> dict:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].lstrip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass
    return {"status": "no_data", "reason": "Format de réponse invalide du synthétiseur."}


def _call_synthesiser(vehicle_block: str, summaries: str) -> dict:
    types = [
        line.split("TYPE:")[-1].strip().split()[0]
        for line in summaries.splitlines()
        if line.startswith("TYPE:")
    ]
    print(f"[synthesiser] input: {len(types)} summaries, types={types}")
    print("[synthesiser] input summaries:")
    for line in summaries.split("=== SOURCE:")[1:]:
        head = line.split("\n")[:6]
        print("  ===" + " | ".join(head))
    user_message = (
        f"{vehicle_block}\n--- PAGE SUMMARIES ---\n"
        f"{summaries[:12000]}\n--- END PAGE SUMMARIES ---"
    )
    messages = [
        SystemMessage(content=SEARCH_SYNTHESIS_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    def _run(model):
        return model.invoke(messages)

    response = run_with_failover(_pool, _run)
    content = response.content
    if isinstance(content, list):
        content = "".join(block.get("text", "") for block in content if isinstance(block, dict))
    print(f"[synthesiser] output length={len(content)}")
    return _parse_json(content)


def _merge_primaries(first: dict, second: dict) -> dict:
    """Option C merge: union only specs.<field>.{primary,alternatives}
    plus clarifications and warnings. First wins on value conflicts.
    Metadata (rationale, confidence, verification, status) from second."""
    FIELDS = ("oem_specification", "viscosity", "capacity_liters")

    def _dedup_entries(items):
        out, seen = [], set()
        for it in items or []:
            key = it.get("value") if isinstance(it, dict) else str(it)
            key = (key or "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(it)
        return out

    def _dedup_strings(items):
        out, seen = [], set()
        for it in items or []:
            key = str(it).strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(it)
        return out

    f_specs = first.get("specs") or {}
    s_specs = second.get("specs") or {}
    merged_specs = {}
    for field in FIELDS:
        fb = f_specs.get(field) or {}
        sb = s_specs.get(field) or {}
        merged_specs[field] = {
            "primary":      _dedup_entries((fb.get("primary")      or []) + (sb.get("primary")      or [])),
            "alternatives": _dedup_entries((fb.get("alternatives") or []) + (sb.get("alternatives") or [])),
        }

    return {
        "status":         "ok",
        "specs":          merged_specs,
        "warnings":       _dedup_strings((first.get("warnings")       or []) + (second.get("warnings")       or [])),
        "clarifications": _dedup_strings((first.get("clarifications") or []) + (second.get("clarifications") or [])),
        "rationale":      second.get("rationale")    or first.get("rationale")    or "",
        "verification":   second.get("verification") or first.get("verification") or {},
        "confidence":     second.get("confidence")   or first.get("confidence")   or "medium",
    }


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
    """Search, summarize pages, synthesize specs, and use Tavily if needed."""
    started = time.perf_counter()
    vehicle_block = (
        f"Vehicle parameters:\n- Brand: {brand}\n- Model: {model}\n- Year: {year}\n"
        f"- Engine: {engine or '(not provided)'}\n"
        f"- Gearbox reference: {gearbox_ref or '(not provided)'}\n"
        f"- Transmission type: {transmission_type or '(not provided)'}\n"
        f"- Fluid type: {fluid_type}"
    )
    params = {
        "brand": brand, "model": model, "year": year,
        "fluid_type": fluid_type, "engine": engine,
        "gearbox_ref": gearbox_ref, "transmission_type": transmission_type,
    }

    t_firecrawl = time.perf_counter()
    fc_summaries = firecrawl_Search.invoke(params)
    if not isinstance(fc_summaries, str):
        fc_summaries = str(fc_summaries)
    print(f"[TIMING] firecrawl: {time.perf_counter() - t_firecrawl:.2f}s")

    fc_usable = (
        fc_summaries
        and fc_summaries not in ("FIRECRAWL_NO_RESULTS", "FIRECRAWL_NO_SUMMARIES")
        and not fc_summaries.startswith("FIRECRAWL_ERROR:")
    )

    first_payload = None
    if fc_usable:
        first_payload = _call_synthesiser(vehicle_block, fc_summaries)
        if first_payload.get("status") == "ok":
            specs = first_payload.get("specs") or {}
            oem = (specs.get("oem_specification") or {}).get("primary") or []
            viscosity = (specs.get("viscosity") or {}).get("primary") or []
            if oem and viscosity:
                print(f"[TIMING] search_agent total: {time.perf_counter() - started:.2f}s (Firecrawl-only, complete)")
                return first_payload

    t_tavily = time.perf_counter()
    tavily_summaries = tavily_Search.invoke(params)
    if not isinstance(tavily_summaries, str):
        tavily_summaries = str(tavily_summaries)
    print(f"[TIMING] tavily: {time.perf_counter() - t_tavily:.2f}s")

    tavily_usable = (
        tavily_summaries
        and not tavily_summaries.startswith("TAVILY_ERROR")
        and tavily_summaries not in ("TAVILY_NO_RESULTS", "TAVILY_NO_SUMMARIES")
    )
    if not tavily_usable:
        if first_payload and first_payload.get("status") == "ok":
            return first_payload
        print(f"[TIMING] search_agent total: {time.perf_counter() - started:.2f}s (no data)")
        return {"status": "no_data", "reason": "Aucune source n'a répondu."}

    merged = fc_summaries if fc_usable else ""
    merged = (merged + "\n\n=== SECONDARY SOURCES (TAVILY) ===\n" + tavily_summaries).strip()
    second_payload = _call_synthesiser(vehicle_block, merged)
    if second_payload.get("status") == "ok":
        specs = second_payload.get("specs") or {}
        oem = (specs.get("oem_specification") or {}).get("primary") or []
        viscosity = (specs.get("viscosity") or {}).get("primary") or []
        if oem and viscosity:
            print(f"[TIMING] search_agent total: {time.perf_counter() - started:.2f}s (Firecrawl + Tavily)")
            return second_payload

    # Both syntheses ok but neither returned a complete payload -> merge primaries.
    if (first_payload  and first_payload.get("status")  == "ok"
        and second_payload and second_payload.get("status") == "ok"):
        return _merge_primaries(first_payload, second_payload)

    if first_payload and first_payload.get("status") == "ok":
        return first_payload

    if second_payload and second_payload.get("status") == "ok":
        return second_payload

    return second_payload or first_payload or {
        "status": "no_data",
        "reason": "Aucune donnee technique fiable n'a ete trouvee.",
    }


Use_Search_Agent = use_search_agent
