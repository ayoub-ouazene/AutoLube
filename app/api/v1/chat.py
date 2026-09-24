from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import (
    CreateSessionResponse,
    MessageRequest,
    MessageResponse,
    EndSessionResponse,
)
from app.services import chat_service


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/session",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session() -> CreateSessionResponse:
    """Start a new chat session. Returns a session_id to use on subsequent calls."""
    session_id = chat_service.create_session()
    return CreateSessionResponse(session_id=session_id)


@router.post(
    "/session/{session_id}/message",
    response_model=MessageResponse,
)
def send_message(session_id: str, payload: MessageRequest) -> MessageResponse:
    """Send a user message and get the assistant reply."""
    if not chat_service.session_exists(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired.",
        )
    try:
        reply = chat_service.process_message(session_id, payload.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {e}",
        )
    return MessageResponse(reply=reply)


@router.delete(
    "/session/{session_id}",
    response_model=EndSessionResponse,
)
def end_session(session_id: str) -> EndSessionResponse:
    """End a chat session and free its history."""
    chat_service.end_session(session_id)
    return EndSessionResponse(ok=True)