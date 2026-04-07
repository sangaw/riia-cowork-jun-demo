"""RITA request middleware.

TraceIDMiddleware
----------------
Attaches a trace ID to every request so errors and logs can be correlated.

- Reads `X-Request-ID` from the incoming request headers if the client supplies one.
- Generates a new UUID4 otherwise.
- Stores the trace ID in a ContextVar so exception handlers can read it without
  threading issues (each async task gets its own slot).
- Writes `X-Request-ID` back onto the response headers.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Module-level ContextVar — safe for concurrent async requests
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

log = structlog.get_logger()


class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = trace_id_var.set(trace_id)
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
        response = None
        try:
            response = await call_next(request)
        finally:
            log.info(
                "http.request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code if response is not None else None,
            )
            structlog.contextvars.clear_contextvars()
            trace_id_var.reset(token)
        response.headers["X-Request-ID"] = trace_id
        return response
