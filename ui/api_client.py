"""
ui/api_client.py
Handles all communication with the FastAPI Orchestrator backend.
Falls back gracefully to fixture data when the API is unreachable.

T-20 additions:
    - call_orchestrator() now attaches the JWT Bearer token from
      session state to every request (T-20.4).
    - HTTP 401 responses trigger mark_token_expired() so the auth
      gate re-shows the login screen with an expiry message (T-20.6).
    - build_payload() now accepts user_id and district from the
      authenticated session (T-20.7).
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import requests

from ui.config import (
    FALLBACK_FIXTURE,
    ORCHESTRATOR_URL,
    API_TIMEOUT_SEC,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------

def build_payload(
    query: str,
    user_id: str,
    district: str,
    language: str,
    crop_context: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Construct the OrchestratorProcessRequest payload.

    T-20.7: user_id comes from the authenticated session; district
    defaults to the saved district when present.
    """
    payload: dict[str, Any] = {
        "query":    query,
        "user_id":  user_id,
        "location": {"district": district},
        "language": language,
    }
    if crop_context:
        payload["crop_context"] = crop_context
    if session_id:
        payload["session_id"] = session_id
    return payload


# ---------------------------------------------------------------------------
# API call + fallback
# ---------------------------------------------------------------------------

def call_orchestrator(
    payload: dict[str, Any],
    auth_headers: dict[str, str] | None = None,
) -> tuple[dict[str, Any], bool]:
    """
    POST to the orchestrator endpoint.

    T-20.4: auth_headers ({"Authorization": "Bearer <token>"}) are merged
    into every outgoing request.

    Returns:
        (response_dict, is_fallback)
        is_fallback=True when fixture data was returned instead of a live response.

    Raises:
        _ApiError: for HTTP 4xx / 5xx that should be surfaced in the UI.
    """
    headers = auth_headers or {}

    try:
        resp = requests.post(
            ORCHESTRATOR_URL,
            json=payload,
            headers=headers,
            timeout=API_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        return resp.json(), False

    except requests.exceptions.ConnectionError:
        logger.warning("Orchestrator API unreachable — loading fixture data.")
        return _load_fallback(), True

    except requests.exceptions.Timeout:
        logger.warning(
            "Orchestrator API timed out after %s s — loading fixture data.",
            API_TIMEOUT_SEC,
        )
        return _load_fallback(), True

    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 0
        try:
            error_body = exc.response.json()
        except Exception:
            error_body = {}
        error_body["_http_status"] = status_code

        # T-20.6: flag token expiry so app.py can redirect to login
        if status_code == 401:
            _flag_token_expired()

        raise _ApiError(status_code, error_body) from exc

    except Exception as exc:
        logger.exception("Unexpected error calling orchestrator: %s", exc)
        return _load_fallback(), True


def _load_fallback() -> dict[str, Any]:
    """Load and return the fixture JSON response."""
    with FALLBACK_FIXTURE.open(encoding="utf-8") as fh:
        return json.load(fh)


def _flag_token_expired() -> None:
    """
    Mark the session token as expired.

    Import is deferred to avoid circular imports between api_client ↔ auth.
    """
    try:
        from ui.auth import mark_token_expired  # noqa: PLC0415
        mark_token_expired()
    except Exception:
        pass  # auth module not loaded yet — harmless


# ---------------------------------------------------------------------------
# Custom exception for HTTP errors
# ---------------------------------------------------------------------------

class _ApiError(Exception):
    """Raised when the API returns an HTTP error that should be surfaced in the UI."""

    def __init__(self, status_code: int, body: dict[str, Any]) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}")
