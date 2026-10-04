"""
ui/admin.py
Admin-only dashboard for the Streamlit frontend.

The dashboard deliberately reads the existing SQLite stores and the existing
health endpoint. It does not add an API, event tracking, or an analytics store.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

import requests
import streamlit as st

from ui.config import API_BASE_URL


# ============================================================================
# Admin authentication
# ============================================================================

ADMIN_USERNAME = "admin123"
ADMIN_PASSWORD = "password12345"
ADMIN_SESSION_KEY = "admin_authenticated"


# ============================================================================
# Paths
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
USERS_DB = PROJECT_ROOT / "data" / "users.sqlite3"
HISTORY_DB = PROJECT_ROOT / "data" / "chat_history.sqlite3"


# ============================================================================
# Admin navigation
# ============================================================================

ADMIN_PAGES = (
    ("dashboard", "Dashboard"),
    ("users", "Users"),
    ("analytics", "Analytics"),
    ("feedback", "Feedback"),
    ("health", "System Health"),
)


# ============================================================================
# Authentication helpers
# ============================================================================

def is_admin_credentials(username: str, password: str) -> bool:
    """Return whether the supplied values match the local admin account."""
    return username.strip() == ADMIN_USERNAME and password == ADMIN_PASSWORD


def is_admin_authenticated() -> bool:
    """Return whether the current Streamlit session is authenticated as admin."""
    return bool(st.session_state.get(ADMIN_SESSION_KEY, False))


def admin_logout() -> None:
    """Log out the current administrator."""
    st.session_state[ADMIN_SESSION_KEY] = False
    st.session_state["admin_page"] = "dashboard"
    st.session_state["auth_page"] = "login"


# ============================================================================
# Admin login
# ============================================================================

def render_admin_login() -> None:
    """Render the separate admin login without calling the user API."""
    st.markdown(
        """
        <style>
        .admin-login-wrapper {
            max-width: 460px;
            margin: 4rem auto 0 auto;
        }
        .admin-login-title {
            text-align: center;
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: .25rem;
        }
        .admin-login-subtitle {
            text-align: center;
            color: #6B7280;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="admin-login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="admin-login-title">🔐 Admin Sign In</div>', unsafe_allow_html=True)
    st.markdown('<div class="admin-login-subtitle">This area is restricted to administrators.</div>', unsafe_allow_html=True)

    with st.form("admin_login_form"):
        username = st.text_input("Username", key="admin_username")
        password = st.text_input("Password", type="password", key="admin_password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

    if submitted:
        if is_admin_credentials(username, password):
            st.session_state[ADMIN_SESSION_KEY] = True
            st.session_state["admin_page"] = "dashboard"
            st.session_state["auth_page"] = "login"
            st.rerun()

        st.error("Incorrect username or password. Please check and try again.")

    if st.button("Back to user sign in", use_container_width=True, key="admin_back_to_user"):
        st.session_state["auth_page"] = "login"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# Admin CSS
# ============================================================================

_ADMIN_SIDEBAR_OPEN = """
section[data-testid="stSidebar"] {
    display: flex !important;
    visibility: visible !important;
}

[data-testid="stMain"],
section.main {
    margin-left: var(--app-sidebar-width) !important;
    width: calc(100% - var(--app-sidebar-width)) !important;
}

@media (max-width: 768px) {
    [data-testid="stMain"],
    section.main {
        margin-left: 0 !important;
        width: 100% !important;
    }
}
"""

_ADMIN_SIDEBAR_CLOSED = """
section[data-testid="stSidebar"] {
    display: none !important;
    visibility: hidden !important;
}

[data-testid="stMain"],
section.main {
    margin-left: 0 !important;
    width: 100% !important;
}
"""

ADMIN_CSS_BASE = """
<style>

:root {
    --app-sidebar-width: 300px;
    --app-sidebar-mobile-width: min(86vw, 320px);
}

/* Hide default Streamlit navbar/header chrome */
header[data-testid="stHeader"],
[data-testid="stSidebarHeader"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stExpandSidebarButton"] {
    display: none !important;
}

.admin-page {
    width: 100%;
}

/* Fixed top bar */
div[data-testid="stHorizontalBlock"]:has(.admin-brand) {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    width: 100% !important;
    height: 64px;
    z-index: 10000;
    display: flex;
    flex-wrap: nowrap !important;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.25rem;
    background: #123D27;
    color: white;
    border-bottom: 1px solid rgba(255,255,255,.15);
    box-shadow: 0 2px 10px rgba(0,0,0,.12);
}

div[data-testid="stHorizontalBlock"]:has(.admin-brand) > div {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.admin-brand) > div:has(.admin-brand) {
    flex: 1 1 auto !important;
}

/* ☰ Toggle button styling in admin topbar */
div[data-testid="stHorizontalBlock"]:has(.admin-brand) > div:first-child button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: white !important;
    font-size: 1.6rem !important;
    line-height: 1 !important;
    padding: .25rem .65rem !important;
    min-height: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.admin-brand) > div:first-child button:hover {
    background: rgba(255, 255, 255, 0.1) !important;
}

.admin-brand {
    display: flex;
    align-items: center;
    gap: .65rem;
    font-size: 1.15rem;
    font-weight: 800;
    white-space: nowrap;
}

.admin-brand-icon {
    font-size: 1.45rem;
}

.admin-brand-subtitle {
    font-size: .78rem;
    font-weight: 500;
    opacity: .75;
    margin-left: .35rem;
}

/* Sidebar structure */
section[data-testid="stSidebar"] {
    position: fixed !important;
    top: 64px !important;
    left: 0 !important;
    bottom: 0 !important;
    width: var(--app-sidebar-width) !important;
    min-width: var(--app-sidebar-width) !important;
    max-width: var(--app-sidebar-width) !important;
    z-index: 9000 !important;
    background: #F1F8F3 !important;
    border-right: 1px solid #D5EADB !important;
    transform: none !important;
    visibility: visible !important;
}

section[data-testid="stSidebar"] > div {
    width: 100% !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 1rem !important;
}

.admin-sidebar-title {
    font-size: 1rem;
    font-weight: 800;
    color: #1F3D2B;
    margin-bottom: .25rem;
}

.admin-sidebar-subtitle {
    font-size: .8rem;
    color: #6B7280;
    margin-bottom: 1rem;
}

.admin-sidebar-section {
    font-size: .75rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #6B7280;
    margin: 1rem 0 .4rem 0;
}

/* Admin navigation buttons */
[class*="st-key-admin_nav_"] button {
    width: 100% !important;
    justify-content: flex-start !important;
    text-align: left !important;
    border-radius: 8px !important;
    border: none !important;
    padding: .55rem .7rem !important;
    color: #1F2937 !important;
    background: transparent !important;
    box-shadow: none !important;
    font-weight: 500 !important;
}

[class*="st-key-admin_nav_"] button:hover {
    background: #DDF1E2 !important;
}

[class*="st-key-admin_nav_"] button[kind="primary"],
[class*="st-key-admin_nav_"] [data-testid="stBaseButton-primary"] {
    background: #D0EAD8 !important;
    color: #14532D !important;
    font-weight: 700 !important;
}

/* Main container top padding */
.block-container,
[data-testid="stMainBlockContainer"] {
    padding-top: 80px !important;
}

.admin-card {
    background: white;
    border: 1px solid #D5EADB;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 3px 12px rgba(0,0,0,.05);
}

@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        width: var(--app-sidebar-mobile-width) !important;
        min-width: var(--app-sidebar-mobile-width) !important;
        max-width: var(--app-sidebar-mobile-width) !important;
    }
    [data-testid="stMain"],
    section.main {
        padding-left: 0 !important;
    }
    .admin-brand-subtitle {
        display: none;
    }
}

</style>
"""


# ============================================================================
# Navigation callbacks & Top bar
# ============================================================================

def toggle_admin_navigation() -> None:
    """☰ handler: show / hide sidebar in session state."""
    st.session_state.show_nav_menu = not st.session_state.get("show_nav_menu", True)


def _render_admin_topbar() -> None:
    """Render topbar with ☰ toggle, logo, title, and subtitle."""
    col_toggle, col_brand = st.columns([1, 15], vertical_alignment="center")

    with col_toggle:
        st.button(
            "☰",
            key="admin_topnav_toggle",
            on_click=toggle_admin_navigation,
            help="Show / hide the sidebar",
        )

    with col_brand:
        st.markdown(
            """
            <div class="admin-brand">
                <span class="admin-brand-icon">🌱</span>
                <span>Agri-Advisor</span>
                <span class="admin-brand-subtitle">ADMIN PANEL</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================================
# Admin sidebar
# ============================================================================

def _set_admin_page(page_id: str) -> None:
    """Change the active admin page."""
    st.session_state["admin_page"] = page_id


def _render_admin_sidebar() -> None:
    """Render only admin navigation in the sidebar."""
    selected = st.session_state.get("admin_page", "dashboard")

    with st.sidebar:
        st.markdown(
            """
            <div class="admin-sidebar-title">Admin Panel</div>
            <div class="admin-sidebar-subtitle">System management and monitoring</div>
            <div class="admin-sidebar-section">Navigation</div>
            """,
            unsafe_allow_html=True,
        )

        for page_id, label in ADMIN_PAGES:
            icon = {
                "dashboard": "📊",
                "users": "👥",
                "analytics": "📈",
                "feedback": "💬",
                "health": "🩺",
            }.get(page_id, "•")

            st.button(
                f"{icon}  {label}",
                key=f"admin_nav_{page_id}",
                type="primary" if page_id == selected else "secondary",
                use_container_width=True,
                on_click=_set_admin_page,
                args=(page_id,),
            )

        st.markdown('<div class="admin-sidebar-section">Session</div>', unsafe_allow_html=True)
        st.caption(f"Signed in as: {ADMIN_USERNAME}")

        if st.button("🚪 Logout", key="admin_sidebar_logout", use_container_width=True):
            admin_logout()
            st.rerun()


# ============================================================================
# Database readers
# ============================================================================

def _read_users() -> list[dict[str, Any]]:
    """Read users from SQLite user database."""
    if not USERS_DB.exists():
        return []

    with sqlite3.connect(USERS_DB) as connection:
        rows = connection.execute(
            "SELECT username, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()

    return [{"username": row[0], "created_at": row[1]} for row in rows]


def _read_history() -> dict[str, dict[str, Any]]:
    """Read conversation history from SQLite store."""
    if not HISTORY_DB.exists():
        return {}

    with sqlite3.connect(HISTORY_DB) as connection:
        rows = connection.execute(
            "SELECT user_id, history_json, updated_at FROM conversation_history"
        ).fetchall()

    result: dict[str, dict[str, Any]] = {}
    for user_id, history_json, updated_at in rows:
        try:
            history = json.loads(history_json)
        except (TypeError, json.JSONDecodeError):
            history = []

        result[user_id] = {
            "history": history if isinstance(history, list) else [],
            "updated_at": updated_at,
        }

    return result


# ============================================================================
# Data helpers
# ============================================================================

def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _user_rows(
    users: list[dict[str, Any]],
    histories: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for user in users:
        username = user["username"]
        record = histories.get(username, {})
        history = record.get("history", [])

        rows.append(
            {
                "Username": username,
                "Registration date": user["created_at"],
                "Last activity": record.get("updated_at", "N/A"),
                "District": "N/A",
                "Preferred language": "N/A",
                "Chat count": len(history),
                "AI request count": len(history),
                "Feedback count": "N/A",
            }
        )
    return rows


def _all_turns(histories: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    for user_id, record in histories.items():
        for turn in record.get("history", []):
            if isinstance(turn, dict):
                turns.append({**turn, "user_id": user_id})
    return turns


def _counts(turns: list[dict[str, Any]], key: str) -> dict[str, int]:
    values = [str(turn.get(key) or "N/A") for turn in turns]
    return dict(Counter(values))


# ============================================================================
# Health
# ============================================================================

def _health() -> dict[str, Any] | None:
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else None
    except (requests.RequestException, ValueError):
        return None


def _metric(label: str, value: Any) -> None:
    st.metric(label, value if value not in (None, "") else "N/A")


# ============================================================================
# Dashboard
# ============================================================================

def _render_overview(
    users: list[dict[str, Any]],
    turns: list[dict[str, Any]],
) -> None:
    histories = _read_history()
    active_cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    active_users = sum(
        1
        for record in histories.values()
        if (_parse_timestamp(record.get("updated_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= active_cutoff
    )

    st.title("Dashboard")
    st.caption("Agri-Advisor system overview")

    cols = st.columns(6)
    values = [
        ("Total Users", len(users)),
        ("Active Users", active_users),
        ("Total Chats", len(turns)),
        ("Total Feedback", "N/A"),
        ("Average Rating", "N/A"),
        ("AI Requests", len(turns)),
    ]

    for column, (label, value) in zip(cols, values):
        with column:
            _metric(label, value)

    st.divider()

    st.subheader("AI request/activity trends")
    st.info("N/A — individual query timestamps are not persisted in the existing history store.")

    st.subheader("Feedback summary")
    st.info("N/A — feedback is held in backend memory and has no read API or durable store.")


# ============================================================================
# Users
# ============================================================================

def _render_users(
    users: list[dict[str, Any]],
    histories: dict[str, dict[str, Any]],
) -> None:
    st.title("Users")
    rows = _user_rows(users, histories)

    search = st.text_input("Search by username", key="admin_user_search").strip().lower()
    if search:
        rows = [row for row in rows if search in row["Username"].lower()]

    st.dataframe(rows, use_container_width=True, hide_index=True)


# ============================================================================
# Analytics
# ============================================================================

def _render_analytics(turns: list[dict[str, Any]]) -> None:
    st.title("Analytics")

    district_counts = _counts(turns, "district")
    crop_counts = _counts(turns, "crop_context")

    st.markdown("**Users by district**")
    st.info("N/A — district is not stored in the user database.")

    st.markdown("**Queries by district / most active districts**")
    st.dataframe(
        [
            {"District": key, "Queries": value}
            for key, value in sorted(district_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        use_container_width=True,
        hide_index=True,
    )

    if district_counts and any(key != "N/A" for key in district_counts):
        st.bar_chart(district_counts)

    st.markdown("**Most requested crops / crop requests**")
    st.dataframe(
        [
            {"Crop": key, "Requests": value}
            for key, value in sorted(crop_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        use_container_width=True,
        hide_index=True,
    )

    if crop_counts and any(key != "N/A" for key in crop_counts):
        st.bar_chart(crop_counts)

    st.markdown("**Crop × district**")
    st.info("N/A — the existing history does not retain a per-query crop/district pair reliably.")

    st.markdown("**Crop × disease**")
    st.info("N/A — disease results are not persisted in the existing history store.")

    st.markdown("**Disease cases by district**")
    st.info("N/A — disease cases are not persisted in the existing history store.")

    st.markdown("**Feedback statistics / feedback over time**")
    st.info("N/A — feedback is backend memory only and is not exposed to the UI.")


# ============================================================================
# Feedback
# ============================================================================

def _render_feedback() -> None:
    st.title("Feedback")
    st.info("N/A — feedback is held in backend memory and has no read API or durable store.")


# ============================================================================
# System health
# ============================================================================

def _render_health() -> None:
    st.title("System Health")
    health = _health()

    if not health:
        st.error("Unable to reach the existing /api/health endpoint.")
        return

    st.metric("Overall status", health.get("status", "N/A"))
    services = health.get("services", {})

    if isinstance(services, dict):
        st.dataframe(
            [
                {
                    "Service": name,
                    "Status": details.get("status", "N/A"),
                    "Latency (ms)": details.get("latency_ms", "N/A"),
                    "Message": details.get("message", "N/A"),
                }
                for name, details in services.items()
                if isinstance(details, dict)
            ],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================================
# Main admin dashboard
# ============================================================================

def render_admin_dashboard() -> None:
    """Render the isolated, read-only admin dashboard."""
    if "show_nav_menu" not in st.session_state:
        st.session_state["show_nav_menu"] = False

    sidebar_open = bool(st.session_state["show_nav_menu"])
    sidebar_css = _ADMIN_SIDEBAR_OPEN if sidebar_open else _ADMIN_SIDEBAR_CLOSED

    st.markdown(ADMIN_CSS_BASE + f"<style>{sidebar_css}</style>", unsafe_allow_html=True)

    users = _read_users()
    histories = _read_history()
    turns = _all_turns(histories)

    _render_admin_topbar()
    _render_admin_sidebar()

    selected = st.session_state.get("admin_page", "dashboard")

    if selected == "dashboard":
        _render_overview(users, turns)
    elif selected == "users":
        _render_users(users, histories)
    elif selected == "analytics":
        _render_analytics(turns)
    elif selected == "feedback":
        _render_feedback()
    elif selected == "health":
        _render_health()
    else:
        st.session_state["admin_page"] = "dashboard"
        _render_overview(users, turns)