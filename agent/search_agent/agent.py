import os 
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from agent.search_agent.tools import ddgs_Search , tavily_Search
from langchain_core.messages import HumanMessage
from agent.prompts import SEARCH_AGENT_SYSTEM_PROMPT
from langchain.tools import tool
from models.Input_schema import SearchInput

from config.apis import main_groq_model , alternative_groq_model , openrouter_model

# Load environment
load_dotenv(Path(__file__).parent.parent.parent / ".env")




search_agent = create_agent(
    model=openrouter_model,
    tools=[ddgs_Search , tavily_Search],  
    system_prompt=SEARCH_AGENT_SYSTEM_PROMPT,
)


@tool("use_search_agent", args_schema=SearchInput)
def use_search_agent( brand: str,model: str, year: int, mileage: int,fluid_type: str, engine: str = "", gearbox_ref: str = "",transmission_type: str = "",) -> dict:
    
    """
        Search and reason over automotive technical specifications.
        Returns a structured dict (JSON-parsed) with keys: status, specs, warnings,
        clarifications, rationale, verification, confidence — or a needs_more_info /
        no_data / error status with a reason.
    """

    user_message = (
        "Vehicle parameters:\n"
        f"- Brand: {brand}\n"
        f"- Model: {model}\n"
        f"- Year: {year}\n"
        f"- Engine: {engine or '(not provided)'}\n"
        f"- Gearbox reference: {gearbox_ref or '(not provided)'}\n"
        f"- Transmission type: {transmission_type or '(not provided)'}\n"
        f"- Mileage: {mileage} km\n"
        f"- Fluid type: {fluid_type}\n"
    )


    try:
        result = search_agent.invoke({"messages":[HumanMessage(content=user_message)]})

    except Exception as e :
        return {"status": "error", "reason": f"Sub-agent invocation failed: {e}"}


    last = result["messages"][-1].content

    if isinstance(last, list):
        last = "".join(b.get("text", "") for b in last if isinstance(b, dict))


    try:
        print(f"answeer of the search agent:{last}")
        return json.loads(last)
    except (json.JSONDecodeError, TypeError) as e:
        print(f"error in json parsing : {e}")
        return {
            "status": "error",
            "reason": "Sub-agent did not return valid JSON.",
            "raw": last[:500] if isinstance(last, str) else str(last)[:500],}






