"""
ui/api_client.py
Handles all communication with the FastAPI Orchestrator backend.

T-20 additions:
    - call_orchestrator() now attaches the JWT Bearer token from
      session state to every request (T-20.4).
    - HTTP 401 responses trigger mark_token_expired() so the auth
      gate re-shows the login screen with an expiry message (T-20.6).
    - build_payload() now accepts user_id and district from the
      authenticated session (T-20.7).
"""
from __future__ import annotations

import logging
from typing import Any

import requests

from ui.config import (
    FEEDBACK_URL,
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
# API calls
# ---------------------------------------------------------------------------

def call_orchestrator(
    payload: dict[str, Any],
    auth_headers: dict[str, str] | None = None,
) -> tuple[dict[str, Any], bool]:
    """
    POST to the orchestrator endpoint.

    T-20.4: auth_headers ({"Authorization": "Bearer <token>"}) are merged
    into every outgoing request.

    Returns the live response and a false fallback flag. Fixtures are reserved
    for an explicit demo mode and must not hide a broken backend integration.

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

    except requests.exceptions.ConnectionError as exc:
        raise _ApiError(
            503, {"detail": "The advisory service is unavailable."}) from exc

    except requests.exceptions.Timeout:
        raise _ApiError(504, {
                        "detail": f"The advisory service timed out after {API_TIMEOUT_SEC} seconds."}) from exc

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
        raise _ApiError(
            503, {"detail": "The advisory service returned an invalid response."}) from exc


def submit_feedback(
    session_id: str,
    helpful: bool,
    auth_headers: dict[str, str] | None = None,
) -> None:
    """Submit FR-50 feedback using the same authenticated session."""
    try:
        resp = requests.post(
            FEEDBACK_URL,
            json={"session_id": session_id, "helpful": helpful},
            headers=auth_headers or {},
            timeout=API_TIMEOUT_SEC,
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 0
        if status_code == 401:
            _flag_token_expired()
        raise _ApiError(
            status_code, {"detail": "Feedback could not be submitted."}) from exc
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise _ApiError(
            503, {"detail": "Feedback service is unavailable."}) from exc


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

    def __init__(self, status_code: int, body: dict[str, Any] | str | None = None) -> None:
        self.status_code = status_code
        if isinstance(body, dict):
            self.body = body
            self.detail = body.get("detail", body.get("message", f"HTTP error {status_code}"))
        elif isinstance(body, str):
            self.body = {"detail": body}
            self.detail = body
        else:
            self.body = {}
            self.detail = f"HTTP error {status_code}"
            
        if status_code == 401 and (self.detail in ("Not authenticated", "Unauthorized") or not self.detail):
            self.detail = "Session expired or unauthorized. Please log in again."

        super().__init__(f"HTTP {status_code}: {self.detail}")

