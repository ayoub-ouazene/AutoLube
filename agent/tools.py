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
import time 

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
    "amazon", "ebay", "aliexpress", "cdiscount", "walmart",
    "facebook", "instagram", "tiktok", "pinterest", "youtube",
    "twitter",  "reddit", "linkedin"
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
    car_info = f"{brand} {model} {engine} {year}".strip()
    car_info_alt = f"{year} {brand} {model} {engine}".strip()
    fluid_lower = fluid_type.lower()

    engine_lower = engine.lower()
    is_diesel = any(d in engine_lower for d in ["dci", "tdi", "hdi", "crdi", "cdti", "d4d", "d-4d", "diesel", "td"])


    # 1. Transmission
    if any(k in fluid_lower for k in ["boite", "gearbox", "transmission"]):
        queries = [
            f"{car_info} boite vitesse transmission contenance viscosite norme",
            f"{car_info_alt} transmission fluid capacity viscosity specification",
            f"{engine} gearbox oil capacity litres type specification",
        ]

    # 2. Oil Filter
    elif any(k in fluid_lower for k in ["filtre", "filter"]):
        queries = [
            f"{car_info} filtre a huile reference OEM catalog",
            f"{car_info_alt} oil filter OEM part number reference",
            f"{engine} oil filter reference OEM number",
        ]

    # 3. Engine Oil
    elif any(k in fluid_lower for k in ["moteur", "engine", "huile"]):
        if is_diesel and year >= 2009:
            queries = [
                f"{car_info} contenance carter huile norme OEM DPF FAP Low SAPS",
                f"{car_info_alt} engine oil capacity viscosity specification DPF",
                f"{engine} engine oil capacity viscosity litres specification",
            ]
        else:
            queries = [
                f"{car_info} contenance carter huile norme OEM",
                f"{car_info_alt} engine oil capacity viscosity specification",
                f"{engine} engine oil capacity viscosity litres specification",
            ]

    # 4. Fallback
    else:
        queries = [
            f"{car_info} {fluid_type} specs",
            f"{car_info_alt} {fluid_type} specification",
            f"{engine} {fluid_type} capacity viscosity specification",
        ]


    raw_results = []
    seen_urls = set()

    try:
        ddgs = DDGS(timeout=15)
        for i, q in enumerate(queries):
            print(f"[DDGS Query {i+1}/{len(queries)}]: {q}")
            try:
                for r in ddgs.text(q, max_results=4):
                    url = r.get("href") or r.get("link") or ""
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        r["_query"] = q
                        raw_results.append(r)
            except Exception as e:
                print(f"[Query {i+1} failed]: {e}")
            if i < len(queries) - 1:
                time.sleep(1.5)

    except Exception as e:
        return f"Search network error: {e}"

    print(f"=== RAW RESULTS COUNT: {len(raw_results)} ===")
    results = sanitize_search_results(raw_results)
    print(f"=== SANITIZED RESULTS COUNT: {len(results)} ===")
    print(results)
    print("======================================results============================")

    # ---- 3. Fallback (unchanged) ----
    if not results:
        fallback_query = f"{brand} {model} {engine} {year} carnet entretien fiche technique"
        print(f"\n[DDGS Fallback Query]: {fallback_query}")
        raw_fallback = list(ddgs.text(fallback_query, max_results=6))
        results = sanitize_search_results(raw_fallback)

    if not results:
        return "No technical datasheets found for this vehicle configuration."

    # ---- 4. Fetch top 3 (unchanged) ----
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

        if sources_count >= 3:
            break

    # ---- 5. Snippet fallback (unchanged, but now snippets come from all 3 queries) ----
    if not scraped_data:
        snippets = []
        for i, item in enumerate(results[:3]):
            body_text = item.get("body") or item.get("snippet") or ""
            snippets.append(f"Snippet {i+1}: {body_text}")
        return "Deep scraping blocked. Raw Snippets:\n" + "\n".join(snippets)

    return "\n\n".join(scraped_data)