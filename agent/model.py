import os 
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from agent.tools import ddgs_Search
from langchain_core.messages import HumanMessage
from agent.prompts import MAIN_AGENT_SYSTEM_PROMPT


try:
    from .tools import Search
except ImportError:  # Supports `python model.py` from the agent directory.
    from tools import Search
    
# Load environment
load_dotenv(Path(__file__).parent / ".env")
apikey = os.getenv("GROQ_API_KEY")

# Initialize LLM
model = ChatGroq(model="openai/gpt-oss-120b", api_key=apikey ,  temperature=0.0 , )


agent = create_agent(
    model=model,
    tools=[ddgs_Search],  
    system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
   

)

def run_chat_session():
    # Store message history for multi-turn conversation
    chat_history = []
    
    print("--- AutoLube AI Assistant Initialized ---")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("Customer: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Append new user message
        chat_history.append(HumanMessage(content=user_input))

        # Invoke agent with full conversation history
        response = agent.invoke({"messages": chat_history})

        # Update chat history with agent's response/tool outputs
        chat_history = response["messages"]

        # Print final text response from agent
        print(f"\nAI Assistant: {chat_history[-1].content}\n")

if __name__ == "__main__":
    run_chat_session()