# agent/db_tools/test_specs.py
from  agent.db_tools.spec_lookup  import (
    specs_lookup,
    _query_engine_cache,
    _query_transmission_cache,
    _ser_engine,
    _ser_transmission,
)
from config.db import SessionLocal


def show(label, result):
    print(f"\n=== {label} ===")
    print(result)


# ---------- direct query tests (bypass the tool wrapper) ----------
with SessionLocal() as session:
    print("--- Direct query: Renault Clio IV, K9K 646, 2016 ---")
    row = _query_engine_cache(session, "Renault", "Clio IV", 2016, "K9K 646")
    print(_ser_engine(row) if row else "None")

    print("\n--- Direct query: Renault Clio IV, 1.5 dCi 110, 2016 ---")
    row = _query_engine_cache(session, "Renault", "Clio IV", 2016, "1.5 dCi 110")
    print(_ser_engine(row) if row else "None")

    print("\n--- Direct query: Renault Clio IV, no engine (should be None — ambiguous) ---")
    row = _query_engine_cache(session, "Renault", "Clio IV", 2016, "")
    print(_ser_engine(row) if row else "None")

    print("\n--- Direct query: VW Golf VII, DDYA, 2016 ---")
    row = _query_engine_cache(session, "Volkswagen", "Golf VII", 2016, "DDYA")
    print(_ser_engine(row) if row else "None")

    print("\n--- Direct query: Peugeot 208, DV6FD, 2015 ---")
    row = _query_engine_cache(session, "Peugeot", "208", 2015, "DV6FD")
    print(_ser_engine(row) if row else "None")

    print("\n--- Direct query: unknown car (should be None) ---")
    row = _query_engine_cache(session, "BMW", "320d", 2015, "N47")
    print(_ser_engine(row) if row else "None")

    print("\n--- Direct query: transmission VW Golf VII MQ250 ---")
    row = _query_transmission_cache(session, "Volkswagen", "Golf VII", 2016, "MQ250", "Manual")
    print(_ser_transmission(row) if row else "None")

    print("\n--- Direct query: transmission Dacia Duster TL4 ---")
    row = _query_transmission_cache(session, "Dacia", "Duster", 2018, "TL4", "Manual")
    print(_ser_transmission(row) if row else "None")


# ---------- tool-wrapper tests (as the LLM would call it) ----------
print("\n\n######## TOOL CALLS ########")

show("Engine Oil — Renault Clio IV K9K 646", specs_lookup.invoke({
    "fluid_type": "Engine Oil",
    "brand": "Renault", "model": "Clio IV", "year": 2016,
    "engine": "K9K 646",
}))

show("Engine Oil — Renault Clio IV (no engine, ambiguous)", specs_lookup.invoke({
    "fluid_type": "Engine Oil",
    "brand": "Renault", "model": "Clio IV", "year": 2016,
    "engine": "",
}))

show("Engine Oil — Peugeot 208 DV6FD", specs_lookup.invoke({
    "fluid_type": "Engine Oil",
    "brand": "Peugeot", "model": "208", "year": 2015,
    "engine": "DV6FD",
}))

show("Engine Oil — BMW 320d (not in cache)", specs_lookup.invoke({
    "fluid_type": "Engine Oil",
    "brand": "BMW", "model": "320d", "year": 2015,
    "engine": "N47",
}))

show("Gearbox Oil — VW Golf VII MQ250 Manual", specs_lookup.invoke({
    "fluid_type": "Gearbox Oil",
    "brand": "Volkswagen", "model": "Golf VII", "year": 2016,
    "gearbox_ref": "MQ250", "transmission_type": "Manual",
}))

show("Gearbox Oil — Dacia Duster TL4 Manual", specs_lookup.invoke({
    "fluid_type": "Gearbox Oil",
    "brand": "Dacia", "model": "Duster", "year": 2018,
    "gearbox_ref": "TL4", "transmission_type": "Manual",
}))

show("Gearbox Oil — unknown", specs_lookup.invoke({
    "fluid_type": "Gearbox Oil",
    "brand": "Škoda", "model": "Octavia II", "year": 2009,
    "gearbox_ref": "MQ200", "transmission_type": "Manual",
}))