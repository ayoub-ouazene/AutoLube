from urllib.parse import quote

from sqlalchemy import select

from app.config import settings
from app.db.models.tables import (
    Additional_Item,
    Filter_Item,
    Oil_Engine_Item,
    Oil_Transmission_Item,
    Order,
    OrderItem,
)
from app.db.session import SessionLocal

from sqlalchemy import func, select
from app.db.models.tables import Order, OrderItem

CATEGORY_MAP = {
    "engine_oil":  Oil_Engine_Item,
    "gearbox_oil": Oil_Transmission_Item,
    "oil_filter":  Filter_Item,
    "additional":  Additional_Item,
}


class OrderError(Exception):
    """Raised when an order cannot be placed. Message is customer-safe."""


def _specification(row, category: str) -> str:
    if category in ("engine_oil", "gearbox_oil"):
        return row.oem or ""
    return row.reference or ""


def _size(row, category: str) -> str | None:
    if category == "oil_filter":
        return None
    return getattr(row, "size", None)


def _name(row, category: str) -> str:
    parts = [row.brand]
    visc = getattr(row, "viscosity", None)
    if visc:
        parts.append(visc)
    size = _size(row, category)
    if size:
        parts.append(size)
    return " ".join(parts)


def create_order(customer: dict, items: list[dict]) -> dict:
    if not items:
        raise OrderError("Aucun article dans la commande.")

    with SessionLocal() as session:
        order = Order(
            customer_name=customer["full_name"],
            customer_phone=customer["phone"],
            customer_email=customer.get("email"),
            wilaya=customer["wilaya"],
            city=customer["city"],
            notes=customer.get("notes"),
            total=0.0,
            status="pending",
        )
        session.add(order)
        session.flush()  # assign order.id

        total = 0.0
        response_items = []

        for item in items:
            cat = item["category"]
            model = CATEGORY_MAP.get(cat)
            if model is None:
                raise OrderError(f"Catégorie inconnue : {cat}")

            row = session.get(model, item["id"])
            if row is None:
                raise OrderError(f"Produit introuvable : {cat}/{item['id']}")

            qty = item["quantity"]
            if row.quantity < qty:
                raise OrderError(
                    f"Stock insuffisant pour {row.brand} "
                    f"({row.quantity} disponible(s), {qty} demandé(s))."
                )

            unit_price = float(row.price)
            line_total = round(unit_price * qty, 2)

            session.add(OrderItem(
                order_id=order.id,
                category=cat,
                product_id=row.id,
                brand_snapshot=row.brand,
                name_snapshot=_name(row, cat),
                specification_snapshot=_specification(row, cat),
                size_snapshot=_size(row, cat),
                unit_price_snapshot=unit_price,
                quantity=qty,
                line_total=line_total,
            ))

           

            total += line_total
            response_items.append({
                "category": cat,
                "product_id": row.id,
                "name": _name(row, cat),
                "size": _size(row, cat),
                "unit_price": unit_price,
                "quantity": qty,
                "line_total": line_total,
            })

        order.total = round(total, 2)
        session.commit()

        return {
            "order_id": order.id,
            "total": float(order.total),
            "items": response_items,
            "whatsapp_url": _build_whatsapp_url(order, response_items),
        }


def _build_whatsapp_url(order: Order, items: list[dict]) -> str:
    lines = [
        f"*Nouvelle commande #{order.id}*",
        "",
        f"Nom : {order.customer_name}",
        f"Téléphone : {order.customer_phone}",
    ]
    if order.customer_email:
        lines.append(f"Email : {order.customer_email}")
    lines.append(f"Wilaya : {order.wilaya}")
    lines.append(f"Ville : {order.city}")
    lines.append("")
    lines.append("*Produits :*")
    for it in items:
        size_part = f" ({it['size']})" if it["size"] else ""
        lines.append(
            f"- {it['name']}{size_part} x{it['quantity']} "
            f"= {it['line_total']:.0f} DA"
        )
    lines.append("")
    lines.append(f"*Total : {float(order.total):.0f} DA*")
    if order.notes:
        lines.append("")
        lines.append(f"Notes : {order.notes}")

    text = "\n".join(lines)
    number = settings.whatsapp_number.strip().lstrip("+")
    return f"https://wa.me/{number}?text={quote(text)}"


