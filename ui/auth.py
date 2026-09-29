"""
ui/auth.py
Agri-Advisor — T-20: Authentication helpers.

Responsibilities
----------------
* init_auth_session()   — seed all auth keys in st.session_state
* is_authenticated()    — gating predicate
* store_token()         — persist JWT + derived fields after login
* clear_auth()          — wipe auth state on logout
* get_auth_headers()    — build Authorization header for every API request
* call_register()       — POST /api/auth/register
* call_login()          — POST /api/auth/login
* maybe_refresh_error() — surface expired-token banner on 401 responses
"""
from __future__ import annotations

import logging
from typing import Any

import requests
import streamlit as st

from ui.config import API_BASE_URL, API_TIMEOUT_SEC

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Endpoint paths
# ---------------------------------------------------------------------------
REGISTER_URL = f"{API_BASE_URL}/api/auth/register"
LOGIN_URL    = f"{API_BASE_URL}/api/auth/login"

# ---------------------------------------------------------------------------
# Session-state keys (single source of truth)
# ---------------------------------------------------------------------------
_KEY_TOKEN      = "jwt_token"
_KEY_USER_ID    = "user_id"
_KEY_DISTRICT   = "saved_district"
_KEY_AUTH_ERR   = "auth_error"
_KEY_AUTH_PAGE  = "auth_page"         # "login" | "register"
_KEY_TOKEN_EXP  = "token_expired"


def init_auth_session() -> None:
    """
    Seed all T-20 auth keys in session_state on first load.
    Called once at the top of app.py, before any rendering.
    """
    defaults: dict[str, Any] = {
        _KEY_TOKEN:     None,    # str | None  — raw JWT
        _KEY_USER_ID:   None,    # str | None  — authenticated username
        _KEY_DISTRICT:  None,    # str | None  — district saved at registration
        _KEY_AUTH_ERR:  None,    # str | None  — last auth error message
        _KEY_AUTH_PAGE: "login", # which auth screen to show
        _KEY_TOKEN_EXP: False,   # True if the last API call returned 401
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------

def is_authenticated() -> bool:
    """Return True when a JWT is stored in session_state."""
    return bool(st.session_state.get(_KEY_TOKEN))


# ---------------------------------------------------------------------------
# Token lifecycle
# ---------------------------------------------------------------------------

def store_token(token: str, user_id: str, district: str | None = None) -> None:
    """
    Persist JWT and user context after a successful login.

    Args:
        token:    Raw Bearer token string returned by the backend.
        user_id:  Authenticated username / user identifier.
        district: Pre-saved district (from registration form); may be None.
    """
    st.session_state[_KEY_TOKEN]     = token
    st.session_state[_KEY_USER_ID]   = user_id
    st.session_state[_KEY_AUTH_ERR]  = None
    st.session_state[_KEY_TOKEN_EXP] = False
    if district:
        st.session_state[_KEY_DISTRICT] = district


def clear_auth() -> None:
    """
    Wipe all auth state and conversation history on logout.
    Resets the app to the login screen.
    """
    for key in (
        _KEY_TOKEN,
        _KEY_USER_ID,
        _KEY_DISTRICT,
        _KEY_AUTH_ERR,
        _KEY_TOKEN_EXP,
        # also clear query-screen state so a new login starts fresh
        "conversation_history",
        "last_response",
        "last_is_fallback",
        "last_error",
        "session_id",
    ):
        st.session_state.pop(key, None)

    st.session_state[_KEY_AUTH_PAGE] = "login"


def get_auth_headers() -> dict[str, str]:
    """
    Return the Authorization header dict if a token is present, else {}.

    Usage::

        headers = get_auth_headers()
        resp = requests.post(url, json=payload, headers=headers)
    """
    token = st.session_state.get(_KEY_TOKEN)
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ---------------------------------------------------------------------------
# T-20.6 — token-expiry flag
# ---------------------------------------------------------------------------

def mark_token_expired() -> None:
    """Call this when an API call returns HTTP 401 while authenticated."""
    st.session_state[_KEY_TOKEN_EXP] = True


def token_just_expired() -> bool:
    """True when a 401 was received in the current session."""
    return bool(st.session_state.get(_KEY_TOKEN_EXP))


# ---------------------------------------------------------------------------
# T-20.3 — Auth API calls
# ---------------------------------------------------------------------------

class AuthError(Exception):
    """Raised when register / login endpoints return an error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def call_register(
    username: str,
    password: str,
) -> dict[str, Any]:
    """
    POST /api/auth/register

    Args:
        username: Chosen username (3-254 alphanumeric chars).
        password: Password (12-128 chars).

    Returns:
        Response JSON dict e.g. {"user_id": "...", "message": "..."}.

    Raises:
        AuthError: on HTTP 4xx/5xx or network failure.
    """
    try:
        resp = requests.post(
            REGISTER_URL,
            json={"username": username, "password": password},
            timeout=API_TIMEOUT_SEC,
        )
        if resp.status_code == 201:
            return resp.json()
        # Surface server error message
        try:
            detail = resp.json().get("detail") or resp.json().get("error", {}).get("message", "")
        except Exception:
            detail = resp.text or "Registration failed."
        raise AuthError(resp.status_code, detail)

    except requests.exceptions.ConnectionError:
        raise AuthError(0, "Cannot connect to the server. Please check your network.")
    except requests.exceptions.Timeout:
        raise AuthError(0, "The server did not respond in time. Please try again.")
    except AuthError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during registration: %s", exc)
        raise AuthError(0, "An unexpected error occurred. Please try again.")


def call_login(
    username: str,
    password: str,
) -> dict[str, Any]:
    """
    POST /api/auth/login

    Returns:
        Response JSON dict with access_token, user_id, etc.

    Raises:
        AuthError: on HTTP 4xx/5xx or network failure.
    """
    try:
        resp = requests.post(
            LOGIN_URL,
            json={"username": username, "password": password},
            timeout=API_TIMEOUT_SEC,
        )
        if resp.status_code == 200:
            return resp.json()
        try:
            detail = resp.json().get("detail") or resp.json().get("error", {}).get("message", "")
        except Exception:
            detail = resp.text or "Login failed."
        raise AuthError(resp.status_code, detail)

    except requests.exceptions.ConnectionError:
        raise AuthError(0, "Cannot connect to the server. Please check your network.")
    except requests.exceptions.Timeout:
        raise AuthError(0, "The server did not respond in time. Please try again.")
    except AuthError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during login: %s", exc)
        raise AuthError(0, "An unexpected error occurred. Please try again.")
