from pydantic import BaseModel, Field
from langchain.tools import tool
from sqlalchemy import select, or_

from app.db.session import SessionLocal
from app.db.models.tables import (
    Oil_Engine_Item,
    Oil_Transmission_Item,
)
import time

from app.agents.schemas import StockLookupInput
from app.services.product_service import _serialize as _serialize_product

OEM_ALIASES = {
    # BMW
    "bmw longlife-04": ["bmw ll-04", "ll-04", "ll04"],
    "bmw longlife-01": ["bmw ll-01", "ll-01", "ll01"],
    "bmw longlife-98": ["bmw ll-98", "ll-98"],

    # VW / Audi / Å koda / Seat
    "vw 504.00": ["vw 504 00", "504.00", "504 00"],
    "vw 507.00": ["vw 507 00", "507.00", "507 00", "vw 507"],

    # Mercedes
    "mb 229.51": ["mb 229 51", "229.51", "229 51", "mercedes 229.51"],
    "mb 229.52": ["mb 229 52", "229.52", "229 52"],
    "mb 229.5":  ["mb 229 5", "229.5", "229 5"],

    # Renault / Dacia
    "renault rn0720": ["rn0720", "rn 0720"],
    "renault rn0710": ["rn0710", "rn 0710"],
    "renault rn0700": ["rn0700", "rn 0700"],
    "renault rn17":   ["rn17", "rn 17"],

    # PSA
    "psa b71 2312": ["b71 2312", "psa b71 2312", "psa b712312"],
    "psa b71 2290": ["b71 2290", "psa b71 2290", "psa b712290"],

    # Ford
    "ford wss-m2c913-c": ["wss-m2c913-c", "m2c913-c"],
    "ford wss-m2c913-d": ["wss-m2c913-d", "m2c913-d"],

    # GM / Opel
    "dexos1":  ["dexos 1", "dexos-1"],
    "dexos2":  ["dexos 2", "dexos-2"],
}



# ---------- serializers ----------

def _ser_engine(item) -> dict:
    result = _serialize_product(item, "engine_oil")
    result["match_quality"] = getattr(item, "_match_quality", "full")
    return result

def _ser_transmission(item) -> dict:
    result = _serialize_product(item, "gearbox_oil")
    result["match_quality"] = getattr(item, "_match_quality", "full")
    return result

import re


def _spec_variants(spec: str) -> list[str]:
    """Expand a spec string into all matchable forms, including synonyms."""
    
    if not spec:
        return []

    s = spec.strip().lower()
    variants = {s}

    # parentheticals and comma parts (existing behavior)
    for p in re.findall(r"\(([^)]+)\)", s):
        p = p.strip()
        if p:
            variants.add(p)
    without_parens = re.sub(r"\([^)]*\)", "", s).strip()
    if without_parens:
        variants.add(without_parens)
    for part in s.split(","):
        p = part.strip()
        if p:
            variants.add(p)

    # NEW: expand via alias map, in both directions
    for canonical, aliases in OEM_ALIASES.items():
        all_forms = {canonical, *aliases}
        # if any form appears in the spec, add all forms as candidates
        if any(form in s for form in all_forms):
            variants.update(all_forms)

    return [v for v in variants if len(v) >= 3]

# ---------- queries ----------

def _mark_match_quality(rows, oem_was_used: bool):
    for row in rows:
        row._match_quality = "full" if oem_was_used else "viscosity_only"
    return rows

def _query_engine_oil(session, spec: str, visc: str):
    stmt = select(Oil_Engine_Item).where(Oil_Engine_Item.quantity > 0)
    oem_used = bool(spec)

    # Match OEM OR API/ACEA, since the search agent may hand us either
    
    variants = _spec_variants(spec)
    if variants:
        or_clauses = []
        for v in variants:
            or_clauses.append(Oil_Engine_Item.oem.ilike(f"%{v}%"))
            or_clauses.append(Oil_Engine_Item.api_acea.ilike(f"%{v}%"))
        stmt = stmt.where(or_(*or_clauses))

    if visc:
        stmt = stmt.where(Oil_Engine_Item.viscosity == visc.lower())

    rows = session.scalars(stmt.order_by(Oil_Engine_Item.price)).all()
    return _mark_match_quality(rows, oem_used)



def _query_gearbox_oil(session, spec: str, visc: str):
    stmt = select(Oil_Transmission_Item).where(Oil_Transmission_Item.quantity > 0)
    oem_used = bool(spec)

    variants = _spec_variants(spec)
    if variants:
        or_clauses = [Oil_Transmission_Item.oem.ilike(f"%{v}%") for v in variants]
        stmt = stmt.where(or_(*or_clauses))

    if visc:
        stmt = stmt.where(Oil_Transmission_Item.viscosity == visc.lower())

    rows = session.scalars(stmt.order_by(Oil_Transmission_Item.price)).all()
    return _mark_match_quality(rows, oem_used)



# ---------- tool ----------

@tool(args_schema=StockLookupInput)
def stock_lookup(fluid_type: str, oem_specification: str = "", viscosity: str = "") -> dict:
    """Look up products in AutoLube stock that match the given specification.

    Returns:
      { "status": "ok" | "no_match" | "error",
        "products": [ {id, brand, ..., size, price, quantity}, ... ],
        "reason": "<short string, only when status != 'ok'>" }

    Call ONLY after you have a specification value. Do not call it with empty inputs.
    """
    _t = time.perf_counter()
    fluid = (fluid_type or "").lower()
    spec = (oem_specification or "").strip()
    visc = (viscosity or "").strip()

    if not spec and not visc:
        print(f"[TIMING] stock_lookup: {time.perf_counter() - _t:.3f}s (error)")
        return {"status": "error", "reason": "No specification or viscosity provided."}

    try:
        with SessionLocal() as session:
            if any(k in fluid for k in ("moteur", "engine")):
                rows = _query_engine_oil(session, spec, visc)
                products = [_ser_engine(r) for r in rows]

            elif any(k in fluid for k in ("boite", "boÃ®te", "gearbox", "transmission")):
                rows = _query_gearbox_oil(session, spec, visc)
                products = [_ser_transmission(r) for r in rows]

            else:
                print(f"[TIMING] stock_lookup: {time.perf_counter() - _t:.3f}s (error)")
                return {"status": "error", "reason": f"Unsupported fluid type: {fluid_type}"}
            
            print("db query executed for stock lookup")

    except Exception as e:
        print(f"[TIMING] stock_lookup: {time.perf_counter() - _t:.3f}s (error)")
        return {"status": "error", "reason": f"DB error: {e}"}

    if not products:
        print(f"[TIMING] stock_lookup: {time.perf_counter() - _t:.3f}s (no_match)")
        return {"status": "no_match", "products": [], "reason": "No matching product in stock."}

    print(f"[TIMING] stock_lookup: {time.perf_counter() - _t:.3f}s (ok)")
    return {"status": "ok", "products": products}