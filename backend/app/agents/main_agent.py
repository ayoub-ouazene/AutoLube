import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.db_tools.specs_lookup import specs_lookup
from app.agents.db_tools.stock_lookup import stock_lookup
from app.agents.extraction import extract_intent
from app.agents.formatter import format_reply
from app.agents.search_agent.agent import use_search_agent
from app.core.exceptions import AppError, ProviderTimeoutError, ProviderUnavailableError, RateLimitError

load_dotenv(Path(__file__).parent.parent.parent / ".env")
MAX_HISTORY = 8


def _translate_llm_error(error: Exception) -> AppError:
    text = str(error).lower()
    if "429" in text or ("rate" in text and "limit" in text) or "tpm" in text or "rpm" in text:
        return RateLimitError()
    if "timeout" in text or "timed out" in text:
        return ProviderTimeoutError()
    if any(value in text for value in ("503", "502", "upstream", "overloaded")):
        return ProviderUnavailableError()
    return AppError()


def _normalize_specs(specs: dict) -> dict:
    """Return all supported spec fields in nested primary/alternatives form."""
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


def _first_spec(specs_data: dict, key: str) -> str:
    value = specs_data.get(key) or {}
    primary = value.get("primary") or []
    return primary[0] if primary else ""


def _vehicle_summary(params: dict) -> str:
    values = [str(params[field]) for field in ("brand", "model", "year", "engine", "gearbox_ref") if params.get(field)]
    return " ".join(values) if values else "Véhicule"


def _build_missing_params_question(missing: list[str]) -> str:
    labels = {"year": "l'année", "engine": "le code moteur", "gearbox_ref": "le code de boîte", "transmission_type": "le type de transmission"}
    requested = [labels[item] for item in missing if item in labels]
    return f"Il me manque : {', '.join(requested)}. Pouvez-vous compléter ?" if requested else "Pouvez-vous préciser les informations de votre véhicule ?"


def _update_vehicle_state(current_vehicle: dict | None, params: dict) -> dict:
    current_vehicle = current_vehicle or {}
    if not params:
        return current_vehicle
    if not current_vehicle:
        return dict(params)
    changed = any(params.get(field) and params[field] != current_vehicle.get(field) for field in ("brand", "model"))
    if changed:
        return dict(params)
    merged = dict(current_vehicle)
    merged.update({key: value for key, value in params.items() if value not in ("", None, 0)})
    return merged


def _trim_history(history: list) -> list:
    return [message for message in history if isinstance(message, (HumanMessage, AIMessage))]


def process_turn(user_message: str, history: list, current_vehicle: dict):
    """Run one turn through the deterministic two-LLM-call pipeline."""
    started = time.perf_counter()
    chat_history = list(history)
    chat_history.append(HumanMessage(content=user_message))
    try:
        intent = extract_intent(user_message, chat_history, current_vehicle or {})
        flow = intent.get("flow", "conversational")
        params = intent.get("params") or {}
        current_vehicle = _update_vehicle_state(current_vehicle, params)

        if flow == "conversational":
            reply, products = intent.get("reply_hint") or "Bonjour ! Comment puis-je vous aider ?", []
        elif flow == "filter_redirect":
            reply, products = "Je me spécialise dans les huiles moteur et de boîte. Pour un filtre à huile, consultez notre catalogue.", []
        elif flow == "brake_redirect":
            reply, products = "Pour le liquide de frein, veuillez consulter notre catalogue ou contacter le magasin.", []
        elif flow == "out_of_scope":
            reply, products = "Je suis spécialisé dans les huiles moteur et de boîte. Pour les autres produits, consultez notre catalogue.", []
        elif flow == "missing_params":
            reply, products = _build_missing_params_question(intent.get("missing", [])), []
        else:
            fluid_type = params.get("fluid_type", "")
            specs_source, specs_data = None, None
            warnings, clarifications, verification = [], [], None
            rationale, confidence = "", "medium"
            specs_result = specs_lookup.invoke(params)
            status = specs_result.get("status") if isinstance(specs_result, dict) else None
            if status == "found":
                specs_source = "cache"
                specs_data = _normalize_specs(specs_result.get("specs") or {})
            elif status in ("not_found", "error"):
                specs_source = "search"
                search_result = use_search_agent.invoke(params)
                search_status = search_result.get("status") if isinstance(search_result, dict) else None
                if search_status == "ok":
                    specs_data = _normalize_specs(search_result.get("specs") or {})
                    warnings = search_result.get("warnings", []) or []
                    clarifications = search_result.get("clarifications", []) or []
                    verification = search_result.get("verification")
                    rationale = search_result.get("rationale", "")
                    confidence = search_result.get("confidence", "medium")
                elif search_status == "needs_more_info":
                    reply = search_result.get("reason") or "Pouvez-vous préciser le modèle exact ?"
                    chat_history.append(AIMessage(content=reply))
                    chat_history = _trim_history(chat_history[-MAX_HISTORY:])
                    return reply, chat_history, current_vehicle, []
                elif search_status == "no_data":
                    reply = search_result.get("reason") or "Aucune donnée technique fiable n'a été trouvée pour ce véhicule."
                    chat_history.append(AIMessage(content=reply))
                    chat_history = _trim_history(chat_history[-MAX_HISTORY:])
                    return reply, chat_history, current_vehicle, []
                else:
                    reply = "Le service de recherche est momentanément indisponible. Veuillez réessayer."
                    chat_history.append(AIMessage(content=reply))
                    chat_history = _trim_history(chat_history[-MAX_HISTORY:])
                    return reply, chat_history, current_vehicle, []
            oem_value = _first_spec(specs_data, "oem_specification") if specs_data else ""
            visc_value = _first_spec(specs_data, "viscosity") if specs_data else ""

            products_status, products = "none", []
            if specs_data and (oem_value or visc_value):
                stock_result = stock_lookup.invoke({
                    "oem_specification": oem_value,
                    "viscosity": visc_value,
                    "capacity_liters": specs_data.get("capacity_liters"),
                    "fluid_type": fluid_type,
                })
                products_status = stock_result.get("status", "none")
                products = stock_result.get("products", []) if products_status == "ok" else []
            elif specs_data:
                products_status = "no_match"
            reply = format_reply(
                vehicle_summary=_vehicle_summary(params), fluid_type=fluid_type,
                specs_source=specs_source, specs_data=specs_data,
                products_status=products_status, products=products,
                warnings=warnings, clarifications=clarifications,
                verification=verification, rationale=rationale,
                confidence=confidence,
                fallback_message="Les spécifications n'ont pas pu être trouvées." if not specs_data else "",
            )

        chat_history.append(AIMessage(content=reply))
        chat_history = _trim_history(chat_history[-MAX_HISTORY:])
        print(f"[TIMING] process_turn total: {time.perf_counter() - started:.2f}s")
        return reply, chat_history, current_vehicle, products
    except AppError:
        raise
    except Exception as error:
        raise _translate_llm_error(error) from error


def run_chat_session():
    chat_history, current_vehicle = [], {}
    print("--- AutoLube AI Assistant Initialized ---")
    print("Bonjour ! Je peux vous aider avec l'huile moteur et l'huile de boîte.")
    print("Type 'exit' to quit.\n")
    while True:
        user_input = input("Customer: ")
        if user_input.lower() in ("exit", "quit"):
            break
        reply, chat_history, current_vehicle, products = process_turn(user_input, chat_history, current_vehicle)
        print(f"\nAI Assistant: {reply}\n")
        if products:
            print(f"[DEBUG] {len(products)} produit(s) recommandé(s)")
