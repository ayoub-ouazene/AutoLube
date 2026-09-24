from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.product import ProductListResponse, ProductOut
from app.services import product_service


router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    category: list[str] | None = Query(None, description="Filter by one or more categories."),
    brand: list[str] | None = Query(None, description="Filter by one or more brands."),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    size_min: float | None = Query(None, ge=0, description="Minimum size in liters."),
    size_max: float | None = Query(None, ge=0, description="Maximum size in liters."),
    q: str | None = Query(None, max_length=200, description="Free-text search."),
    sort: str = Query("random", pattern="^(random|price_asc|price_desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ProductListResponse:
    return product_service.list_products(
        categories=category,
        brands=brand,
        min_price=min_price,
        max_price=max_price,
        size_min=size_min,
        size_max=size_max,
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/{category}/{product_id}", response_model=ProductOut)
def get_product(category: str, product_id: int) -> ProductOut:
    result = product_service.get_product(category, product_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return result