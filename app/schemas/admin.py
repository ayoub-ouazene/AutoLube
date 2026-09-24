from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="JWT to send as Bearer token on admin requests.")
    token_type: str = Field("bearer", description="Always 'bearer'.")
    expires_in: int = Field(..., description="Token lifetime in seconds.")





from datetime import datetime


class AdminOrderSummary(BaseModel):
    id: int
    created_at: str = Field(..., description="ISO 8601 timestamp.")
    customer_name: str
    customer_phone: str
    wilaya: str
    city: str
    total: float
    status: str
    item_count: int


class AdminOrderListResponse(BaseModel):
    items: list[AdminOrderSummary]
    total: int
    page: int
    page_size: int
    has_next: bool


class AdminOrderItemDetail(BaseModel):
    id: int
    category: str
    product_id: int
    brand: str
    name: str
    specification: str
    size: str | None
    unit_price: float
    quantity: int
    line_total: float


class AdminOrderDetail(BaseModel):
    id: int
    created_at: str
    customer_name: str
    customer_phone: str
    customer_email: str | None
    wilaya: str
    city: str
    notes: str | None
    total: float
    status: str
    items: list[AdminOrderItemDetail]


class OrderStatusResponse(BaseModel):
    order_id: int
    status: str




class AdminStockItem(BaseModel):
    category: str
    id: int
    brand: str
    name: str
    specification: str
    viscosity: str | None = None
    size: str | None = None
    price: float
    quantity: int
    in_stock: bool


class AdminStockListResponse(BaseModel):
    items: list[AdminStockItem]
    total: int
    page: int
    page_size: int
    has_next: bool


class AdminStockUpdate(BaseModel):
    brand: str | None = Field(None, min_length=1, max_length=64)
    specification: str | None = Field(None, min_length=1, max_length=500)
    viscosity: str | None = Field(None, max_length=16)
    size: str | None = Field(None, max_length=16)
    price: float | None = Field(None, ge=0)
    quantity: int | None = Field(None, ge=0)
    category_type: str | None = Field(None, max_length=64)

class AdminStockCreate(BaseModel):
    category: str = Field(..., pattern="^(engine_oil|gearbox_oil|oil_filter|additional)$")
    brand: str = Field(..., min_length=1, max_length=64)
    specification: str = Field(..., min_length=1, max_length=500)
    viscosity: str | None = Field(None, max_length=16)
    size: str | None = Field(None, max_length=16)
    price: float = Field(..., ge=0)
    quantity: int = Field(0, ge=0)
    # Only meaningful for category == "additional"
    category_type: str | None = Field(
        None, max_length=64,
        description="Required for 'additional' category (e.g., 'liquide de frein', 'additif').",
    )
