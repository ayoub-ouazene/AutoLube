from pydantic import BaseModel, Field


class CreateSessionResponse(BaseModel):
    session_id: str = Field(..., description="Opaque session identifier. Send it back on every subsequent request.")


class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Customer message in natural language.")


class MessageResponse(BaseModel):
    reply: str = Field(..., description="Assistant reply text.")


class EndSessionResponse(BaseModel):
    ok: bool = True