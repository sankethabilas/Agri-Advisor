"""Small shared helpers for bounded external dependency recovery."""

import json
import logging
import time
from typing import Callable, TypeVar

import requests

logger = logging.getLogger("agri_advisor.resilience")
T = TypeVar("T")


def log_structured(
    target: logging.Logger,
    level: int,
    event: str,
    *,
    exc_info: bool = False,
    **fields: object,
) -> None:
    """Write JSON event data and retain fields on the LogRecord for test tooling."""
    record = {"event": event, **fields}
    target.log(
        level,
        json.dumps(record, sort_keys=True, default=str),
        extra=record,
        exc_info=exc_info,
    )


def request_with_retry(
    operation: Callable[[], requests.Response],
    *,
    service: str,
    attempts: int = 3,
    base_delay_seconds: float = 0.2,
) -> requests.Response:
    """Execute an HTTP request with bounded exponential backoff."""
    for attempt in range(1, attempts + 1):
        try:
            response = operation()
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            log_structured(
                logger,
                logging.WARNING,
                "external_api_request_failed",
                service=service,
                attempt=attempt,
                max_attempts=attempts,
                exception_type=type(exc).__name__,
            )
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
            retryable = (
                status_code is None
                or status_code in (408, 429)
                or status_code >= 500
            )
            if attempt == attempts or not retryable:
                raise
            time.sleep(base_delay_seconds * (2 ** (attempt - 1)))
    raise RuntimeError("External request retry loop exited unexpectedly")