"""
ui/app.py
Agri-Advisor — Streamlit UI Shell  (Task T-08 + T-17 + T-20)

Entry point:
    streamlit run ui/app.py

Design spec:  /docs/ui-spec.md
API contract: /docs/api-contract.md
Backend:      POST http://localhost:8000/api/orchestrator/process  (T-06)

T-17 additions:
    - Language selector (en / si / ta) persisted in session_state["selected_language"]
    - All static UI strings sourced from utils.i18n.get_string()
    - Dynamic advisory output translated at render-time via advisory_renderer

T-20 additions:
    - Registration screen  (T-20.1)
    - Login screen with client-side validation  (T-20.2)
    - JWT stored in session_state, attached to every API request  (T-20.4)
    - Query screen is gated behind authentication  (T-20.5)
    - Logout control in sidebar  (T-20.5)
    - Friendly error messages for invalid credentials / expired tokens  (T-20.6)
    - Authenticated user_id and saved district in query payload  (T-20.7)
"""
from __future__ import annotations
import streamlit as st
from ui.api_client import _ApiError, build_payload, call_orchestrator
from ui.auth import (
    clear_auth,
    get_auth_headers,
    init_auth_session,
    is_authenticated,
    token_just_expired,
)
from ui.auth_pages import render_auth_screen
from ui.components import (
    render_advisory_response,
    render_conversation_history,
    render_error,
)
from ui.config import (
    APP_ICON,
    APP_SUBTITLE,
    APP_TITLE,
    CROP_CONTEXTS,
    DISTRICTS,
)
from ui.history_store import load_history, save_history
from ui.styles import DARK_MODE_CSS, GLOBAL_CSS, LIGHT_MODE_CSS
from utils.i18n import SUPPORTED_LANGUAGES, get_string

import sys
import uuid
from pathlib import Path

# Make project-local packages importable when Streamlit launches this file
# directly (for example: `streamlit run ui/app.py`).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# T-17: i18n helpers


# ============================================================================
# Page configuration  (must be the very first Streamlit call)
# ============================================================================
st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_SUBTITLE}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help":     "https://doa.gov.lk",
        "Report a bug": None,
        "About":        f"**{get_string('app_title', 'en')}** · {get_string('app_subtitle', 'en')} · v0.1.0",
    },
)


# ============================================================================
# Session-state initialisation
# ============================================================================

def _init_session() -> None:
    """Initialise all session-state keys on first load (T-08 + T-17 + T-20)."""
    # T-20: auth keys first (they gate everything else)
    init_auth_session()

    # Query screen state (only relevant after login)
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "last_response" not in st.session_state:
        st.session_state.last_response = None
    if "last_is_fallback" not in st.session_state:
        st.session_state.last_is_fallback = False
    if "last_error" not in st.session_state:
        st.session_state.last_error = None

    # T-17 locale
    if "language" not in st.session_state:
        st.session_state.language = "en"
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "en"
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "System"
    if "show_nav_menu" not in st.session_state:
        st.session_state.show_nav_menu = False

    user_id = st.session_state.get("user_id")
    if user_id and st.session_state.get("history_owner") != user_id:
        st.session_state.conversation_history = load_history(user_id)
        st.session_state.history_owner = user_id


_init_session()


def _render_top_nav() -> None:
    """Render the brand, account identity, language, and theme controls."""
    _lang = st.session_state.get("selected_language", "en")
    nav_brand, nav_user, nav_language, nav_theme = st.columns(
        [4.8, 1.4, 1.7, 1.5],
        vertical_alignment="center",
    )

    with nav_brand:
        st.markdown(
            f"""
            <div class="top-nav-brand">
                <span class="top-nav-mark">{APP_ICON}</span>
                <span>
                    <strong>{get_string('app_title', _lang)}</strong>
                    <small>{get_string('app_tagline', _lang)}</small>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with nav_user:
        user_id = st.session_state.get("user_id")
        if user_id:
            st.markdown(
                f'<div class="top-nav-user">👤 <strong>{user_id}</strong></div>',
                unsafe_allow_html=True,
            )

    with nav_language:
        lang_options = list(SUPPORTED_LANGUAGES.keys())
        current_label = next(
            (label for label, code in SUPPORTED_LANGUAGES.items() if code == _lang),
            lang_options[0],
        )
        selected_label = st.selectbox(
            get_string("lbl_language", _lang),
            options=lang_options,
            index=lang_options.index(current_label),
            key="lang_selector",
            label_visibility="visible",
        )
        selected_code = SUPPORTED_LANGUAGES[selected_label]
        st.session_state.selected_language = selected_code
        st.session_state.language = selected_code

    with nav_theme:
        theme_mode = st.selectbox(
            "Display mode",
            options=("System", "Light", "Dark"),
            index=("System", "Light", "Dark").index(
                st.session_state.get("theme_mode", "System")
            ),
            key="theme_mode_selector",
            label_visibility="collapsed",
        )
        st.session_state.theme_mode = theme_mode


_render_top_nav()

if st.button("☰ Navigation", key="navbar_navigation_toggle"):
    st.session_state.show_nav_menu = not st.session_state.show_nav_menu
    st.rerun()

if st.session_state.show_nav_menu:
    st.markdown(
        """
        <div class="navbar-menu-panel">
            <strong>Navigation</strong>
            <span>🌱 Ask for advice</span>
            <span>🗂 Conversation history</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Inject global CSS after the display mode is known. Streamlit reruns the
# script when the selector changes, so the theme updates without JavaScript.
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
if st.session_state.theme_mode == "Dark":
    st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)
