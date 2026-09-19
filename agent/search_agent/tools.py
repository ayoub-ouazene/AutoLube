import os 
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch
from tavily import TavilyClient
from ddgs import DDGS
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
import trafilatura
import requests
import re
from urllib.parse import urlparse
import time 

from schema import SearchInput

load_dotenv(Path(__file__).parent.parent / ".env")
apikey = os.getenv("TAVILY_API_KEY")

groq_apikey = os.getenv("GROQ_API_KEY")



tavily_client = TavilyClient(api_key=apikey)

extractor_llm = ChatGroq(model="openai/gpt-oss-20b", api_key=groq_apikey, temperature=0.0)

TRUSTED_DOMAINS = [
   "castrol.com", "liqui-moly.com", "motul.com", 
    "totalenergies.com", "auto-abc.eu", "kroon-oil.com", "oilspecifications.org"
]

#################################################################################


def execute_tavily_fallback(query: str, car_info: str) -> str:
    """Executes Tavily search using the official Python SDK."""
    print(f"\n[Tavily Fallback Triggered]: {query}")
    try:
        # 1. Search restricted to trusted lubricant databases
        response = tavily_client.search(
            query=query,
            max_results=4,
            search_depth="basic",
            include_domains=TRUSTED_DOMAINS
        )
        results = response.get("results", [])
        print(f"[Tavily] Trusted domains returned {len(results)} results.")

        # 2. If restricted domains return nothing, try open web search
        if not results:
            print("[Tavily] No trusted domain results. Querying open web...")
            response = tavily_client.search(
                query=f"{car_info} technical specs oil capacity OEM standard",
                max_results=4,
                search_depth="basic",
                exclude_domains=["amazon.com", "ebay.com", "facebook.com", "youtube.com"]
            )
            results = response.get("results", [])
            print(f"[Tavily] Open web returned {len(results)} results.")

        if not results:
            return "No technical data found via primary or secondary search."

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"Source {i} ({r.get('title')} - {r.get('url')}):\n{r.get('content')}")

        return "\n\n".join(formatted)

    except Exception as e:
        print(f"❌ [Tavily Error Caught]: {e}")
        return f"Secondary search error: {str(e)}"



def extract_specs_from_text(raw_text: str, car_info: str, fluid_type: str) -> str:
    """Uses a micro-LLM to clean scraped web content into a rich technical summary."""
    fluid_lower = fluid_type.lower()

    if any(k in fluid_lower for k in ("boite", "boîte", "gearbox", "transmission")):
        priority = """
        1. OE fluid reference / OEM part number (e.g., VW G 052 512 A2, Renault NFJ / NFX, PSA 9730.A1, Ford WSS-M2C200-D2, MB 235.10).
        2. Viscosity grade (e.g., 75W-80, 75W-90, 80W-90, ATF).
        3. API / ACEA / OEM class (e.g., API GL-4, GL-4+, GL-5, Dexron, Mercon, MTF).
        4. Sump capacity in Liters (with/without filter).
        5. Critical warnings (GL-5 vs yellow metals / synchronizers, ATF vs MTF distinction, manual vs automatic).
        """
    elif any(k in fluid_lower for k in ("filtre", "filter")):
        priority = """
        1. Exact OE part number (e.g., 7700274177, 06A115561B, 8200768913).
        2. Aftermarket reference (e.g., MANN W 712/95, Purflux LS924, Bosch F026407...).
        3. Filter type (spin-on, cartridge, housing) and thread/height if listed.
        4. Compatibility notes (engine code, year range, variant).
        """
    else:
        priority = """
            1. Exact sump/carter capacity in Liters (with/without filter).
            2. Recommended viscosity grade (e.g., 0W-30, 5W-30, 5W-40).
            3. Official OEM specification (e.g., PSA B71 2312, VW 507.00, RN0700 / RN0720 / RN17, MB 229.51, dexos).
            4. Critical warnings (wet-belt timing, DPF/FAP Low-SAPS requirement, high-mileage adjustment).
            """

    extraction_prompt = f"""You are a precise automotive technical data extractor.
            Analyze the following webpage content for the vehicle: {car_info}.
            Requested fluid type: {fluid_type}

            TASK:
            Extract ALL technical facts, numbers, and conditional notes. Prioritize in this order:
            {priority}

            CRITICAL INSTRUCTION FOR MULTIPLE VARIANTS:
            If the text contains specs for DIFFERENT variants (e.g., 2WD/4x2 vs. 4x4, Manual vs. Automatic, Manual Gearbox vs. Rear Axle / Differential / Pont, different engine codes or years), DO NOT merge or average them. List each variant separately with its exact condition and specs.

            RULES:
            - Do NOT invent values. If a fact is not present in the text, omit it.
            - Do NOT drop warnings, variant distinctions, or conditional notes.
            - Do NOT add marketing fluff, prices, or store links.
            - Format output as a clear bulleted technical summary.

            Webpage Content:
            {raw_text[:3000]}
            """
    response = extractor_llm.invoke(extraction_prompt)
    content = response.content
    if isinstance(content, list):  # newer LangChain returns content blocks
        content = "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return content
    


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
                return extracted[:3000]
    except Exception as  e:
        print(url, type(e).__name__)
        pass
    return ""


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
        netloc = re.sub(r'^www\.', '', netloc)
        
        for blocked in BLOCKED_BASE_DOMAINS:
            if blocked in netloc:
                return True
        return False
    except Exception:
        return True 

