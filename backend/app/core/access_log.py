import time
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


# Per-request duration. Set by the middleware, read by the patched formatter.
_duration: ContextVar[float | None] = ContextVar("request_duration", default=None)


class AccessDurationMiddleware(BaseHTTPMiddleware):
    """Measures each request and stores the duration in a contextvar."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            _duration.set(time.perf_counter() - start)
        return response


_patch_installed = False


def install_uvicorn_duration_patch() -> None:
    """
    Patch uvicorn's AccessFormatter once so it appends the request duration
    from the contextvar. Idempotent.
    """
    global _patch_installed
    if _patch_installed:
        return

    from uvicorn.logging import AccessFormatter

    original_format_message = AccessFormatter.formatMessage

    def patched_format_message(self, record):
        line = original_format_message(self, record)
        # Only access log records have exactly 5 tuple args:
        # (client_addr, method, path, http_version, status_code)
        if isinstance(record.args, tuple) and len(record.args) == 5:
            d = _duration.get()
            if d is not None:
                line = f"{line} ({d:.3f}s)"
        return line

    AccessFormatter.formatMessage = patched_format_message
    _patch_installed = True