elif st.session_state.theme_mode == "Light":
    st.markdown(LIGHT_MODE_CSS, unsafe_allow_html=True)


# ============================================================================
# T-20.5 — Auth gate: redirect unauthenticated users to login/register
# ============================================================================

if not is_authenticated():
    # Show a minimal branded header above the auth card
    st.markdown(
        f"""
        <div class="auth-hero">
                <h1>{APP_ICON} {get_string('app_title', st.session_state.get('selected_language', 'en'))}</h1>
                <p>{get_string('app_subtitle', st.session_state.get('selected_language', 'en'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_auth_screen()
    st.stop()


# ============================================================================
# Authenticated section — everything below is gated
# ============================================================================

# T-20.6 — surface token-expiry banner on re-entry
if token_just_expired():
    st.error(
        get_string("err_auth_expired", st.session_state.get(
            "selected_language", "en")),
        icon="🔒",
    )
    clear_auth()
    st.rerun()


# ============================================================================
# Input form
# ============================================================================

# T-17: resolve active language code for all form strings
_lang = st.session_state.get("selected_language", "en")

st.markdown(f"### 🌱 {get_string('app_subtitle', _lang)}")

# T-20.7: pre-populate district from the user's saved district (if set)
_saved_district = st.session_state.get("saved_district")
_default_district = _saved_district if _saved_district in DISTRICTS else "Anuradhapura"

with st.form(key="query_form", clear_on_submit=False):
    # Row 1: District + Crop context
    col_district, col_crop = st.columns(2)

    with col_district:
        district = st.selectbox(
            get_string("lbl_district", _lang),
            options=DISTRICTS,
            index=DISTRICTS.index(_default_district),
            help="Select the district where your farm is located.",
        )

    with col_crop:
        crop_raw = st.selectbox(
            get_string("lbl_crop", _lang),
            options=CROP_CONTEXTS,
            index=0,
            help="Select your crop to help the advisor give better advice.",
        )
        crop_context = None if crop_raw.startswith("—") else crop_raw

    # Row 2: Query text area
    query_text = st.text_area(
        get_string("lbl_query", _lang),
        placeholder=get_string("ph_query", _lang),
        max_chars=1000,
        height=130,
        help="Write in plain language. Maximum 1 000 characters.",
        key="query_input",
        label_visibility="visible",
    )

    # Soft character counter (shown only when approaching the limit)
    char_count = len(query_text)
    if char_count > 800:
        css_class = "error" if char_count >= 1000 else "warn"
        counter_label = get_string(
            "lbl_char_counter", _lang).format(count=char_count)
        st.markdown(
            f'<div class="char-counter {css_class}">{counter_label}</div>',
            unsafe_allow_html=True,
        )

    # Submit button (full width via CSS)
    submitted = st.form_submit_button(
        get_string("btn_submit", _lang),
        use_container_width=True,
        type="primary",
    )


# ============================================================================
# Form submission & API call
# ============================================================================

if submitted:
    # Client-side validation (T-17: localised error message)
    if not query_text.strip():
        st.error(get_string("err_empty_query", _lang))
        st.stop()

    # T-20.7: use the authenticated user_id; fall back gracefully
    auth_user_id = st.session_state.get(
        "user_id") or f"farmer_{uuid.uuid4().hex[:8]}"

    payload = build_payload(
        query=query_text.strip(),
        user_id=auth_user_id,                         # T-20.7: real user_id
        district=district,                            # T-20.7: may be saved district
        language=st.session_state.language,
        crop_context=crop_context,
        session_id=st.session_state.session_id,
    )

    progress = st.progress(0, text="Preparing your advisory request…")
    with st.spinner("🌿 Analysing your crop problem — this usually takes a few seconds…"):
        try:
            progress.progress(15, text="Contacting the advisory service…")
            response, is_fallback = call_orchestrator(
                payload,
                auth_headers=get_auth_headers(),      # T-20.4: JWT attached
            )
            progress.progress(100, text="Advisory ready")
            st.session_state.last_error = None

            # Persist session_id for multi-turn continuity
            session_id = response.get("metadata", {}).get("session_id")
            if session_id:
                st.session_state.session_id = session_id

            # Store result
            st.session_state.last_response = response
            st.session_state.last_is_fallback = is_fallback

            # Append to conversation history
            answer_full = response.get("answer", "")
            answer_summary = answer_full[:200].rstrip(
            ) + ("…" if len(answer_full) > 200 else "")
            st.session_state.conversation_history.append({
                "query":          query_text.strip(),
                "district":       district,
                "crop_context":   crop_context,
                "language":       st.session_state.language,
                "answer_summary": answer_summary,
                "session_id":     session_id,
            })
            save_history(
                auth_user_id,
                st.session_state.conversation_history,
            )

        except _ApiError as exc:
            progress.empty()
            st.session_state.last_response = None
            st.session_state.last_is_fallback = False
            st.session_state.last_error = (exc.status_code, exc.body)

            # T-20.6: token-expiry redirect
            if exc.status_code == 401:
                st.warning(
                    "⏱️ **Your session has expired.** You will be redirected to sign in.",
                    icon="🔒",
                )
                clear_auth()
                st.rerun()

        except Exception as exc:  # noqa: BLE001
            progress.empty()
            st.session_state.last_response = None
            st.session_state.last_is_fallback = False
            st.session_state.last_error = (0, {"detail": str(exc)})


# ============================================================================
# Conversation history
# ============================================================================

render_conversation_history(st.session_state.conversation_history)


# ============================================================================
# Advisory response / error
# ============================================================================

if st.session_state.last_error is not None:
    status_code, body = st.session_state.last_error
    render_error(status_code, body)

elif st.session_state.last_response is not None:
    # T-17.4: pass selected_language so the renderer can translate output
    _render_lang = st.session_state.get("selected_language", "en")
    st.markdown('<div class="advisory-container">', unsafe_allow_html=True)
    render_advisory_response(
        st.session_state.last_response,
        is_fallback=st.session_state.last_is_fallback,
        lang=_render_lang,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# Sidebar — session info + T-20.5 logout control
# ============================================================================

with st.sidebar:
    _slang = st.session_state.get("selected_language", "en")

    st.markdown("### Navigation")
    if is_authenticated():
        st.markdown("**🌱 Ask for advice**")
        st.caption("Your current advisory workspace")
    else:
        st.markdown("**🔐 Sign in or create an account**")
        st.caption("Start here to ask about your crops")
    st.markdown("---")

    # ── Authenticated user panel ──────────────────────────────────────────
    auth_user = st.session_state.get("user_id", "")
    saved_district = st.session_state.get("saved_district", "—")

    st.markdown(f"### {get_string('sidebar_heading', _slang)}")
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #F0FDF4, #DCFCE7);
            border: 1px solid #BBF7D0;
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 12px;
        ">
            <p style="margin:0;font-size:0.9rem;color:#166534;font-weight:600;">
                👤 {auth_user}
            </p>
            <p style="margin:4px 0 0 0;font-size:0.8rem;color:#4B5563;">
                📍 {saved_district}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.session_id:
        st.markdown(
            f"{get_string('lbl_session_id', _slang)} `{st.session_state.session_id}`")
    st.markdown(f"{get_string('lbl_language_code', _slang)} `{_slang}`")
    st.markdown(
        f"{get_string('lbl_turns', _slang)} {len(st.session_state.conversation_history)}")

    st.markdown("---")

    # Clear conversation
    if st.button(get_string("btn_clear", _slang), use_container_width=True, key="btn_clear_conv"):
        for key in ("conversation_history", "last_response", "last_is_fallback",
                    "last_error", "session_id"):
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.history_owner = st.session_state.get("user_id")
        save_history(st.session_state.get("user_id"), [])
        st.rerun()

    st.markdown("---")

    # T-20.5: Logout control
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button(get_string("btn_logout", _slang), use_container_width=True, key="btn_logout"):
        clear_auth()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.78rem;color:#6B7280;">Agri-Advisor v0.1.0<br>'
        'T-08 · T-17 · T-20 · UI Shell</p>',
        unsafe_allow_html=True,
    )
