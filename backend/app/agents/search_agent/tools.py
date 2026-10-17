import os 
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch
from tavily import TavilyClient
from ddgs import DDGS
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from firecrawl import Firecrawl
from langchain_core.messages import HumanMessage
import trafilatura
import requests
import re
import re as _re
from urllib.parse import urlparse
import time 
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.apis import small_groq_model

from app.agents.prompts import PAGE_EXTRACTION_PROMPT
from app.agents.schemas import SearchInput
from app.core.llm_pool import load_keys_from_env, run_with_failover

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
apikey = os.getenv("TAVILY_API_KEY")
_firecrawl_client = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))



tavily_client = TavilyClient(api_key=apikey)

extractor_llm = small_groq_model
_page_pool = load_keys_from_env()

_OEM_NORMALIZERS = [
    (_re.compile(r"\b(?:psa\s*)?b71[\s\-_]*(\d{4})\b", _re.IGNORECASE),
     lambda match: f"PSA B71 {match.group(1)}"),
    (_re.compile(r"\bg[\s\-_]*0(\d{2})[\s\-_]*(\d{3})[\s\-_]*([a-z]\d)\b", _re.IGNORECASE),
     lambda match: f"G 0{match.group(1)} {match.group(2)} {match.group(3).upper()}"),
    (_re.compile(r"\bvw[\s\-_]*5(\d{2})[\s\-_\.]*((?:\d{2}))\b", _re.IGNORECASE),
     lambda match: f"VW 5{match.group(1)}.{match.group(2)}"),
    (_re.compile(r"\bmb[\s\-_]*2(\d{2})[\s\-_\.]*((?:\d{1,2}))\b", _re.IGNORECASE),
     lambda match: f"MB 2{match.group(1)}.{match.group(2)}"),
    (_re.compile(r"\b(?:bmw\s*)?ll[\s\-_]*(\d{2})\b", _re.IGNORECASE),
     lambda match: f"BMW LL-{match.group(1)}"),
    (_re.compile(r"\brn[\s\-_]*(\d{3,4})\b", _re.IGNORECASE),
     lambda match: f"RN{match.group(1)}"),
    (_re.compile(r"\bdexos[\s\-_]*([12])\b", _re.IGNORECASE),
     lambda match: f"Dexos{match.group(1)}"),
    (_re.compile(r"\bwss[\s\-_]*m2c[\s\-_]*(\d{3})[\s\-_]*([a-z])\b", _re.IGNORECASE),
     lambda match: f"WSS-M2C{match.group(1)}-{match.group(2).upper()}"),
    (_re.compile(r"\b9[\s\._]*55535[\s\-_]*([a-z]{2,4})\b", _re.IGNORECASE),
     lambda match: f"9.55535-{match.group(1).upper()}"),
]


def _normalize_oem_codes(text: str) -> str:
    """Canonicalize recognized OEM code shapes; leave other text unchanged."""
    if not text:
        return text
    normalized = text
    for pattern, rewriter in _OEM_NORMALIZERS:
        normalized = pattern.sub(rewriter, normalized)
    return normalized


def _fluid_category_from_summary(summary: str) -> str:
    """Read the page extractor's fluid category, defaulting when absent."""
    for line in summary.splitlines():
        if line.upper().startswith("FLUID_CATEGORY:"):
            value = line.split(":", 1)[1].strip().lower()
            if value in {"engine_oil", "gearbox_oil", "both", "unrelated"}:
                return value
            return "unspecified"
    return "unspecified"


def _extract_page_summary(raw_text: str, car_info: str, fluid_type: str) -> str:
    """Summarize one scraped page using rotating provider keys."""
    prompt = PAGE_EXTRACTION_PROMPT.format(
        car_info=car_info,
        fluid_type=fluid_type,
        raw_text=raw_text[:6000],
    )
    try:
        messages = [HumanMessage(content=prompt)]

        def _run(model):
            return model.invoke(messages)

        response = run_with_failover(_page_pool, _run)
    except Exception as error:
        print(f"[per-page extractor failed]: {error}")
        return ""
    content = response.content
    if isinstance(content, list):
        content = "".join(block.get("text", "") for block in content if isinstance(block, dict))
    return _normalize_oem_codes(content.strip())

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
        response = requests.get(url, headers=headers, timeout=5)
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


def _fetch_and_extract(url: str, car_info: str, fluid_type: str):
    """Return (url, clean_content) or (url, None) on failure."""
    try:
        content = fetch_full_page_content(url)
        if not content:
            return url, None
        try:
            return url, extract_specs_from_text(content, car_info, fluid_type)
        except Exception as error:
            print(f"[scrape] extractor failed for {url}: {error}")
            return url, content
    except Exception as error:
        print(f"[scrape] fetch failed for {url}: {error}")
        return url, None


