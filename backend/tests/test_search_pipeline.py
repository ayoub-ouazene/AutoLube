"""
Test the extraction prompt in isolation.
Feed it known text, check what it returns.

Run with:
    python -m tests.test_search_pipeline
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import SEARCH_SYNTHESIS_SYSTEM_PROMPT
from app.core.llm_pool import load_keys_from_env, run_with_failover

load_dotenv(Path(__file__).parent.parent / ".env")

POOL = load_keys_from_env()

MB_SOURCE = """
=== SOURCE 1: Mercedes-Benz C-Class W205 Service Data ===
Model: C220d (2014-2018)
Engine: OM651 (2.1L, 170 hp)
Engine oil capacity (with filter): 6.5 L
Recommended viscosity: 5W-30
OEM specification: MB 229.51
Note: DPF-equipped, low-SAPS oil required.
"""

MULTI_VARIANT_SOURCE = """
=== SOURCE 1: VW Golf oil chart ===
1.6 TDI (2012-2017, 105 hp) — 4.3 L — 5W-30 — VW 507.00
2.0 TDI (2012-2017, 150 hp) — 4.6 L — 5W-30 — VW 507.00
1.4 TSI (2012-2017, 122 hp) — 4.0 L — 5W-30 — VW 504.00
"""

NOISE_SOURCE = """
=== SOURCE 1: Auto shop home page ===
Welcome to our store. We sell engine oil, filters, and accessories.
Add to cart to buy. Free shipping over 5000 DA. Login for member prices.
"""


def ask(label: str, source: str, vehicle: str) -> None:
    print("=" * 72)
    print(f"CASE: {label}")
    print("=" * 72)
    messages = [
        SystemMessage(content=SEARCH_SYNTHESIS_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Vehicle parameters:\n{vehicle}\n"
            f"--- SEARCH RESULTS ---\n{source}\n--- END SEARCH RESULTS ---"
        )),
    ]

    def _run(model):
        return model.invoke(messages)

    response = run_with_failover(POOL, _run)
    content = response.content
    if isinstance(content, list):
        content = "".join(block.get("text", "") for block in content if isinstance(block, dict))
    print(content)
    print()


def main() -> int:
    ask(
        "Mercedes C220d — expect MB 229.51, 6.5 L, 5W-30",
        MB_SOURCE,
        "- Brand: Mercedes-Benz\n- Model: C220d\n- Year: 2016\n"
        "- Engine: OM651\n- Fluid: Engine Oil",
    )
    ask(
        "Multi-variant — expect 4.3 L and VW 507.00 for 1.6 TDI only",
        MULTI_VARIANT_SOURCE,
        "- Brand: Volkswagen\n- Model: Golf VII\n- Year: 2016\n"
        "- Engine: 1.6 TDI\n- Fluid: Engine Oil",
    )
    ask(
        "Noise source — expect no_data",
        NOISE_SOURCE,
        "- Brand: Seat\n- Model: Leon\n- Year: 2018\n"
        "- Engine: 1.5 TSI\n- Fluid: Engine Oil",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
