from agent.prompts import MAIN_AGENT_SYSTEM_PROMPT
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from  agent.db_tools.stock_lookup import stock_lookup
from langchain_core.messages import HumanMessage , SystemMessage  , AIMessage
import os 
from pathlib import Path
from dotenv import load_dotenv
from agent.search_agent.agent import use_search_agent

from agent.db_tools.spec_lookup import specs_lookup
from config.apis import main_groq_model , alternative_groq_model , openrouter_model

load_dotenv(Path(__file__).parent.parent / ".env")


main_agent = create_agent(
    model=openrouter_model,
    tools=[use_search_agent, stock_lookup , specs_lookup],
    system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
)

MAX_HISTORY = 8   

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
        "  • l'huile moteur\n"
        "  • l'huile de boîte (transmission)\n"
        "  • le filtre à huile\n"
        "  • le liquide de frein\n\n"
        "Pour commencer, indiquez-moi le véhicule (marque, modèle, année, "
        "code moteur ou boîte) et le type de fluide souhaité.\n"
    )
    print("Type 'exit' to quit.\n")


    while True:
        user_input = input("Customer: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        chat_history.append(HumanMessage(content=user_input))

        # Build the payload: ephemeral vehicle context + trimmed history
        payload = []
        if current_vehicle:
            payload.append(SystemMessage(
                content=(
                    "Contexte véhicule actuel (à utiliser pour référence ; "
                    "réinitialiser si l'utilisateur mentionne un autre véhicule) :\n"
                    f"{current_vehicle}"
                )
            ))
        payload.extend(chat_history[-MAX_HISTORY:])

        response = main_agent.invoke({"messages": payload})
        response_messages = response["messages"]

        # Update the persistent vehicle state from this turn's tool call (if any)
        new_args = extract_vehicle_from_tool_call(response_messages)
        current_vehicle = update_vehicle_state(current_vehicle, new_args)

        # Keep only the AI's final reply in history — drop tool-call plumbing
        ai_reply = response_messages[-1]
        chat_history.append(ai_reply)
        chat_history = _trim_history(chat_history[-MAX_HISTORY:])

        # Print the reply
        last_response = ai_reply.content
        if isinstance(last_response, list):
            last_response = "".join(
                b.get("text", "") for b in last_response if isinstance(b, dict)
            )
        print(f"\nAI Assistant: {last_response}\n")


if __name__ == "__main__":
    run_chat_session()