import asyncio
import contextlib
import time
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# ------------------------------------------------------------------ config

# Each rule: (method, path_pattern, limit, window_seconds, key_source)
# key_source is either "ip" or the name of a path capture like "session_id".
RATE_LIMITS: list[tuple[str, str, int, int, str]] = [
    ("POST",   "/api/v1/chat/session",                                 20, 60, "ip"),
    ("POST",   "/api/v1/chat/session/{session_id}/message",            15, 60, "session_id"),
    ("POST",   "/api/v1/orders",                                       5, 60, "ip"),
    ("POST",   "/api/v1/admin/login",                                   5, 60, "ip"),
    ("POST",   "/api/v1/admin/stock",                                  30, 60, "ip"),
    ("POST",   "/api/v1/admin/stock/{category}/{product_id}/images",   10, 60, "ip"),
    ("PATCH",  "/api/v1/admin/stock/{category}/{product_id}",          60, 60, "ip"),
    ("DELETE", "/api/v1/admin/stock/{category}/{product_id}",          30, 60, "ip"),
]

# Longest window in the config, used by the sweep to decide what's dead.
_MAX_WINDOW = max(rule[3] for rule in RATE_LIMITS)


# ------------------------------------------------------------------ state

# key -> sorted list of monotonic timestamps of the requests in the window
_buckets: dict[str, list[float]] = {}


# ------------------------------------------------------------------ helpers

def _path_matches(pattern: str, path: str) -> tuple[bool, dict[str, str]]:
    """
    Match a pattern like "/api/v1/chat/session/{session_id}/message" against
    a concrete path. Returns (matched, captures). Segments must match 1:1;
    a "{name}" segment captures any single non-empty segment.
    """
    p_segs = pattern.strip("/").split("/")
    a_segs = path.strip("/").split("/")
    if len(p_segs) != len(a_segs):
        return False, {}

    captures: dict[str, str] = {}
    for p_seg, a_seg in zip(p_segs, a_segs):
        if p_seg.startswith("{") and p_seg.endswith("}"):
            captures[p_seg[1:-1]] = a_seg
        elif p_seg != a_seg:
            return False, {}
    return True, captures


def _find_rule(method: str, path: str) -> tuple[int, int, str, dict[str, str]] | None:
    for r_method, pattern, limit, window, key_source in RATE_LIMITS:
        if r_method != method:
            continue
        matched, captures = _path_matches(pattern, path)
        if matched:
            return limit, window, key_source, captures
    return None


def _build_key(request: Request, key_source: str, captures: dict[str, str]) -> str | None:
    if key_source == "ip":
        host = request.client.host if request.client else "unknown"
        return f"ip:{host}"
    # Named path capture
    value = captures.get(key_source)
    if not value:
        return None
    return f"{key_source}:{value}"


def _check(key: str, limit: int, window: int) -> tuple[bool, float]:
    """
    Sliding window check.
    Returns (allowed, retry_after_seconds).
    """
    now = time.monotonic()
    cutoff = now - window

    bucket = _buckets.get(key, [])
    # Drop entries that fell out of the window (they're at the head)
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)

    if len(bucket) >= limit:
        # Earliest entry will fall off at bucket[0] + window
        retry_after = window - (now - bucket[0])
        return False, max(retry_after, 0.0)

    bucket.append(now)
    _buckets[key] = bucket
    return True, 0.0


def _sweep_expired() -> int:
    """Drop keys whose newest request is older than the longest window."""
    now = time.monotonic()
    dead = [
        key for key, bucket in _buckets.items()
        if not bucket or (now - bucket[-1]) > _MAX_WINDOW
    ]
    for key in dead:
        del _buckets[key]
    return len(dead)


# ------------------------------------------------------------------ middleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # FastAPI prefixes everything with /api/v1 via the router; compare on
        # the full path since that's what comes in on the wire.
        rule = _find_rule(request.method, request.url.path)
        if rule is None:
            return await call_next(request)

        limit, window, key_source, captures = rule
        key = _build_key(request, key_source, captures)
        if key is None:
            # e.g. missing session_id in the URL — let the route 404 naturally
            return await call_next(request)

        allowed, retry_after = _check(key, limit, window)
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Trop de requêtes. Veuillez réessayer dans un instant."
                },
                headers={"Retry-After": str(int(retry_after) + 1)},
            )

        return await call_next(request)


# ------------------------------------------------------------------ background sweep

_cleanup_task: asyncio.Task | None = None


async def _cleanup_loop() -> None:
    try:
        while True:
            await asyncio.sleep(60)
            removed = _sweep_expired()
            if removed:
                print(f"[rate_limit] swept {removed} expired key(s)")
    except asyncio.CancelledError:
        pass


def start_cleanup_task() -> asyncio.Task:
    global _cleanup_task
    _cleanup_task = asyncio.create_task(_cleanup_loop())
    return _cleanup_task


async def stop_cleanup_task(task: asyncio.Task) -> None:
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task