def sanitize_search_results(results: list[dict]) -> list[dict]:
    """Filters out blacklisted e-commerce domains from raw DDGS outputs."""
    sanitized = []
    for item in results:
        url = item.get("href") or item.get("link") or ""
        if not is_domain_blocked(url):
            sanitized.append(item)
    return sanitized




import re


def is_data_sufficient(text: str, fluid_type: str) -> bool:
    """
    Car-agnostic check to verify if scraped text contains enough technical data
    for the requested fluid type.
    """
    if not text or len(text.strip()) < 150:
        return False

    text_lower = text.lower()
    fluid_lower = fluid_type.lower()

    is_filter  = any(k in fluid_lower for k in ("filtre", "filter"))
    is_gearbox = any(k in fluid_lower for k in ("boite", "boîte", "gearbox", "transmission"))

    # 1. Universal Capacity Pattern
    capacity_pattern = r'(\b\d+[\.,]?\d*\s*(l|litre|litres|liter|liters|qt|quarts)\b|\b(contenance|carter|capacity|sump)\b.*?\b\d+[\.,]?\d*\b)'
    has_capacity = bool(re.search(capacity_pattern, text_lower))

    # 2. Universal Viscosity Pattern (engine + gear grades)
    viscosity_pattern = r'\b(0|5|10|15|20|70|75|80|85)w[-_]?(16|20|30|40|50|60|80|90|110|140)\b'
    has_viscosity = bool(re.search(viscosity_pattern, text_lower))

    # 3. Universal Spec Keywords (fluid-agnostic)
    spec_keywords = [
        r'\bacea\b', r'\bapi\b', r'\bilsac\b', r'\bsae\b', r'\bjaso\b',
        r'\bgl[- ]?[45]\b', r'\batf\b', r'\bmtf\b', r'\bcvt\b', r'\bdsg\b',
        r'\bdexron\b', r'\bmercon\b',
        r'\b(norme|norm|specification|spec|approval|homologation|oem|standard|reference|part number)\b'
    ]
    has_spec_keyword = any(re.search(p, text_lower) for p in spec_keywords)

    # 4. Oil Filter: no capacity/viscosity — look for a part reference
    if is_filter:
        filter_pattern = r'\b(oc|op|ph|hu|wl|w)\s?-?\d{2,5}\b|\b\d{6,}[a-z0-9]{0,4}\b'
        return bool(re.search(filter_pattern, text_lower))

    # 5. Gearbox Oil: capacity OR gear viscosity, AND a spec keyword
    if is_gearbox:
        return (has_capacity or has_viscosity) and has_spec_keyword

    # 6. Engine Oil (default): capacity AND (viscosity OR spec keyword)
    return has_capacity and (has_viscosity or has_spec_keyword)




@tool(args_schema=SearchInput)
def tavily_Search():



