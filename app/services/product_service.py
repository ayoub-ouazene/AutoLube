import hashlib
import re

from sqlalchemy import or_, select

from app.db.models.tables import (
    Additional_Item,
    Filter_Item,
    Oil_Engine_Item,
    Oil_Transmission_Item,
)
from app.db.session import SessionLocal


CATEGORY_MAP = {
    "engine_oil":  Oil_Engine_Item,
    "gearbox_oil": Oil_Transmission_Item,
    "oil_filter":  Filter_Item,
    "additional":  Additional_Item,
}


def _parse_size_liters(size: str | None) -> float | None:
    """Parse '5L' → 5.0, '20 l' → 20.0, '1 pc' → None."""
    if not size:
        return None
    m = re.match(r"^\s*([\d.,]+)\s*l\b", size.lower())
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _serialize(row, category: str) -> dict:
    """Normalize a row from any of the four tables into a common dict."""
    if category == "engine_oil":
        specification = row.oem or ""
        viscosity = row.viscosity
        size = row.size
    elif category == "gearbox_oil":
        specification = row.oem or ""
        viscosity = row.viscosity
        size = row.size
    elif category == "oil_filter":
        specification = row.reference or ""
        viscosity = None
        size = None
    elif category == "additional":
        specification = row.reference or ""
        viscosity = None 
        size = row.size
    else:
        raise ValueError(f"Unknown category: {category}")

    parts = [row.brand, viscosity, size]
    name = " ".join(p for p in parts if p)

    return {
        "category": category,
        "id": row.id,
        "brand": row.brand,
        "name": name,
        "specification": specification,
        "viscosity": viscosity,
        "size": size,
        "price": float(row.price),
        "in_stock": row.quantity > 0,
    }


def _random_key(item: dict) -> str:
    """Deterministic, stable hash per (category, id). Used as sort key."""
    return hashlib.md5(f"{item['category']}:{item['id']}".encode()).hexdigest()


def _build_query(model, category, brands, min_price, max_price, q):
    stmt = select(model)

    if brands:
        stmt = stmt.where(model.brand.in_(brands))
    if min_price is not None:
        stmt = stmt.where(model.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(model.price <= max_price)

    if q:
        like = f"%{q.lower()}%"
        clauses = [model.brand.ilike(like)]
        if category in ("engine_oil", "gearbox_oil"):
            clauses.append(model.oem.ilike(like))
            clauses.append(model.viscosity.ilike(like))
        if category == "engine_oil":
            clauses.append(model.api_acea.ilike(like))
        if category in ("oil_filter", "additional"):
            clauses.append(model.reference.ilike(like))
        if category == "additional":
            clauses.append(model.category_type.ilike(like))
        stmt = stmt.where(or_(*clauses))

    return stmt


def list_products(
    categories: list[str] | None,
    brands: list[str] | None,
    min_price: float | None,
    max_price: float | None,
    size_min: float | None,
    size_max: float | None,
    q: str | None,
    sort: str,
    page: int,
    page_size: int,
) -> dict:
    
    # Normalize categories filter
    if categories:
        categories = [c for c in categories if c in CATEGORY_MAP]
    if not categories:
        categories = list(CATEGORY_MAP.keys())

    rows: list[dict] = []

    with SessionLocal() as session:
        for cat in categories:
            model = CATEGORY_MAP[cat]
            stmt = _build_query(model, cat, brands, min_price, max_price, q)
            for row in session.scalars(stmt).all():
                rows.append(_serialize(row, cat))

    # Size filter (in Python; size is a string)
    if size_min is not None or size_max is not None:
        filtered = []
        for r in rows:
            liters = _parse_size_liters(r["size"])
            if liters is None:
                continue
            if size_min is not None and liters < size_min:
                continue
            if size_max is not None and liters > size_max:
                continue
            filtered.append(r)
        rows = filtered

    # Sort
    if sort == "price_asc":
        rows.sort(key=lambda r: r["price"])
    elif sort == "price_desc":
        rows.sort(key=lambda r: -r["price"])
    else:
        rows.sort(key=_random_key)

    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = rows[start:end]

    return {
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": end < total,
    }


def get_product(category: str, product_id: int) -> dict | None:
    if category not in CATEGORY_MAP:
        return None
    model = CATEGORY_MAP[category]
    with SessionLocal() as session:
        row = session.get(model, product_id)
        if row is None:
            return None
        return _serialize(row, category)