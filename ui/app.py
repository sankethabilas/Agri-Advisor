"""
ui/app.py
Agri-Advisor — Streamlit UI Shell  (Task T-08 + T-17)

Entry point:
    streamlit run ui/app.py

Design spec:  /docs/ui-spec.md
API contract: /docs/api-contract.md
Backend:      POST http://localhost:8000/api/orchestrator/process  (T-06)

T-17 additions:
    - Language selector (en / si / ta) persisted in session_state["selected_language"]
    - All static UI strings sourced from utils.i18n.get_string()
    - Dynamic advisory output translated at render-time via advisory_renderer
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any

import streamlit as st

# Allow `ui.*` and `utils.*` imports when launched from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.api_client import _ApiError, build_payload, call_orchestrator
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
    LANGUAGES,
)
from ui.styles import GLOBAL_CSS

# T-17: i18n helpers
from utils.i18n import SUPPORTED_LANGUAGES, get_string

# ============================================================================
# Page configuration  (must be the very first Streamlit call)
# ============================================================================
st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_SUBTITLE}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get help":     "https://doa.gov.lk",
        "Report a bug": None,
        "About":        f"**{APP_TITLE}** · Smart Farming Assistant for Sri Lanka · v0.1.0",
    },
)

# Inject global CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ============================================================================
# Session-state initialisation
# ============================================================================

def _init_session() -> None:
    """Initialise all session-state keys on first load."""
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"farmer_{uuid.uuid4().hex[:8]}"
    if "session_id" not in st.session_state:
        st.session_state.session_id = None          # populated from first API response
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []  # list[dict]
    if "last_response" not in st.session_state:
        st.session_state.last_response = None
    if "last_is_fallback" not in st.session_state:
        st.session_state.last_is_fallback = False
    if "last_error" not in st.session_state:
        st.session_state.last_error = None          # tuple(status_code, body) | None
    if "language" not in st.session_state:
        st.session_state.language = "en"
    # T-17.1 — canonical session key for the selected locale code
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "en"


_init_session()


# ============================================================================
# Header
# ============================================================================

def _render_header() -> None:
    """
    Render the green gradient header with language selector.

    T-17.1 -- The selectbox persists the chosen locale code in
    both ``st.session_state.selected_language`` (T-17 canonical key)
    and ``st.session_state.language`` (legacy key used by the API payload).
    """
    header_col, lang_col = st.columns([4, 1])

    # Resolve current language for header tagline
    _lang = st.session_state.get("selected_language", "en")

    with header_col:
        tagline = get_string("app_tagline", _lang)
        st.markdown(
            f"""
            <div class="agri-header">
                <h1>{APP_ICON} {APP_TITLE}</h1>
                <p>{tagline}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with lang_col:
        st.markdown("<br><br>", unsafe_allow_html=True)

        # T-17.1: language selector -- options from SUPPORTED_LANGUAGES
        lang_options = list(SUPPORTED_LANGUAGES.keys())   # display labels
        # Find current index so the widget reflects session state on rerun
        current_code  = st.session_state.get("selected_language", "en")
        current_label = next(
            (lbl for lbl, code in SUPPORTED_LANGUAGES.items() if code == current_code),
            lang_options[0],
        )
        default_index = lang_options.index(current_label)

        selected_lang_label = st.selectbox(
            get_string("lbl_language", current_code),
            options=lang_options,
            index=default_index,
            key="lang_selector",
            label_visibility="visible",
        )
        selected_code = SUPPORTED_LANGUAGES[selected_lang_label]

        # Persist in BOTH keys for backward compatibility
        st.session_state.selected_language = selected_code  # T-17 canonical
        st.session_state.language          = selected_code  # legacy API payload key


_render_header()


# ============================================================================
# Input form
# ============================================================================

# T-17: resolve active language code for all form strings
_lang = st.session_state.get("selected_language", "en")

st.markdown(f"### 🌱 {get_string('app_subtitle', _lang)}")

with st.form(key="query_form", clear_on_submit=False):
    # Row 1: District + Crop context
    col_district, col_crop = st.columns(2)

    with col_district:
        district = st.selectbox(
            get_string("lbl_district", _lang),
            options=DISTRICTS,
            index=DISTRICTS.index("Anuradhapura"),
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
        counter_label = get_string("lbl_char_counter", _lang).format(count=char_count)
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

    payload = build_payload(
        query=query_text.strip(),
        user_id=st.session_state.user_id,
        district=district,
        language=st.session_state.language,
        crop_context=crop_context,
        session_id=st.session_state.session_id,
    )

    with st.spinner("🌿 Analysing your crop problem — this usually takes a few seconds…"):
        try:
            response, is_fallback = call_orchestrator(payload)
            st.session_state.last_error = None

            # Persist session_id for multi-turn continuity
            session_id = response.get("metadata", {}).get("session_id")
            if session_id:
                st.session_state.session_id = session_id

            # Store result
            st.session_state.last_response    = response
            st.session_state.last_is_fallback = is_fallback

            # Append to conversation history (store a short summary)
            answer_full = response.get("answer", "")
            # Take the first 200 chars as a summary preview
            answer_summary = answer_full[:200].rstrip() + ("…" if len(answer_full) > 200 else "")
            st.session_state.conversation_history.append({
                "query":          query_text.strip(),
                "district":       district,
                "crop_context":   crop_context,
                "language":       st.session_state.language,
                "answer_summary": answer_summary,
                "session_id":     session_id,
            })

        except _ApiError as exc:
            st.session_state.last_response    = None
            st.session_state.last_is_fallback = False
            st.session_state.last_error       = (exc.status_code, exc.body)

        except Exception as exc:  # noqa: BLE001
            st.session_state.last_response    = None
            st.session_state.last_is_fallback = False
            st.session_state.last_error       = (0, {"detail": str(exc)})


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
        lang=_render_lang,           # T-17: target locale for output translation
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# Sidebar — session info (debug / developer panel)
# ============================================================================

with st.sidebar:
    # T-17: localised sidebar labels
    _slang = st.session_state.get("selected_language", "en")

    st.markdown(f"### {get_string('sidebar_heading', _slang)}")
    st.markdown(f"{get_string('lbl_user_id', _slang)} `{st.session_state.user_id}`")
    if st.session_state.session_id:
        st.markdown(f"{get_string('lbl_session_id', _slang)} `{st.session_state.session_id}`")
    st.markdown(f"{get_string('lbl_language_code', _slang)} `{_slang}`")
    st.markdown(f"{get_string('lbl_turns', _slang)} {len(st.session_state.conversation_history)}")

    st.markdown("---")
    if st.button(get_string("btn_clear", _slang), use_container_width=True):
        for key in ("conversation_history", "last_response", "last_is_fallback",
                    "last_error", "session_id"):
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.78rem;color:#6B7280;">Agri-Advisor v0.1.0<br>'
        'T-08 · T-17 · UI Shell</p>',
        unsafe_allow_html=True,
    )
