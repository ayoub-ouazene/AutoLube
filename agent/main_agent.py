from agent.prompts import MAIN_AGENT_SYSTEM_PROMPT
from langchain_groq import ChatGroq
from langchain.agents import create_agent

from langchain_core.messages import HumanMessage
import os 
from pathlib import Path
from dotenv import load_dotenv
from agent.search_agent.agent import Use_Search_Agent

load_dotenv(Path(__file__).parent / ".env")
apikey2 = os.getenv("GROQ_API_KEY2")


main_model = ChatGroq(model="openai/gpt-oss-120b", api_key=apikey2 ,  temperature=0.0 , )
main_agent = create_agent(
    model=main_model,
    tools=[Use_Search_Agent],
    system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
)




def run_chat_session():
    # Store message history for multi-turn conversation
    chat_history = []
    
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

        # Append new user message
        chat_history.append(HumanMessage(content=user_input))

        # Invoke agent with full conversation history
        response = main_agent.invoke({"messages": chat_history})

        # Update chat history with agent's response/tool outputs
        chat_history = response["messages"]

        # Print final text response from agent
        last_response = chat_history[-1].content
        if isinstance(last_response, list):
            last_response = "".join(b.get("text","") for b in last_response if isinstance(b, dict))

        print(f"\nAI Assistant: {last_response}\n")



if __name__ == "__main__":
    run_chat_session()