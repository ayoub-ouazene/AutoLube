from pydantic import BaseModel, Field
from langchain.tools import tool
from sqlalchemy import select, or_

from config.db import SessionLocal
from models.db import (
    Oil_Engine_Item,
    Oil_Transmission_Item,
)

from models.Input_schema import StockLookupInput


# ---------- serializers ----------

def _ser_engine(item: Oil_Engine_Item) -> dict:
    return {
        "id": item.id,
        "brand": item.brand,
        "oem": item.oem,
        "api_acea": item.api_acea,
        "viscosity": item.viscosity,
        "size": item.size,
        "price": float(item.price),
        "quantity": item.quantity,
    }


def _ser_transmission(item: Oil_Transmission_Item) -> dict:
    return {
        "id": item.id,
        "brand": item.brand,
        "oem": item.oem,
        "viscosity": item.viscosity,
        "size": item.size,
        "price": float(item.price),
        "quantity": item.quantity,
    }

import re


def _spec_variants(spec: str) -> list[str]:
    """Break a spec string into candidate patterns for matching against stock.

    'BMW Longlife-04 (LL-04)'  ->  ['bmw longlife-04 (ll-04)', 'bmw longlife-04', 'll-04']
    'VW 507.00'                ->  ['vw 507.00']
    'RN0720, RN17'             ->  ['rn0720, rn17', 'rn0720', 'rn17']
    """
    if not spec:
        return []
    s = spec.strip().lower()
    variants = [s]

    # parenthetical parts as separate candidates
    for p in re.findall(r"\(([^)]+)\)", s):
        p = p.strip()
        if p and p not in variants:
            variants.append(p)

    # the string without the parentheticals
    without_parens = re.sub(r"\([^)]*\)", "", s).strip()
    if without_parens and without_parens not in variants:
        variants.append(without_parens)

    # comma-split parts
    for part in s.split(","):
        p = part.strip()
        if p and p not in variants:
            variants.append(p)

    # drop too-short tokens that would match everything
    return [v for v in variants if len(v) >= 3]


# ---------- queries ----------

def _query_engine_oil(session, spec: str, visc: str):
    stmt = select(Oil_Engine_Item).where(Oil_Engine_Item.quantity > 0)

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

    return session.scalars(stmt.order_by(Oil_Engine_Item.price)).all()


def _query_gearbox_oil(session, spec: str, visc: str):
    stmt = select(Oil_Transmission_Item).where(Oil_Transmission_Item.quantity > 0)

    variants = _spec_variants(spec)
    clauses = []
    for v in variants:
        clauses.append(Oil_Transmission_Item.oem.ilike(f"%{v}%"))
    if visc:
        clauses.append(Oil_Transmission_Item.viscosity == visc.lower())

    if clauses:
        stmt = stmt.where(or_(*clauses))

    return session.scalars(stmt.order_by(Oil_Transmission_Item.price)).all()



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
    fluid = (fluid_type or "").lower()
    spec = (oem_specification or "").strip()
    visc = (viscosity or "").strip()

    if not spec and not visc:
        return {"status": "error", "reason": "No specification or viscosity provided."}

    try:
        with SessionLocal() as session:
            if any(k in fluid for k in ("moteur", "engine")):
                rows = _query_engine_oil(session, spec, visc)
                products = [_ser_engine(r) for r in rows]

            elif any(k in fluid for k in ("boite", "boîte", "gearbox", "transmission")):
                rows = _query_gearbox_oil(session, spec, visc)
                products = [_ser_transmission(r) for r in rows]

            else:
                return {"status": "error", "reason": f"Unsupported fluid type: {fluid_type}"}
            
            print("db query executed for stock lookup")

    except Exception as e:
        return {"status": "error", "reason": f"DB error: {e}"}

    if not products:
        return {"status": "no_match", "products": [], "reason": "No matching product in stock."}

    return {"status": "ok", "products": products}