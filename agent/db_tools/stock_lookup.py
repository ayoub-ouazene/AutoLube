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



# ---------- queries ----------

def _query_engine_oil(session, spec: str, visc: str):
    stmt = select(Oil_Engine_Item).where(Oil_Engine_Item.quantity > 0)

    # Match OEM OR API/ACEA, since the search agent may hand us either
    if spec:
        s = spec.lower()
        stmt = stmt.where(or_(
            Oil_Engine_Item.oem.ilike(f"%{s}%"),
            Oil_Engine_Item.api_acea.ilike(f"%{s}%"),
        ))
    if visc:
        stmt = stmt.where(Oil_Engine_Item.viscosity == visc.lower())

    return session.scalars(stmt.order_by(Oil_Engine_Item.price)).all()


def _query_gearbox_oil(session, spec: str, visc: str):
    stmt = select(Oil_Transmission_Item).where(Oil_Transmission_Item.quantity > 0)

    # For gearbox we accept spec OR viscosity match (as before — either signal is enough)
    clauses = []
    if spec:
        clauses.append(Oil_Transmission_Item.oem.ilike(f"%{spec.lower()}%"))
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
            print("db query executed")

    except Exception as e:
        return {"status": "error", "reason": f"DB error: {e}"}

    if not products:
        return {"status": "no_match", "products": [], "reason": "No matching product in stock."}

    return {"status": "ok", "products": products}