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

from app.core.apis import small_groq_model

from app.agents.schemas import SearchInput 

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
apikey = os.getenv("TAVILY_API_KEY")



tavily_client = TavilyClient(api_key=apikey)

extractor_llm = small_groq_model

TRUSTED_DOMAINS_COMMON = [
    "castrol.com", "liqui-moly.com", "motul.com",
    "totalenergies.com", "auto-abc.eu", "kroon-oil.com",
    "oilspecifications.org", "fuchs.com",
]

TRUSTED_DOMAINS_ENGINE_OIL = TRUSTED_DOMAINS_COMMON

TRUSTED_DOMAINS_GEARBOX = TRUSTED_DOMAINS_COMMON


#################################################################################


def execute_tavily_fallback(car_info: str, query_seed: str , trusted_domains: list) -> str:
    """Internal helper. Runs Tavily (trusted â†’ open web), returns formatted text
    or a TAVILY_ERROR / TAVILY_NO_RESULTS marker."""

    for attempt in (1, 2):
        try:
            response = tavily_client.search(
                query=query_seed,
                max_results=4,
                search_depth="advanced",
                include_domains = trusted_domains ,
                
            )
            results = response.get("results", [])
            print(f"[Tavily] Trusted domains returned {len(results)} results.")

            if not results:
                print("[Tavily] No trusted domain results. Querying open web...")
                response = tavily_client.search(
                    query=f"{car_info} technical specs oil capacity OEM standard",
                    max_results=5,
                    search_depth="advanced",
                    exclude_domains=["amazon.com", "ebay.com", "facebook.com", "youtube.com"],
                )
                results = response.get("results", [])
                print(f"[Tavily] Open web returned {len(results)} results.")

            if not results:
                return "TAVILY_NO_RESULTS"

            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(f"Source {i} ({r.get('title')} - {r.get('url')}):\n{r.get('content')}")


            formatted_text = "\n\n".join(formatted)
            return _sanitize_text_sources(formatted_text)
        
        except Exception as e:
            print(f"âŒ [Tavily Error Caught]: {e}")

            if attempt == 2 :
                return f"TAVILY_ERROR: {e}"
            time.sleep(2)



def extract_specs_from_text(raw_text: str, car_info: str, fluid_type: str) -> str:
    """Uses a micro-LLM to clean scraped web content into a rich technical summary."""
    fluid_lower = fluid_type.lower()

    if any(k in fluid_lower for k in ("boite", "boÃ®te", "gearbox", "transmission")):
        priority = """
        1. OE fluid reference / OEM part number (e.g., VW G 052 512 A2, Renault NFJ / NFX, PSA 9730.A1, Ford WSS-M2C200-D2, MB 235.10).
        2. Viscosity grade (e.g., 75W-80, 75W-90, 80W-90, ATF).
        3. API / ACEA / OEM class (e.g., API GL-4, GL-4+, GL-5, Dexron, Mercon, MTF).
        4. Sump capacity in Liters (with/without filter).
        5. Critical warnings (GL-5 vs yellow metals / synchronizers, ATF vs MTF distinction, manual vs automatic).
        """
    else:
        priority = """
            1. Exact sump/carter capacity in Liters (with/without filter).
            2. Recommended viscosity grade (e.g., 0W-30, 5W-30, 5W-40).
            3. Official OEM specification (e.g., PSA B71 2312, VW 507.00, RN0700 / RN0720 / RN17, MB 229.51, dexos).
            4. Critical warnings (wet-belt timing, DPF/FAP Low-SAPS requirement).
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


def _sanitize_text_sources(text: str) -> str:
    """Strip Source blocks pointing at blacklisted domains from a formatted
    Tavily response."""
    blocks = re.split(r"\n\n(?=Source \d+)", text)
    kept = []
    for b in blocks:
        m = re.search(r"-\s*(https?://\S+)", b)
        if not m:
            continue
        if is_domain_blocked(m.group(1)):
            continue
        kept.append(b)
    return "\n\n".join(kept) if kept else "TAVILY_NO_RESULTS"



@tool(args_schema=SearchInput)
def tavily_Search(
    brand: str,
    model: str,
    year: int,
    fluid_type: str,
    engine: str = "",
    gearbox_ref: str = "",
    transmission_type: str = "",
) -> str:
    """Fallback search tool. Use ONLY when ddgs_Search returned an error marker
    (DDGS_ERROR / DDGS_NO_RESULTS / DDGS_NO_CONTENT) OR when one or more of the
    target values required for the requested fluid_type are missing from the
    ddgs_Search output. The required targets depend on the fluid:
      - Engine Oil  : OEM specification, capacity in liters, viscosity grade.
      - Gearbox Oil : OEM fluid reference, capacity in liters, viscosity grade.
     
    Call at most once per invocation. Both tool outputs remain in context and
    must be merged, with Tavily's values taking precedence on conflicts."""

    base = f"{brand} {model} {year}".strip()
    identifier = (gearbox_ref or engine).strip()
    car_info = f"{base} {identifier}".strip()

    fluid_lower = fluid_type.lower()
    if any(k in fluid_lower for k in ["boite", "boÃ®te", "gearbox", "transmission"]):
        query_seed = f"{car_info} boite de vitesses {transmission_type} huile preconisation specification"
        domains = TRUSTED_DOMAINS_GEARBOX

    else:
        query_seed = f"{car_info} contenance carter huile norme OEM"
        domains = TRUSTED_DOMAINS_ENGINE_OIL

    result = execute_tavily_fallback(car_info, query_seed , domains)
   

    return result 


