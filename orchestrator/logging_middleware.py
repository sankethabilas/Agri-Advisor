"""
Request/Response Logging Middleware for Agri-Advisor Orchestrator (Subtask T-06.6).
Injects correlation IDs (X-Request-ID), measures processing latency, and records structured access logs.
"""

import logging
import sys
import time
from typing import Callable
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Configure structured logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("agri_advisor.orchestrator")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """FastAPI / Starlette middleware for request tracing and latency logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Correlation ID from incoming header or freshly generated
        request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:8]}"
        request.state.request_id = request_id

        start_time = time.perf_counter()
        client_host = request.client.host if request.client else "unknown"

        logger.info(
            f"--> [{request_id}] {request.method} {request.url.path} (client: {client_host})"
        )

        try:
            response: Response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = str(duration_ms)

            logger.info(
                f"<-- [{request_id}] {request.method} {request.url.path} | status={response.status_code} | latency={duration_ms}ms"
            )
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"<-- [{request_id}] {request.method} {request.url.path} | ERROR: {type(exc).__name__} | latency={duration_ms}ms"
            )
            raise