def confirm_order(order_id: int) -> dict:
    """
    Mark an order as confirmed and decrement stock for its items.
    Raises OrderError if the order doesn't exist, is already confirmed,
    or if any item no longer has enough stock.
    """
    with SessionLocal() as session:
        order = session.get(Order, order_id)
        if order is None:
            raise OrderError(f"Commande introuvable : #{order_id}")
        if order.status == "confirmed":
            raise OrderError("Cette commande est déjà confirmée.")
        if order.status == "cancelled":
            raise OrderError("Cette commande est annulée.")

        # Load its items
        items = session.scalars(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).all()

        # First pass: verify all items have enough stock
        for it in items:
            model = CATEGORY_MAP.get(it.category)
            if model is None:
                raise OrderError(f"Catégorie inconnue : {it.category}")
            row = session.get(model, it.product_id)
            if row is None:
                raise OrderError(f"Produit introuvable : {it.category}/{it.product_id}")
            if row.quantity < it.quantity:
                raise OrderError(
                    f"Stock insuffisant pour {it.brand_snapshot} : "
                    f"{row.quantity} disponible(s), {it.quantity} requis."
                )

        # Second pass: decrement
        for it in items:
            model = CATEGORY_MAP[it.category]
            row = session.get(model, it.product_id)
            row.quantity -= it.quantity

        order.status = "confirmed"
        session.commit()

        return {
            "order_id": order.id,
            "status": order.status,
            "total": float(order.total),
        }




def list_orders(
    status: str | None,
    page: int,
    page_size: int,
) -> dict:
    """Return a paginated list of orders, newest first."""
    with SessionLocal() as session:
        base = select(Order)
        count_stmt = select(func.count()).select_from(Order)

        if status:
            base = base.where(Order.status == status)
            count_stmt = count_stmt.where(Order.status == status)

        total = session.scalar(count_stmt) or 0

        base = (
            base.order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = session.scalars(base).all()

        # Count items per order in one query
        order_ids = [r.id for r in rows]
        item_counts: dict[int, int] = {}
        if order_ids:
            counts_stmt = (
                select(OrderItem.order_id, func.count(OrderItem.id))
                .where(OrderItem.order_id.in_(order_ids))
                .group_by(OrderItem.order_id)
            )
            for oid, cnt in session.execute(counts_stmt):
                item_counts[oid] = cnt

        items = [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "customer_name": r.customer_name,
                "customer_phone": r.customer_phone,
                "wilaya": r.wilaya,
                "city": r.city,
                "total": float(r.total),
                "status": r.status,
                "item_count": item_counts.get(r.id, 0),
            }
            for r in rows
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": page * page_size < total,
        }



def get_order_detail(order_id: int) -> dict | None:
    """Return full order with its line items, or None if not found."""
    with SessionLocal() as session:
        order = session.get(Order, order_id)
        if order is None:
            return None

        items = session.scalars(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).all()

        return {
            "id": order.id,
            "created_at": order.created_at.isoformat(),
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "customer_email": order.customer_email,
            "wilaya": order.wilaya,
            "city": order.city,
            "notes": order.notes,
            "total": float(order.total),
            "status": order.status,
            "items": [
                {
                    "id": it.id,
                    "category": it.category,
                    "product_id": it.product_id,
                    "brand": it.brand_snapshot,
                    "name": it.name_snapshot,
                    "specification": it.specification_snapshot,
                    "size": it.size_snapshot,
                    "unit_price": float(it.unit_price_snapshot),
                    "quantity": it.quantity,
                    "line_total": float(it.line_total),
                }
                for it in items
            ],
        }



def cancel_order(order_id: int) -> dict:
    """Mark an order as cancelled. Stock is NOT restored because it was never
    decremented until confirmation."""
    with SessionLocal() as session:
        order = session.get(Order, order_id)
        if order is None:
            raise OrderError(f"Commande introuvable : #{order_id}")
        if order.status == "confirmed":
            raise OrderError("Impossible d'annuler une commande déjà confirmée.")
        if order.status == "cancelled":
            raise OrderError("Cette commande est déjà annulée.")

        order.status = "cancelled"
        session.commit()

        return {
            "order_id": order.id,
            "status": order.status,
        }