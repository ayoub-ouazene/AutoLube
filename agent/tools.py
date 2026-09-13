import os 
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch
from ddgs import DDGS
from pydantic import BaseModel , Field
from langchain_groq import ChatGroq
import trafilatura
import requests

load_dotenv(Path(__file__).parent / ".env")
apikey = os.getenv("TAVILY_API_KEY")

groq_apikey = os.getenv("GROQ_API_KEY")

tavily_search = TavilySearch(
    max_results=5,
    api_key=apikey
)

extractor_llm = ChatGroq(model="openai/gpt-oss-20b" , api_key=groq_apikey , temperature=0.0)


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


def fetch_full_page_content(url: str) -> str:
    """Fetches full page body text while bypassing basic bot blocks."""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            extracted = trafilatura.extract(
                response.text, 
                include_tables=True, 
                include_links=False, 
                output_format='txt'
            )
            if extracted and len(extracted) > 200:
                # Return up to 2500 characters of rich main content per source
                return extracted[:2500]
    except Exception:
        pass
    return ""

class SearchInput(BaseModel):
    brand: str = Field(description="Car brand, e.g., Renault, Dacia, Volkswagen")
    model: str = Field(description="Car model, e.g., Duster, Golf, Symbol")
    year: int = Field(description="Production year as integer, e.g., 2018")
    engine: str = Field(description="Engine code or displacement, e.g., 1.5 dCi, 1.2 16V")
    mileage: int = Field(description="Current vehicle mileage in km, e.g., 180000")
    fluid_type: str = Field(description="Fluid type: Engine Oil, Gearbox Oil, or Oil Filter")



# Domains that block scrapers or lack technical specifications
BLOCKED_DOMAINS = [
    "oscaro.com", "piecesauto24.com", "mister-auto.com", 
    "autodoc.fr", "amazon.fr", "ebay.fr", "cdiscount.com"
]



#Improved version of DDGS search 
@tool(args_schema=SearchInput)
def ddgs_Search(brand: str, model: str, year: int, engine: str,  mileage: int, fluid_type: str) -> str:
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

    fluid_lower = fluid_type.lower()

    # Exclude e-commerce catalog pages directly in the search query
    exclude_query = " ".join([f"-site:{domain}" for domain in BLOCKED_DOMAINS])

    if "boite" in fluid_lower or "gearbox" in fluid_lower:
        query = f'"{brand} {model}" "{engine}" {year} "boite" OR "transmission" contenance norme viscosite {exclude_query}'
    elif "moteur" in fluid_lower or "engine" in fluid_lower:
        query = f'"{brand} {model}" "{engine}" {year} contenance carter huile norme constructeur {exclude_query}'
    else:
        query = f'"{brand} {model}" "{engine}" {year} {fluid_type} reference {exclude_query}'

    print(f"\n[DDGS Query]: {query}")

    try:
        ddgs = DDGS(timeout=15)
        results = list(ddgs.text(query, max_results=10)) 
    except Exception as e :
        return f"Search network error: {e}"
    

    print("=== RAW SEARCH TOOL OUTPUT START ===")
    print(results)
    print("=== RAW SEARCH TOOL OUTPUT END ===")

    if not results:
        # Fallback query if first search is too restrictive
        fallback_query = f"{brand} {model} {engine} contenance huile {fluid_type}"
        results = list(ddgs.text(fallback_query, max_results=3)) 

    if not results:
        return "No technical datasheets found for this vehicle configuration."


    scraped_data = []
    sources_count = 0

    for item in results:
        url = item.get("href", "")
        title = item.get("title", "")
        
        # Skip forbidden domains if missed by DDGS operator
        if any(domain in url for domain in BLOCKED_DOMAINS):
            continue

        full_content = fetch_full_page_content(url)
        
        if full_content:
            sources_count += 1
            if  len(full_content)>150 :
                clean_content =  extract_specs_from_text(full_content, car_info)
            else :
                clean_content = full_content 

            scraped_data.append(
                f"=== SOURCE {sources_count}: {title} ===\nURL: {url}\nCONTENT:\n{clean_content}\n"
            )
        
        # Stop once we have 3 deep, rich content pages
        if sources_count >= 3:
            break

    if not scraped_data:
        # Fallback to snippets if all deep scraping failed
        snippets = [f"Snippet {i+1}: {item.get('body')}" for i, item in enumerate(results[:3])]
        return "Deep scraping blocked. Raw Snippets:\n" + "\n".join(snippets)

    return "\n\n".join(scraped_data)
    
