from pydantic import  Field
from langchain.tools import tool
from sqlalchemy import select

from config.db import SessionLocal
from models.db import Oil_Engine_Cache, Transmission_Oil_Cache
from models.Input_schema import SpecsLookupInput
import re



_TOKEN_SPLIT = re.compile(r"[\s/,;]+")


def _tokens(text: str) -> set[str]:
    if not text:
        return set()
    return {t for t in _TOKEN_SPLIT.split(text.lower()) if len(t) >= 2}


def _score(user_value: str, row_value: str) -> int:
    """Token overlap between the user's engine/gearbox string and the row's."""
    if not user_value or not row_value:
        return 0
    return len(_tokens(user_value) & _tokens(row_value))


def _query_engine_cache(session, brand, model, year, engine):
    stmt = select(Oil_Engine_Cache).where(
        Oil_Engine_Cache.brand.ilike(f"%{brand}%"),
        Oil_Engine_Cache.model.ilike(f"%{model}%"),
        Oil_Engine_Cache.start_year <= year,
        Oil_Engine_Cache.end_year >= year,
    )
    rows = session.scalars(stmt).all()
    if not rows:
        return None

    if engine:
        scored = [(r, _score(engine, r.engine)) for r in rows]
        scored.sort(key=lambda t: t[1], reverse=True)
        best, best_score = scored[0]
        if best_score > 0:
            return best
        return None

    # no engine provided: only resolve if unambiguous
    if len(rows) == 1:
        return rows[0]
    return None


def _query_transmission_cache(session, brand, model, year, gearbox_ref, transmission_type):
    stmt = select(Transmission_Oil_Cache).where(
        Transmission_Oil_Cache.brand.ilike(f"%{brand}%"),
        Transmission_Oil_Cache.model.ilike(f"%{model}%"),
        Transmission_Oil_Cache.start_year <= year,
        Transmission_Oil_Cache.end_year >= year,
    )
    rows = session.scalars(stmt).all()
    if not rows:
        return None

    if gearbox_ref:
        scored = [(r, _score(gearbox_ref, r.gearbox)) for r in rows]
        scored.sort(key=lambda t: t[1], reverse=True)
        best, best_score = scored[0]
        if best_score > 0:
            return best
        return None

    if transmission_type:
        tt = transmission_type.lower()
        matches = [r for r in rows if tt in (r.transmission_type or "").lower()]
        if len(matches) == 1:
            return matches[0]

    if len(rows) == 1:
        return rows[0]
    return None


def _ser_engine(item: Oil_Engine_Cache) -> dict:
    return {
        "oem_specification": item.oem,
        "capacity_liters": item.capacity_liters,
        "viscosity": item.viscosity,
        "api_acea": item.api_acea,
    }


def _ser_transmission(item: Transmission_Oil_Cache) -> dict:
    return {
        "oem_specification": item.oem,
        "capacity_liters": item.capacity_liters,
        "viscosity": item.viscosity,
    }


@tool(args_schema=SpecsLookupInput)
def specs_lookup(
    fluid_type: str,
    brand: str,
    model: str,
    year: int,
    engine: str = "",
    gearbox_ref: str = "",
    transmission_type: str = "",
) -> dict:
    """Look up a vehicle's oil specifications in AutoLube's local cache.

    Call this FIRST for Engine Oil or Gearbox Oil. If it returns
    `status: "found"`, skip the search agent and go straight to stock_lookup.

    Returns:
      { "status": "found", "specs": {oem_specification, capacity_liters, viscosity, [api_acea]} }
      { "status": "not_found" }
      { "status": "error", "reason": "..." }
    """
    fluid = (fluid_type or "").lower()

    try:
        with SessionLocal() as session:
            if any(k in fluid for k in ("moteur", "engine")):
                row = _query_engine_cache(session, brand, model, year, engine)
                
                if row is None:
                    return {"status": "not_found"}

                print("hit the cache")
                print(f"the row of the db : {_ser_engine(row)}")
                
                return {"status": "found", "specs": _ser_engine(row)}

            if any(k in fluid for k in ("boite", "boîte", "gearbox", "transmission")):
                row = _query_transmission_cache(
                    session, brand, model, year, gearbox_ref, transmission_type
                )
                
                if row is None:
                    return {"status": "not_found"}
                
                print("hit the cache")
                print(f"the row of the db : {_ser_transmission(row)}")
                return {"status": "found", "specs": _ser_transmission(row)}

            return {"status": "error", "reason": f"Unsupported fluid type: {fluid_type}"}

    except Exception as e:
        return {"status": "error", "reason": f"DB error: {e}"}