@tool(args_schema=SearchInput)
def ddgs_Search(brand: str, model: str, year: int,  mileage: int, fluid_type: str , engine: str = "", gearbox_ref: str = "", transmission_type: str = "",) -> str:
    """ Searches for technical automotive specifications, deep-scrapes the top sources,
        and returns a structured, noise-free summary of specs and warnings.
    """

  
    # Base identifiers (no engine, no gearbox — added per branch)
    base = f"{brand} {model} {year}".strip()
    base_alt = f"{year} {brand} {model}".strip()

    # For gearbox queries: prefer dedicated gearbox_ref, fall back to engine for legacy calls
    trans_label = transmission_type.strip()
    gearbox_code = f"{gearbox_ref or engine} {trans_label}".strip()
    
    
    fluid_lower = fluid_type.lower()

    engine_lower = engine.lower()
    is_diesel = any(d in engine_lower for d in ["dci", "tdi", "hdi", "crdi", "cdti", "d4d", "d-4d", "diesel"])

    is_gearbox_req = any(k in fluid_lower for k in ["boite", "gearbox", "transmission"])

    _car_parts = [brand, model, year]

    # 1. Transmission / Gearbox
    if is_gearbox_req:
        
        if  not gearbox_code:
             return ("Paramètre manquant : référence/code de boîte requis pour une recherche "
                "d'huile de boîte. Ex. : MQ250, TL4, MA5, DQ250.")
        
        parts = [base]
        if gearbox_code:
            parts.append(gearbox_code)
            _car_parts.append(gearbox_code)
        if trans_label:
            parts.append(trans_label)
            _car_parts.append(trans_label)

        car_gb = " ".join(parts).strip()

        parts_alt = [base_alt]
        if gearbox_code:
            parts_alt.append(gearbox_code)
        if trans_label:
            parts_alt.append(trans_label)
    
        car_gb_alt = " ".join(parts_alt).strip()
        engine_part = f" {engine}" if engine else ""

        queries = [
            f"{car_gb} boite de vitesses huile preconisation specification",
            f"{car_gb_alt} transmission gearbox fluid specification recommendation",
            f"{gearbox_code}{engine_part} boite de vitesses huile recommandee capacite".strip(),
        ]



    # 2. Oil Filter
    elif any(k in fluid_lower for k in ["filtre", "filter"]):

        if engine:
             _car_parts.append(engine)

        car_info_f = f"{base} {engine}".strip()
        car_info_f_alt = f"{base_alt} {engine}".strip()
        queries = [
            f"{car_info_f} filtre a huile reference OEM catalog",
            f"{car_info_f_alt} oil filter OEM part number reference",
            f"{engine} oil filter reference OEM number",
        ]

    # 3. Engine Oil
    elif any(k in fluid_lower for k in ["moteur", "engine"]):

        if engine:
                     _car_parts.append(engine)
        car_info = f"{base} {engine}".strip()
        car_info_alt = f"{base_alt} {engine}".strip()
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
        if engine:
                     _car_parts.append(engine)
        queries = [
            f"{base} {fluid_type} specs",
            f"{base_alt} {fluid_type} specification",
            f"{engine} {fluid_type} capacity viscosity specification",
        ]


    car_info = " ".join(str(p) for p in _car_parts if p).strip()
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
        print(f"DDGS Network Error: {e}")
        return execute_tavily_fallback(queries[0], car_info)

    print(f"=== RAW RESULTS COUNT: {len(raw_results)} ===")
    results = sanitize_search_results(raw_results)
    print(f"=== SANITIZED RESULTS COUNT: {len(results)} ===")


    # If DDGS still yielded no results, switch to Tavily
    if not results:
        return execute_tavily_fallback(queries[0], car_info)

    scraped_data = []
    sources_count = 0

    for item in results:
        url = item.get("href") or item.get("link") or ""
        title = item.get("title", "")

        if not url:
            continue

        full_content = fetch_full_page_content(url)

        if full_content:

            sources_count+=1 
            if len(full_content) > 150:
                try: 
                    clean_content = extract_specs_from_text(full_content, car_info,fluid_type)
                except Exception as e:
                    clean_content = full_content
                    print(f"Error in extractor Model : {e}")    

            else:
                clean_content = full_content

            scraped_data.append(
                f"=== SOURCE {sources_count}: {title} ===\nURL: {url}\nCONTENT:\n{clean_content}\n"
            )

        if sources_count >= 5:
            break

    # Snippet Fallback if deep scraping fails
    if not scraped_data:
        snippets = []
        for i, item in enumerate(results[:3]):
            body_text = item.get("body") or item.get("snippet") or ""
            snippets.append(f"Snippet {i+1}: {body_text}")


        output_text = "Deep scraping blocked. Raw Snippets:\n" + "\n".join(snippets)

    else:
        output_text = "\n\n".join(scraped_data)

    return output_text