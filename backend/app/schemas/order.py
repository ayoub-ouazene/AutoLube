from pydantic import BaseModel, Field


class OrderItemIn(BaseModel):
    category: str = Field(..., pattern="^(engine_oil|gearbox_oil|oil_filter|additional)$")
    id: int
    quantity: int = Field(..., ge=1, le=50)


class CustomerInfo(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=128)
    phone: str = Field(..., min_length=6, max_length=32)
    email: str | None = Field(None, max_length=128)
    wilaya: str = Field(..., min_length=2, max_length=64)
    city: str = Field(..., min_length=2, max_length=64)
    notes: str | None = Field(None, max_length=500)


class OrderCreate(BaseModel):
    customer: CustomerInfo
    items: list[OrderItemIn] = Field(..., min_length=1, max_length=30)


class OrderItemOut(BaseModel):
    category: str
    product_id: int
    name: str
    size: str | None
    unit_price: float
    quantity: int
    line_total: float


class OrderCreateResponse(BaseModel):
    order_id: int
    total: float
    items: list[OrderItemOut]
    whatsapp_url: str