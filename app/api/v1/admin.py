
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.config import settings
from app.core.security import create_access_token, verify_credentials
from app.schemas.admin import LoginRequest, LoginResponse


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    """Exchange admin credentials for a JWT."""
    if not verify_credentials(payload.username, payload.password):
        # Generic message — never reveal whether the username or password was wrong
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides.",
        )

    token = create_access_token()
    return LoginResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )



from app.api.deps import get_current_admin
from app.schemas.admin import AdminOrderListResponse
from app.services import order_service


@router.get(
    "/orders",
    response_model=AdminOrderListResponse,
    dependencies=[Depends(get_current_admin)],
)
def list_orders(
                status: str | None = Query(None, pattern="^(pending|confirmed|cancelled|delivered)$"),
                page: int = Query(1, ge=1),
                page_size: int = Query(20, ge=1, le=100),
                
            ) -> AdminOrderListResponse:
    """List orders, newest first. Optional status filter."""
    return order_service.list_orders(
        status=status,
        page=page,
        page_size=page_size,
    )




from app.schemas.admin import AdminOrderDetail, OrderStatusResponse
from app.services.order_service import OrderError


@router.get(
    "/orders/{order_id}",
    response_model=AdminOrderDetail,
    dependencies=[Depends(get_current_admin)],
)
def get_order(order_id: int) -> AdminOrderDetail:
    """Full order detail including line items."""
    result = order_service.get_order_detail(order_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    return result


@router.post(
    "/orders/{order_id}/confirm",
    response_model=OrderStatusResponse,
    dependencies=[Depends(get_current_admin)],
)
def confirm_order_route(order_id: int) -> OrderStatusResponse:
    """Confirm an order and decrement stock for its items."""
    try:
        result = order_service.confirm_order(order_id)
    except OrderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post(
    "/orders/{order_id}/cancel",
    response_model=OrderStatusResponse,
    dependencies=[Depends(get_current_admin)],
)
def cancel_order_route(order_id: int) -> OrderStatusResponse:
    """Cancel a pending order. Does not touch stock."""
    try:
        result = order_service.cancel_order(order_id)
    except OrderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result



from app.schemas.admin import (
    AdminStockItem,
    AdminStockListResponse,
    AdminStockUpdate,
    AdminStockCreate,
)
from app.services import product_service


@router.get(
    "/stock",
    response_model=AdminStockListResponse,
    dependencies=[Depends(get_current_admin)],
)
def list_stock(
    category: str | None = Query(None, pattern="^(engine_oil|gearbox_oil|oil_filter|additional)$"),
    q: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AdminStockListResponse:
    """List stock items including quantity (admin-only field)."""
    return product_service.list_stock_admin(
        category=category, q=q, page=page, page_size=page_size
    )


@router.patch(
    "/stock/{category}/{product_id}",
    response_model=AdminStockItem,
    dependencies=[Depends(get_current_admin)],
)
def update_stock(
    category: str,
    product_id: int,
    payload: AdminStockUpdate,
) -> AdminStockItem:
    """Partial update. Send only the fields you want to change."""
    try:
        result = product_service.update_stock_item(
            category, product_id, payload.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    return result


@router.post(
    "/stock",
    response_model=AdminStockItem,
    status_code=201,
    dependencies=[Depends(get_current_admin)],
)
def create_stock(payload: AdminStockCreate) -> AdminStockItem:
    """Create a new stock item."""
    try:
        return product_service.create_stock_item(
            payload.category, payload.model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/stock/{category}/{product_id}",
    status_code=204,
    dependencies=[Depends(get_current_admin)],
)
def delete_stock(category: str, product_id: int) -> None:
    """Delete a stock item."""
    try:
        deleted = product_service.delete_stock_item(category, product_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Produit introuvable.")





@router.post(
    "/stock/{category}/{product_id}/images",
    response_model=AdminStockItem,
    dependencies=[Depends(get_current_admin)],
)
def upload_stock_images(
    category: str,
    product_id: int,
    front: UploadFile | None = File(None, description="Face avant (JPEG/PNG/WEBP, max 5 MB)"),
    back: UploadFile | None = File(None, description="Face arrière (JPEG/PNG/WEBP, max 5 MB)"),
) -> AdminStockItem:
    """Upload or replace front/back images for a stock item. Send either or both."""
    front_bytes = front.file.read() if front else None
    front_type = front.content_type if front else None
    back_bytes = back.file.read() if back else None
    back_type = back.content_type if back else None

    try:
        result = product_service.set_stock_images(
            category, product_id,
            front_bytes, front_type,
            back_bytes, back_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    return result


@router.delete(
    "/stock/{category}/{product_id}/images/{position}",
    response_model=AdminStockItem,
    dependencies=[Depends(get_current_admin)],
)
def delete_stock_image(
    category: str,
    product_id: int,
    position: str,
) -> AdminStockItem:
    """Remove a specific image (front or back) from a stock item."""
    try:
        result = product_service.clear_stock_image(category, product_id, position)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    return result