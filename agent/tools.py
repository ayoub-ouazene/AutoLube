import os 
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch
from ddgs import DDGS
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
import trafilatura
import requests
import re
from urllib.parse import urlparse

load_dotenv(Path(__file__).parent / ".env")
apikey = os.getenv("TAVILY_API_KEY")
groq_apikey = os.getenv("GROQ_API_KEY")

tavily_search = TavilySearch(
    max_results=5,
    api_key=apikey
)

extractor_llm = ChatGroq(model="openai/gpt-oss-20b", api_key=groq_apikey, temperature=0.0)

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
    3. Official OEM specification standards (e.g., PSA B71 2312, VW 507.00, RN0700, RN0720, RN17, API GL-4).
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


BLOCKED_BASE_DOMAINS = {
    "oscaro", "autodoc", "auto-doc", "piecesauto24", "piecesauto",
    "mister-auto", "amazon", "ebay", "cdiscount", "partauto",
    "motordoctor", "lacentrale", "caradisiac", "facebook", "instagram",
    "yakarouler", "auto-doc", "piecesauto", "mongrossisteauto", "norauto", "feuvert"
}


def is_domain_blocked(url: str) -> bool:
    """Checks if a URL belongs to an e-commerce or blacklisted domain regardless of TLD."""
    if not url:
        return True
    try:
        netloc = urlparse(url).netloc.lower()
        # Clean subdomain prefixes
        netloc = re.sub(r'^www\.', '', netloc)
        
        # Check against blocked base keywords
        for blocked in BLOCKED_BASE_DOMAINS:
            if blocked in netloc:
                return True
        return False
    except Exception:
        return True  # Block malformed URLs

def sanitize_search_results(results: list[dict]) -> list[dict]:
    """Filters out blacklisted e-commerce domains from raw DDGS outputs."""
    sanitized = []
    for item in results:
        # DDGS sometimes uses 'href', sometimes 'link'
        url = item.get("href") or item.get("link") or ""
        if not is_domain_blocked(url):
            sanitized.append(item)
    return sanitized


@tool(args_schema=SearchInput)
def ddgs_Search(brand: str, model: str, year: int, engine: str, mileage: int, fluid_type: str) -> str:
    """ Searches for technical automotive specifications, deep-scrapes the top sources,
        and returns a structured, noise-free summary of specs and warnings.
    """
    car_info = f"{brand} {model} {year} {engine}"
    fluid_lower = fluid_type.lower()

    # Deterministic query construction geared towards technical documentation
    if "boite" in fluid_lower or "gearbox" in fluid_lower or "transmission" in fluid_lower:
        query = f'{brand} {model} {engine} {year} "fiche technique" OR "manuel" boite vitesse transmission contenance viscosite norme'
    elif "moteur" in fluid_lower or "engine" in fluid_lower or "huile" in fluid_lower:
        query = f'{brand} {model} {engine} {year} "fiche technique" OR "revue technique" contenance carter huile norme OEM'
    else:
        query = f'{brand} {model} {engine} {year} {fluid_type} "reference technique" OR "carnet entretien"'

    print(f"\n[DDGS Deterministic Query]: {query}")

    try:
        ddgs = DDGS(timeout=15)
        raw_results = list(ddgs.text(query, max_results=12)) 
    except Exception as e:
        return f"Search network error: {e}"

    print(f"=== RAW RESULTS COUNT: {len(raw_results)} ===")
    results = sanitize_search_results(raw_results)
    print(f"=== SANITIZED RESULTS COUNT: {len(results)} ===")

    if not results:
        # Informational fallback query without heavy operators
        fallback_query = f"{brand} {model} {engine} {year} carnet entretien fiche technique"
        print(f"\n[DDGS Fallback Query]: {fallback_query}")
        raw_fallback = list(ddgs.text(fallback_query, max_results=6))
        results = sanitize_search_results(raw_fallback)

    if not results:
        return "No technical datasheets found for this vehicle configuration."

    scraped_data = []
    sources_count = 0

    for item in results:
        url = item.get("href") or item.get("link") or ""
        title = item.get("title", "")

        if not url:
            continue

        full_content = fetch_full_page_content(url)
        
        if full_content:
            sources_count += 1
            if len(full_content) > 150:
                clean_content = extract_specs_from_text(full_content, car_info)
            else:
                clean_content = full_content 

            scraped_data.append(
                f"=== SOURCE {sources_count}: {title} ===\nURL: {url}\nCONTENT:\n{clean_content}\n"
            )
        
        # Stop once we have 3 deep technical sources
        if sources_count >= 3:
            break

    if not scraped_data:
        # Fallback to snippets if extraction failed
        snippets = []
        for i, item in enumerate(results[:3]):
            body_text = item.get("body") or item.get("snippet") or ""
            snippets.append(f"Snippet {i+1}: {body_text}")
        return "Deep scraping blocked. Raw Snippets:\n" + "\n".join(snippets)

    return "\n\n".join(scraped_data)