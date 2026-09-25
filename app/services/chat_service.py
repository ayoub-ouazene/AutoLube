import time
import uuid
from typing import Any

from app.agents.main_agent import process_turn


# ---------- session store ----------

_SESSION_MAX_SECONDS = 30 * 60   # hard cap from creation
_SESSION_IDLE_SECONDS = 10 * 60  # inactivity cap

_sessions: dict[str, dict[str, Any]] = {}


def _is_expired(session: dict[str, Any]) -> bool:
    now = time.time()
    age = now - session["created_at"]
    idle = now - session["last_activity"]
    return age > _SESSION_MAX_SECONDS or idle > _SESSION_IDLE_SECONDS


def _evict_expired() -> None:
    """Drop sessions that have exceeded either timeout."""
    expired = [sid for sid, s in _sessions.items() if _is_expired(s)]
    for sid in expired:
        _sessions.pop(sid, None)


# ---------- public API ----------

def create_session() -> str:
    _evict_expired()
    session_id = str(uuid.uuid4())
    now = time.time()
    _sessions[session_id] = {
        "history": [],
        "current_vehicle": {},
        "created_at": now,
        "last_activity": now,
    }
    return session_id


def process_message(session_id: str, message: str) -> str:
    _evict_expired()

    session = _sessions.get(session_id)
    if session is None or _is_expired(session):
        _sessions.pop(session_id, None)
        raise KeyError(f"Unknown or expired session: {session_id}")

    reply, updated_history, updated_vehicle = process_turn(
        user_message=message,
        history=session["history"],
        current_vehicle=session["current_vehicle"],
    )

    session["history"] = updated_history
    session["current_vehicle"] = updated_vehicle
    session["last_activity"] = time.time()   # <- resets idle timer
    # created_at stays fixed — that's the hard cap

    return reply


def end_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def session_exists(session_id: str) -> bool:
    _evict_expired()
    session = _sessions.get(session_id)
    return session is not None and not _is_expired(session)