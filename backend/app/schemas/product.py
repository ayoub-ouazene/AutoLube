from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    category: str = Field(..., description="engine_oil | gearbox_oil | oil_filter | additional")
    id: int
    brand: str
    name: str = Field(..., description="Display label composed from brand, viscosity, size.")
    specification: str = Field(..., description="OEM / API / reference string.")
    viscosity: str | None = None
    size: str | None = None
    price: float
    in_stock: bool
    image_front_url: str | None = None
    image_back_url: str | None = None


class ProductListResponse(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int
    has_next: bool