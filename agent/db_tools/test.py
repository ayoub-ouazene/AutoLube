from config.db import SessionLocal
from agent.db_tools.stock_lookup import (
    _query_engine_oil, _query_gearbox_oil,
    _ser_engine, _ser_transmission,
)

with SessionLocal() as s:
    print("=== VW 507.00 / 5W-30 ===")
    for r in _query_engine_oil(s, "vw 507.00", "5w-30"):
        print(_ser_engine(r))

    print("\n=== RN0720 / 5W-30 ===")
    for r in _query_engine_oil(s, "rn0720", "5w-30"):
        print(_ser_engine(r))

    print("\n=== VW G 052 171 A2 ===")
    for r in _query_gearbox_oil(s, "g 052 171 a2", ""):
        print(_ser_transmission(r))

    print("\n=== Renault NFJ ===")
    for r in _query_gearbox_oil(s, "nfj", ""):
        print(_ser_transmission(r))