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