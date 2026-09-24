import time
import uuid
from typing import Any

from app.agents.main_agent import process_turn


# ---------- session store ----------

_SESSION_TTL_SECONDS = 60 * 60  # 1 hour

_sessions: dict[str, dict[str, Any]] = {}


def _evict_expired() -> None:
    """Drop sessions whose last activity is older than the TTL."""
    now = time.time()
    expired = [
        sid for sid, s in _sessions.items()
        if now - s["last_used"] > _SESSION_TTL_SECONDS
    ]
    for sid in expired:
        _sessions.pop(sid, None)


# ---------- public API ----------

def create_session() -> str:
    _evict_expired()
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "history": [],
        "current_vehicle": {},
        "last_used": time.time(),
    }
    return session_id


def process_message(session_id: str, message: str) -> str:
    _evict_expired()

    session = _sessions.get(session_id)
    if session is None:
        raise KeyError(f"Unknown session: {session_id}")

    reply, updated_history, updated_vehicle = process_turn(
        user_message=message,
        history=session["history"],
        current_vehicle=session["current_vehicle"],
    )

    session["history"] = updated_history
    session["current_vehicle"] = updated_vehicle
    session["last_used"] = time.time()

    return reply


def end_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def session_exists(session_id: str) -> bool:
    _evict_expired()
    return session_id in _sessions