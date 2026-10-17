import time
import re as _re
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


def _normalize_specs(payload: dict) -> dict:
    specs = payload.get("specs") or payload
    normalized = {}
    for field in ("oem_specification", "capacity_liters", "viscosity"):
        value = specs.get(field)
        if isinstance(value, str):
            normalized[field] = {
                "primary": [value] if value else [],
                "alternatives": [],
            }
        elif isinstance(value, list):
            normalized[field] = {"primary": value, "alternatives": []}
        elif isinstance(value, dict):
            normalized[field] = {
                "primary": value.get("primary") or [],
                "alternatives": value.get("alternatives") or [],
            }
        else:
            normalized[field] = {"primary": [], "alternatives": []}
    return normalized


def _canonical_viscosity(value: str) -> str:
    """Normalize to SAE format: 5w30 -> 5W-30, 0W20 -> 0W-20."""
    if not value:
        return value
    normalized = str(value).strip().upper()
    match = _re.match(r"^(\d{1,2})W[-\s]?(\d{2,3})$", normalized)
    if match:
        return f"{match.group(1)}W-{match.group(2)}"
    return normalized


def _canonical_oem(value: str) -> str:
    """Normalize OEM specification letter case while preserving separators."""
    if not value:
        return value
    return str(value).strip().upper()


def _first_spec(specs_data: dict, key: str) -> str:
    value = specs_data.get(key)
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        primary = value.get("primary") or []
        return primary[0] if primary else ""
    return ""


def _vehicle_summary(params: dict) -> str:
    values = [str(params[field]) for field in ("brand", "model", "year", "engine", "gearbox_ref") if params.get(field)]
    return " ".join(values) if values else "Véhicule"


def _build_missing_params_question(missing: list[str]) -> str:
    labels = {"year": "l'année", "engine": "le code moteur", "gearbox_ref": "le code de boîte", "transmission_type": "le type de transmission"}
    requested = [labels[item] for item in missing if item in labels]
    return f"Il me manque : {', '.join(requested)}. Pouvez-vous compléter ?" if requested else "Pouvez-vous préciser les informations de votre véhicule ?"


def _missing_labels(missing: list) -> str:
    labels = {
        "brand": "la marque",
        "model": "le modèle",
        "year": "l'année",
        "engine": "le code moteur",
        "gearbox_ref": "la référence de boîte",
        "transmission_type": "le type de transmission",
    }
    parts = [labels.get(item, item) for item in missing]
    if not parts:
        return "les informations manquantes"
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " et " + parts[-1]


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
            missing = list(intent.get("missing", []))
            current_vehicle = {
                **(current_vehicle or {}),
                **{key: value for key, value in params.items() if value},
                "_last_missing": missing,
            }
            reply, products = _build_missing_params_question(missing), []
        elif flow == "unresolved_missing_params":
            labels = _missing_labels(intent.get("missing", []))
            reply = (
                f"Sans {labels}, je ne peux pas vous proposer une recommandation fiable. "
                "Vous pouvez retrouver cette information dans le carnet d'entretien "
                "du véhicule, auprès du constructeur, ou en contactant notre service "
                "client AutoLube."
            )
            chat_history.append(AIMessage(content=reply))
            chat_history = _trim_history(chat_history[-MAX_HISTORY:])
            return reply, chat_history, current_vehicle, []
        else:
            current_vehicle.pop("_last_missing", None)
            fluid_type = params.get("fluid_type", "")
            specs_source, specs_data = None, None
            warnings, clarifications, verification = [], [], None
            rationale, confidence = "", "medium"
            specs_result = specs_lookup.invoke(params)
            status = specs_result.get("status") if isinstance(specs_result, dict) else None
            if status == "found":
                specs_source = "cache"
                specs_data = specs_result.get("specs")
            elif status in ("not_found", "error"):
                specs_source = "search"
                search_result = use_search_agent.invoke(params)
                search_status = search_result.get("status") if isinstance(search_result, dict) else None
                if search_status == "ok":
                    specs_data = search_result.get("specs")
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
                    print(f"[search_agent] no_data reason: {search_result.get('reason', '')}")
                    reply = (
                        "Je n'ai pas trouvé de spécifications techniques fiables pour "
                        "ce véhicule dans mes sources habituelles. Pour éviter toute "
                        "erreur sur l'huile à utiliser, je vous invite à vérifier "
                        "directement dans le carnet d'entretien de votre véhicule, ou "
                        "à passer en boutique — nous pourrons confirmer la référence "
                        "exacte ensemble."
                    )
                    chat_history.append(AIMessage(content=reply))
                    chat_history = _trim_history(chat_history[-MAX_HISTORY:])
                    return reply, chat_history, current_vehicle, []
                else:
                    reason = search_result.get("reason", "") if isinstance(search_result, dict) else search_result
                    print(f"[search_agent] error reason: {reason}")
                    reply = (
                        "Le service de recherche est momentanément indisponible. "
                        "Veuillez réessayer dans quelques instants, ou consulter "
                        "directement le carnet d'entretien de votre véhicule."
                    )
                    chat_history.append(AIMessage(content=reply))
                    chat_history = _trim_history(chat_history[-MAX_HISTORY:])
                    return reply, chat_history, current_vehicle, []
            if specs_data is not None:
                specs_data = _normalize_specs(specs_data)
                for field in ("oem_specification", "viscosity"):
                    block = specs_data.get(field) or {}
                    for bucket in ("primary", "alternatives"):
                        items = block.get(bucket) or []
                        # Drop empty / whitespace-only entries so the formatter's
                        # "non précisée" fallback fires.
                        items = [item for item in items if item and str(item).strip()]
                        if field == "viscosity":
                            block[bucket] = [_canonical_viscosity(item) for item in items]
                        else:
                            block[bucket] = [_canonical_oem(item) for item in items]
                    specs_data[field] = block
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
