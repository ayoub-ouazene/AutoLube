from fastapi import APIRouter, HTTPException, status

from app.schemas.order import OrderCreate, OrderCreateResponse
from app.services import order_service
from app.services.order_service import OrderError


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate) -> OrderCreateResponse:
    try:
        result = order_service.create_order(
            customer=payload.customer.model_dump(),
            items=[i.model_dump() for i in payload.items],
        )
    except OrderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return OrderCreateResponse(**result)