"""
Firecrawl search-only test — no scraping.

Run with:
    python -m scripts.test_firecrawl
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("FIRECRAWL_API_KEY")
if not API_KEY:
    print("ERROR: FIRECRAWL_API_KEY not set in backend/.env", file=sys.stderr)
    sys.exit(1)

client = Firecrawl(api_key=API_KEY)

QUERIES = [
    ("Clio IV engine oil", "Renault Clio IV 2016 K9K 646 contenance carter huile norme OEM DPF"),
    ("Golf VII gearbox oil", "Volkswagen Golf VII 2016 MQ250 boite de vitesses huile preconisation specification"),
    ("Peugeot 308 engine oil", "Peugeot 308 2015 1.6 BlueHDi 120 contenance carter huile norme OEM DPF FAP Low SAPS"),
    ("BMW 320d engine oil", "BMW 320d F30 2015 N47 contenance carter huile norme OEM"),
    ("Fiat 500 engine oil", "Fiat 500 2014 1.3 Multijet 95 contenance carter huile norme OEM"),
    ("Škoda Octavia II gearbox oil", "Škoda Octavia II 2009 MQ200 manual boite de vitesses huile preconisation specification"),
]


def run_one(label: str, query: str) -> None:
    print("=" * 80)
    print(f"QUERY: {label}")
    print(f"  {query}")
    print("=" * 80)

    t0 = time.perf_counter()
    try:
        results = client.search(query=query, limit=8, sources=["web"])
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}\n")
        return

    elapsed = time.perf_counter() - t0
    print(f"  Latency: {elapsed:.2f}s")

    web = getattr(results, "web", None) or []
    print(f"  Results returned: {len(web)}\n")

    for i, item in enumerate(web, 1):
        url = getattr(item, "url", None) or getattr(item, "link", None) or ""
        title = getattr(item, "title", "") or ""
        description = getattr(item, "description", None) or getattr(item, "snippet", None) or ""

        print(f"  --- Result {i} ---")
        print(f"  URL:         {url}")
        print(f"  Title:       {title[:120]}")
        print(f"  Description: {description[:200]}")
        print()


def main() -> int:
    print()
    print(f"Firecrawl search-only test — {len(QUERIES)} queries, limit=8, no scrape")
    print(f"API key: {API_KEY[:10]}...")
    print()

    for label, query in QUERIES:
        run_one(label, query)

    print("=" * 80)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