@tool(args_schema=SearchInput)
def ddgs_Search(brand: str, model: str, year: int,  fluid_type: str , engine: str = "", gearbox_ref: str = "", transmission_type: str = "",) -> str:
    """ Searches for technical automotive specifications, deep-scrapes the top sources,
        and returns a structured, noise-free summary of specs and warnings.
    """

  
    # Base identifiers (no engine, no gearbox â€” added per branch)
    base = f"{brand} {model} {year}".strip()
    base_alt = f"{year} {brand} {model}".strip()

    # For gearbox queries: prefer dedicated gearbox_ref, fall back to engine for legacy calls
    trans_label = transmission_type.strip()
    gearbox_code = f"{gearbox_ref or engine}".strip()
    
    
    fluid_lower = fluid_type.lower()

    engine_lower = engine.lower()
    is_diesel = any(d in engine_lower for d in ["dci", "tdi", "hdi", "crdi", "cdti", "d4d", "d-4d", "diesel"])

    is_gearbox_req = any(k in fluid_lower for k in ["boite", "gearbox", "transmission"])

    _car_parts = [brand, model, year]

    # 1. Transmission / Gearbox
    if is_gearbox_req:
        
        if  not gearbox_code:
             return ("ParamÃ¨tre manquant : rÃ©fÃ©rence/code de boÃ®te requis pour une recherche "
                "d'huile de boÃ®te. Ex. : MQ250, TL4, MA5, DQ250.")
        
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
        engine_part = f"{engine}" if engine else ""

        queries = [
            f"{car_gb} boite de vitesses huile preconisation specification",
            f"{car_gb_alt} transmission gearbox fluid specification recommendation",
            f"{gearbox_code} {engine_part} boite {trans_label} de vitesses huile recommandee capacite".strip(),
        ]


    # 3. Engine Oil
    elif any(k in fluid_lower for k in ["moteur", "engine"]):

        if engine:
                     _car_parts.append(engine)
        car_info = f"{base} {engine}".strip()
        car_info_alt = f"{base_alt} {engine}".strip()
        if is_diesel and year >= 2009:
            queries = [
                f"{car_info} contenance carter huile norme OEM",
                f"{car_info_alt} engine oil capacity viscosity specification ",
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