import os 
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch
from ddgs import DDGS


load_dotenv(Path(__file__).parent / ".env")
apikey = os.getenv("TAVILY_API_KEY")

tavily_search = TavilySearch(
    max_results=5,
    api_key=apikey
)

@tool
def Search(name: str, year: int, model: str, refrence: str, fluid_type: str):
    """Search the internet for exact OEM fluid specifications and oil references for a car.
    
    Args:
        name: The car brand (e.g., Renault, Volkswagen).
        year: Model production year (e.g., 2018).
        model: Specific car model (e.g., Symbol, Golf).
        refrence: Engine code or gearbox spec (e.g., 1.2 16V D4F, 2.0 TDI).
        fluid_type: Fluid category (Engine Oil, Gearbox Oil, Brake Fluid, Coolant).
    """
    
    query = f"OEM {fluid_type} specification viscosity capacity {name} {model} {year} {refrence}"

    result = tavily_search.invoke({"query": query})
    
    if isinstance(result, dict) and result.get("answer"):
        return result["answer"]
        
    formatted = []
    results_list = result.get("results", []) if isinstance(result, dict) else []
    for r in results_list[:3]:
        formatted.append(f"- {r.get('title', '')}: {r.get('content', '')}")
        
    return "\n".join(formatted) if formatted else "No technical results found."



@tool

def Search2(name: str, year: int, model: str, refrence: str, fluid_type: str):
    """Search the internet for exact OEM fluid specifications and oil references for a car.
    
    Args:
        name: The car brand (e.g., Renault, Volkswagen).
        year: Model production year (e.g., 2018).
        model: Specific car model (e.g., Symbol, Golf).
        refrence: Engine code or gearbox spec (e.g., 1.2 16V D4F, 2.0 TDI).
        fluid_type: Fluid category (Engine Oil, Gearbox Oil, Brake Fluid, Coolant).
    """


    query = f"OEM {fluid_type} specification viscosity capacity {name} {model} {year} {refrence}"
    
    with DDGS() as ddgs:
        results = ddgs.text(query , max_results=10)

    if not results:
        return "No results found."
        
    formatted = []
    for r in results:
        formatted.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n")
    
    return "\n---\n".join(formatted)

       