def _scrape_and_summarize_parallel(candidates, car_info, fluid_type):
    """Scrape candidate URLs in parallel and return formatted summaries."""
    def _scrape_one(url, title, description):
        full_content = fetch_full_page_content(url)
        if full_content:
            summary = _extract_page_summary(full_content, car_info, fluid_type)
            if summary:
                return "scraped", url, title, summary
        if description and len(description) > 80:
            summary = _extract_page_summary(description, car_info, fluid_type)
            if summary:
                return "snippet", url, title, summary
        return None, url, title, ""

    blocks = []
    if not candidates:
        return blocks
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_scrape_one, url, title, description):
            (url, title, description)
            for url, title, description in candidates
        }
        for source_number, future in enumerate(as_completed(futures), 1):
            source_type, url, title, summary = future.result()
            if summary:
                fluid_category = _fluid_category_from_summary(summary)
                blocks.append(
                    f"=== SOURCE {source_number}: {title} ===\n"
                    f"URL: {url}\n"
                    f"FLUID_CATEGORY: {fluid_category}\n"
                    f"SUMMARY:\n{summary}\n"
                )
    return blocks


def _append_unverified_snippets(blocks, sanitized_results):
    """Append search snippets from sanitized result positions 5 through 7."""
    if len(sanitized_results) < 4:
        return blocks
    for source_number, item in enumerate(sanitized_results[4:7], 5):
        url = item.get("href") or item.get("link") or ""
        title = item.get("title", "")
        snippet = item.get("body") or item.get("content") or item.get("snippet") or ""
        if url and snippet:
            blocks.append(
                f"=== SOURCE {source_number}: {title} ===\n"
                f"URL: {url}\n"
                "CONTENT (search snippet, unverified):\n"
                f"{snippet[:500]}\n"
            )
    return blocks


