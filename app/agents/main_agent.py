from app.agents.prompts import MAIN_AGENT_SYSTEM_PROMPT

from app.core.llm_pool import load_keys_from_env, run_with_failover
from app.core.exceptions import (
    AppError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)

from langchain.agents import create_agent
from  app.agents.db_tools.stock_lookup import stock_lookup
from langchain_core.messages import HumanMessage , SystemMessage  , AIMessage
import os 
from pathlib import Path
from dotenv import load_dotenv
from app.agents.search_agent.agent import use_search_agent

from app.agents.db_tools.specs_lookup import specs_lookup
from app.core.apis import main_groq_model , openrouter_model 

load_dotenv(Path(__file__).parent.parent.parent / ".env")

pool = load_keys_from_env()

# main_agent = create_agent(
#     model=main_groq_model,
#     tools=[use_search_agent, stock_lookup , specs_lookup],
#     system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
# )


TOOLS = [use_search_agent, stock_lookup , specs_lookup]


def _translate_llm_error(e: Exception) -> AppError:
    s = str(e).lower()
    if "429" in s or "rate" in s and "limit" in s or "tpm" in s or "rpm" in s:
        return RateLimitError()
    if "timeout" in s or "timed out" in s:
        return ProviderTimeoutError()
    if "503" in s or "502" in s or "upstream" in s or "overloaded" in s:
        return ProviderUnavailableError()
    return AppError()

def invoke_main_agent(messages):
    def _run(model):
        agent = create_agent(
            model=model,
            tools=TOOLS,
            system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
        )
        return agent.invoke({"messages": messages})
    return run_with_failover(pool, _run)

MAX_HISTORY = 8   

def process_turn(user_message: str, history: list, current_vehicle: dict):
    """
    Process a single user message through the main agent.
    Returns (reply_text: str, updated_history: list, updated_vehicle: dict).
    Pure function with respect to inputs - does not read stdin, does not print.
    """
    chat_history = list(history)
    chat_history.append(HumanMessage(content=user_message))

    # Build the payload: ephemeral vehicle context + trimmed history
    payload = []
    if current_vehicle:
        payload.append(SystemMessage(
            content=(
                "Contexte v\u00e9hicule actuel (\u00e0 utiliser pour r\u00e9f\u00e9rence ; "
                "r\u00e9initialiser si l'utilisateur mentionne un autre v\u00e9hicule) :\n"
                f"{current_vehicle}"
            )
        ))
    payload.extend(chat_history[-MAX_HISTORY:])

    try:
        response = invoke_main_agent(payload)
    except AppError:
        raise
    except Exception as e:
        raise _translate_llm_error(e) from e
    response_messages = response["messages"]

    # Update the persistent vehicle state from this turn's tool call (if any)
    new_args = extract_vehicle_from_tool_call(response_messages)
    current_vehicle = update_vehicle_state(current_vehicle, new_args)

    # Keep only the AI's final reply in history - drop tool-call plumbing
    ai_reply = response_messages[-1]
    chat_history.append(ai_reply)
    chat_history = _trim_history(chat_history[-MAX_HISTORY:])

    last_response = ai_reply.content
    if isinstance(last_response, list):
        last_response = "".join(
            b.get("text", "") for b in last_response if isinstance(b, dict)
        )

    return last_response, chat_history, current_vehicle

def extract_vehicle_from_tool_call(response_messages):
    """Scan the turn's messages for a use_search_agent call, return its args dict."""
    for msg in reversed(response_messages):
        for call in getattr(msg, "tool_calls", None) or []:
            if call["name"] == "use_search_agent":
                return call["args"]
    return None

def update_vehicle_state(current_vehicle, new_args):
    """Reset if brand/model changed; otherwise merge non-empty fields."""
    if not new_args:
        return current_vehicle
    if not current_vehicle:
        return dict(new_args)

    brand_changed = new_args.get("brand") and new_args["brand"] != current_vehicle.get("brand")
    model_changed = new_args.get("model") and new_args["model"] != current_vehicle.get("model")

    if brand_changed or model_changed:
        return dict(new_args)

    merged = dict(current_vehicle)
    for k, v in new_args.items():
        if v not in ("", 0, None):
            merged[k] = v
    return merged


def _trim_history(history):
    """Keep only HumanMessage and final AIMessage (no tool calls).
    Drops every ToolMessage and every AIMessage that carries tool_calls."""
    kept = []
    for m in history:
        if isinstance(m, HumanMessage):
            kept.append(m)
        elif isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
            kept.append(m)
    return kept


def run_chat_session():
    # Store message history for multi-turn conversation
    chat_history = []
    current_vehicle = {}
    
    print("--- AutoLube AI Assistant Initialized ---")
    print(
        "Bonjour ! Je suis l'assistant AutoLube. Je peux vous aider avec :\n"
        "  \u2022 l'huile moteur\n"
        "  \u2022 l'huile de bo\u00eete (transmission)\n"
        "  \u2022 le filtre \u00e0 huile\n"
        "  \u2022 le liquide de frein\n\n"
        "Pour commencer, indiquez-moi le v\u00e9hicule (marque, mod\u00e8le, ann\u00e9e, "
        "code moteur ou bo\u00eete) et le type de fluide souhait\u00e9.\n"
    )
    print("Type 'exit' to quit.\n")


    while True:
        user_input = input("Customer: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        last_response, chat_history, current_vehicle = process_turn(
            user_input, chat_history, current_vehicle
        )
        print(f"\nAI Assistant: {last_response}\n")

