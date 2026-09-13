import os 
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch
from ddgs import DDGS
from pydantic import BaseModel , Field
from langchain_groq import ChatGroq
import trafilatura

load_dotenv(Path(__file__).parent / ".env")
apikey = os.getenv("TAVILY_API_KEY")

groq_apikey = os.getenv("GROQ_API_KEY")

tavily_search = TavilySearch(
    max_results=5,
    api_key=apikey
)

extractor_llm = ChatGroq(model="openai/gpt-oss-20b" , api_key=groq_apikey)


#################################################################################

def extract_specs_from_text(raw_text: str, car_info: str) -> str:
    """Uses a micro-LLM to clean scraped web content into a rich technical summary."""
    extraction_prompt = f"""
    You are a precise automotive technical data extractor.
    Analyze the following webpage content for the vehicle: {car_info}.

    TASK:
    Extract ALL technical facts, numbers, and conditional notes regarding:
    1. Exact fluid sump/carter capacity in Liters (with/without filter).
    2. Recommended oil viscosities (e.g., 0W-30, 5W-30, 5W-40, 75W-80, 80W-90).
    3. Official OEM specification standards (e.g., PSA B71 2312, VW 507.00, RN0700, API GL-4).
    4. Critical warnings or conditions (e.g., wet-belt timing system, DPF/FAP diesel requirements, high-mileage recommendations).

    CRITICAL INSTRUCTION FOR MULTIPLE VARIANTS:
    If the text contains specs for DIFFERENT variants (e.g., 2WD/4x2 vs. 4x4, Manual vs. Automatic, or Manual Gearbox vs. Rear Axle/Differential/Pont), DO NOT merge or average them. List each variant separately with its exact condition and specs!

    RULES:
    - Do NOT drop warnings, variant distinctions, or conditional notes.
    - Do NOT add marketing fluff, prices, or store links.
    - Format output as a clear bulleted technical summary.

    Webpage Content:
    {raw_text[:4000]}
    """
    response = extractor_llm.invoke(extraction_prompt)
    return response.content

class SearchInput(BaseModel):
    brand: str = Field(description="Car brand, e.g., Renault, Dacia, Volkswagen")
    model: str = Field(description="Car model, e.g., Duster, Golf, Symbol")
    year: int = Field(description="Production year as integer, e.g., 2018")
    engine: str = Field(description="Engine code or displacement, e.g., 1.5 dCi, 1.2 16V")
    fluid_type: str = Field(description="Fluid type: Engine Oil, Gearbox Oil, or Oil Filter")

################################################################################
# tavily search tool
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
    
    query = f"OEM {fluid_type} specification viscosity capacity {name} {model} {year} {refrence} in algeria"

    result = tavily_search.invoke({"query": query})
    
    if isinstance(result, dict) and result.get("answer"):
        return result["answer"]
        
    formatted = []
    results_list = result.get("results", []) if isinstance(result, dict) else []
    for r in results_list[:3]:
        formatted.append(f"- {r.get('title', '')}: {r.get('content', '')}")
        
    return "\n".join(formatted) if formatted else "No technical results found."


#raw ddgs search tool 
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


    query = f"OEM {fluid_type} specification viscosity capacity {name} {model} {year} {refrence} in algeria"
    
    with DDGS(timeout=10) as ddgs:
        results = ddgs.text(query , max_results=5)

    if not results:
        return "No results found."
        
    formatted = []
    for r in results:
        formatted.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n")
    
    return "\n---\n".join(formatted)



#Improved version of DDGS search 
@tool(args_schema=SearchInput)
def ddgs_Search(brand: str, model: str, year: int, engine: str, fluid_type: str) -> str:
    """Searches for technical automotive specifications, deep-scrapes the top sources,
    and returns a structured, noise-free summary of specs and warnings.

    Args:
        brand: The car brand (e.g., Renault, Volkswagen).
        year: Model production year (e.g., 2018).
        model: Specific car model (e.g., Symbol, Golf).
        engine: Engine code or gearbox spec (e.g., 1.2 16V D4F, 2.0 TDI).
        fluid_type: Fluid category (Engine Oil, Gearbox Oil, Oil Filter).
    """
    car_info = f"{brand} {model} {year} {engine}"
    ddgs = DDGS(timeout=10)
    fluid_lower = fluid_type.lower()

    # Dynamic query building targeting exact component types
    if "boite" in fluid_lower or "gearbox" in fluid_lower or "transmission" in fluid_lower:
        query = f'"{brand} {model}" "{engine}" {year} "boite de vitesses" contenance huile viscosite -prix -achat'
    elif "moteur" in fluid_lower or "engine" in fluid_lower:
        query = f'"{brand} {model}" "{engine}" {year} contenance carter huile moteur norme constructeur -prix -achat'
    elif "filtre" in fluid_lower or "filter" in fluid_lower:
        query = f'"{brand} {model}" "{engine}" {year} reference filtre a huile -prix -achat'
    else:
        query = f'"{brand} {model}" "{engine}" {year} contenance carter huile viscosité norme constructeur {fluid_type} -prix -achat'

    print(f"\n[DDGS Query]: {query}")
    results = list(ddgs.text(query, max_results=4)) 

    if not results:
        # Fallback query if first search is too restrictive
        fallback_query = f"{brand} {model} {engine} contenance huile {fluid_type}"
        results = list(ddgs.text(fallback_query, max_results=3)) 

    if not results:
        return "No technical datasheets found for this vehicle configuration."

    summarized_sources = []

    for idx, item in enumerate(results, start=1):
        url = item.get("href")
        title = item.get("title", "")
        
        try:
            downloaded = trafilatura.fetch_url(url)
            scraped_text = trafilatura.extract(
                downloaded, 
                include_tables=True, 
                include_links=False, 
                output_format='txt'
            )

            if scraped_text and len(scraped_text) > 150:
                clean_summary = extract_specs_from_text(scraped_text, car_info)
                summarized_sources.append(f"--- Source {idx} ({title}) ---\n{clean_summary}\n")
            else:
                # Fallback to DDGS snippet if page cannot be scraped
                snippet = item.get("body", "")
                summarized_sources.append(f"--- Source {idx} (Snippet) ---\n{snippet}\n")

        except Exception:
            continue

    return "\n".join(summarized_sources) if summarized_sources else "Failed to extract content from sources."