BLOCKED_BASE_DOMAINS = {
    "amazon", "ebay", "aliexpress", "cdiscount", "walmart",
    "facebook", "instagram", "tiktok", "pinterest", "youtube",
    "twitter", "reddit", "linkedin", "autodoc", "auto-doc", "piecesauto24",
    "mister-auto", "oscaro", "pieces24", "autodoc24", "carter-cash", "norauto",
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
    """Fallback search that returns per-page summaries like Firecrawl."""
    car_info = f"{brand} {model} {engine} {year}".strip()
    car_info_alt = f"{year} {brand} {model} {engine}".strip()
    fluid_lower = (fluid_type or "").lower()
    if any(k in fluid_lower for k in ("boite", "boîte", "gearbox", "transmission")):
        queries = [
            f"{car_info} huile de boite preconisation specification",
            f"{car_info_alt} gearbox oil specification OEM reference",
        ]
    elif any(k in fluid_lower for k in ("filtre", "filter")):
        queries = [
            f"{car_info} filtre a huile reference preconisation",
            f"{car_info_alt} oil filter reference OEM",
        ]
    else:
        queries = [
            f"{car_info} huile moteur preconisation specification",
            f"{car_info_alt} engine oil specification OEM",
        ]

    raw = []
    seen_urls = set()
    for i, query in enumerate(queries):
        print(f"[Tavily Query {i + 1}/{len(queries)}]: {query}")
        try:
            response = tavily_client.search(
                query=query,
                max_results=8,
                search_depth="basic",
                exclude_domains=[
                    "amazon.com", "ebay.com", "aliexpress.com",
                    "facebook.com", "youtube.com", "reddit.com",
                    "pinterest.com", "tiktok.com", "twitter.com",
                    "instagram.com", "linkedin.com",
                ],
            )
        except Exception as error:
            print(f"[Tavily Query {i + 1} failed]: {error}")
            continue

        results = response.get("results", []) or []
        print(f"[Tavily] Query {i + 1} returned {len(results)} results.")
        for item in results:
            url = item.get("url") or ""
            title = item.get("title") or ""
            content = item.get("content") or ""
            if url and url not in seen_urls:
                seen_urls.add(url)
                raw.append({"href": url, "title": title, "body": content})

    if not raw:
        return "TAVILY_NO_RESULTS"
    sanitized = sanitize_search_results(raw)
    print(f"[Tavily] Sanitized results: {len(sanitized)}")
    if not sanitized:
        return "TAVILY_NO_RESULTS"
    candidates = [
        (item["href"], item.get("title", ""), item.get("body", ""))
        for item in sanitized[:4]
    ]
    page_summaries = _scrape_and_summarize_parallel(candidates, car_info, fluid_type)
    page_summaries = _append_unverified_snippets(page_summaries, sanitized)
    if not page_summaries:
        return "TAVILY_NO_SUMMARIES"
    return "\n\n".join(page_summaries)


@tool(args_schema=SearchInput)
def ddgs_Search(brand: str, model: str, year: int,  fluid_type: str , engine: str = "", gearbox_ref: str = "", transmission_type: str = "",) -> str:
    """ Searches for technical automotive specifications, deep-scrapes the top sources,
        and returns a structured, noise-free summary of specs and warnings.
    """
    fluid_guard = (fluid_type or "").lower()
    if any(k in fluid_guard for k in ("filtre", "filter")):
        return "FILTER_NOT_SUPPORTED"
    if any(k in fluid_guard for k in ("frein", "brake")):
        return "BRAKE_NOT_SUPPORTED"

  
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
        queries = [
            f"{car_gb} boite de vitesses huile preconisation specification",
            f"{car_gb_alt} transmission gearbox fluid specification",
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
                f"{car_info_alt} engine oil capacity viscosity specification",
            ]
        else:
            queries = [
                f"{car_info} contenance carter huile norme OEM",
                f"{car_info_alt} engine oil capacity viscosity specification",
            ]

    # 4. Fallback
    else:
        if engine:
                     _car_parts.append(engine)
        queries = [
            f"{base} {fluid_type} specs",
            f"{base_alt} {fluid_type} specification",
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

    candidates = []
    for item in results[:4]:
        url = item.get("href") or item.get("link") or ""
        title = item.get("title", "")
        description = item.get("body") or item.get("snippet") or ""
        if url:
            candidates.append((url, title, description))

    page_summaries = _scrape_and_summarize_parallel(candidates, car_info, fluid_type)
    if not page_summaries:
        return "DDGS_NO_SUMMARIES"
    return "\n\n".join(page_summaries)


@tool(args_schema=SearchInput)
def firecrawl_Search(
    brand: str,
    model: str,
    year: int,
    mileage: int = 0,
    fluid_type: str = "",
    engine: str = "",
    gearbox_ref: str = "",
    transmission_type: str = "",
) -> str:
    """Firecrawl-backed replacement for ddgs_Search. Same output format.

    Searches with Firecrawl, sanitizes by domain blocklist, scrapes each
    surviving URL with trafilatura, then runs the same per-page extraction
    used by the DDGS path.
    """
    fluid_guard = (fluid_type or "").lower()
    if any(k in fluid_guard for k in ("filtre", "filter")):
        return "FILTER_NOT_SUPPORTED"
    if any(k in fluid_guard for k in ("frein", "brake")):
        return "BRAKE_NOT_SUPPORTED"
    car_info = f"{brand} {model} {engine} {year}".strip()
    car_info_alt = f"{year} {brand} {model} {engine}".strip()
    fluid_lower = fluid_type.lower()
    engine_lower = engine.lower()
    is_diesel = any(d in engine_lower for d in [
        "dci", "tdi", "hdi", "crdi", "cdti", "d4d", "d-4d", "diesel"
    ])
    is_gearbox_req = any(k in fluid_lower for k in ["boite", "gearbox", "transmission"])

    if is_gearbox_req:
        car_gb = f"{brand} {model} {year} {gearbox_ref} {transmission_type}".strip()
        car_gb_alt = f"{year} {brand} {model} {gearbox_ref} {transmission_type}".strip()
        queries = [
            f"Quelle huile de boite de vitesses pour {car_gb} specification constructeur",
            f"{car_gb_alt} gearbox oil specification OEM reference",
        ]
    elif any(k in fluid_lower for k in ["moteur", "engine"]):
        queries = [
            f"Quelle huile moteur recommandée pour {car_info} specification constructeur",
            f"{car_info_alt} engine oil specification OEM recommendation",
        ]
    else:
        queries = [
            f"{brand} {model} {year} {fluid_type} specification constructeur",
            f"{year} {brand} {model} {fluid_type} specification OEM",
        ]

    raw_results: list[dict] = []
    seen_urls: set[str] = set()
    try:
        for i, query in enumerate(queries):
            print(f"[Firecrawl Query {i + 1}/{len(queries)}]: {query}")
            try:
                response = _firecrawl_client.search(
                    query=query,
                    limit=10,
                    sources=["web"],
                )
            except Exception as error:
                print(f"[Firecrawl Query {i + 1} failed]: {error}")
                continue

            for result in getattr(response, "web", None) or []:
                url = getattr(result, "url", None) or getattr(result, "link", None) or ""
                title = getattr(result, "title", "") or ""
                description = (
                    getattr(result, "description", None)
                    or getattr(result, "snippet", None)
                    or ""
                )
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    raw_results.append({"href": url, "title": title, "body": description})
    except Exception as error:
        print(f"Firecrawl Network Error: {error}")
        return f"FIRECRAWL_ERROR: {error}"

    print(f"=== RAW RESULTS COUNT: {len(raw_results)} ===")
    results = sanitize_search_results(raw_results)
    print(f"=== SANITIZED RESULTS COUNT: {len(results)} ===")
    if not results:
        return "FIRECRAWL_NO_RESULTS"

    candidates = []
    for item in results[:4]:
        url = item.get("href") or item.get("link") or ""
        title = item.get("title", "")
        description = item.get("body") or item.get("snippet") or ""
        if url:
            candidates.append((url, title, description))

    page_summaries = _scrape_and_summarize_parallel(candidates, car_info, fluid_type)
    page_summaries = _append_unverified_snippets(page_summaries, results)
    if not page_summaries:
        return "FIRECRAWL_NO_SUMMARIES"
    return "\n\n".join(page_summaries)