from pydantic import BaseModel, Field
from app.schemas.product import ProductOut

class CreateSessionResponse(BaseModel):
    session_id: str = Field(..., description="Opaque session identifier. Send it back on every subsequent request.")


class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Customer message in natural language.")


class MessageResponse(BaseModel):
    reply: str = Field(..., description="Assistant reply text.")
    products: list[ProductOut] = Field(
        default_factory=list,
        description=(
            "Products recommended in this turn, ready to render as cards. "
            "Empty when the reply is text-only (filter/brake fluid, no stock, "
            "or info request)."
        ),
    )

class EndSessionResponse(BaseModel):
    ok: bool = True