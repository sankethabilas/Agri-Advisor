"""
ui/app.py
Agri-Advisor — Streamlit UI Shell  (Task T-08)

Entry point:
    streamlit run ui/app.py

Design spec:  /docs/ui-spec.md
API contract: /docs/api-contract.md
Backend:      POST http://localhost:8000/api/orchestrator/process  (T-06)
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any

import streamlit as st

# Allow `ui.*` imports when launched from the project root
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


_init_session()


# ============================================================================
# Header
# ============================================================================

def _render_header() -> None:
    """Render the green gradient header with language selector."""
    header_col, lang_col = st.columns([4, 1])

    with header_col:
        st.markdown(
            f"""
            <div class="agri-header">
                <h1>{APP_ICON} {APP_TITLE}</h1>
                <p>{APP_SUBTITLE} — Helping Sri Lankan farmers grow better crops</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with lang_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        selected_lang_label = st.selectbox(
            "🌐 Language",
            options=list(LANGUAGES.keys()),
            index=0,
            key="lang_selector",
            label_visibility="visible",
        )
        st.session_state.language = LANGUAGES[selected_lang_label]


_render_header()


# ============================================================================
# Input form
# ============================================================================

st.markdown("### 🌱 Ask Your Farming Question")

with st.form(key="query_form", clear_on_submit=False):
    # Row 1: District + Crop context
    col_district, col_crop = st.columns(2)

    with col_district:
        district = st.selectbox(
            "📍 Your District",
            options=DISTRICTS,
            index=DISTRICTS.index("Anuradhapura"),
            help="Select the district where your farm is located.",
        )

    with col_crop:
        crop_raw = st.selectbox(
            "🌾 Crop Type (optional)",
            options=CROP_CONTEXTS,
            index=0,
            help="Select your crop to help the advisor give better advice.",
        )
        crop_context = None if crop_raw.startswith("—") else crop_raw

    # Row 2: Query text area
    query_text = st.text_area(
        "Describe your crop problem",
        placeholder=(
            "e.g. My paddy has yellowing leaves with small brown spots. "
            "What disease is this and how should I treat it?"
        ),
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
        st.markdown(
            f'<div class="char-counter {css_class}">{char_count} / 1 000 characters</div>',
            unsafe_allow_html=True,
        )

    # Submit button (full width via CSS)
    submitted = st.form_submit_button(
        "🔍 Ask Agri-Advisor",
        use_container_width=True,
        type="primary",
    )


# ============================================================================
# Form submission & API call
# ============================================================================

if submitted:
    # Client-side validation
    if not query_text.strip():
        st.error("❌ Please describe your crop problem before submitting.")
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
    st.markdown('<div class="advisory-container">', unsafe_allow_html=True)
    render_advisory_response(
        st.session_state.last_response,
        is_fallback=st.session_state.last_is_fallback,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# Sidebar — session info (debug / developer panel)
# ============================================================================

with st.sidebar:
    st.markdown("### ⚙️ Session Info")
    st.markdown(f"**User ID:** `{st.session_state.user_id}`")
    if st.session_state.session_id:
        st.markdown(f"**Session ID:** `{st.session_state.session_id}`")
    st.markdown(f"**Language:** `{st.session_state.language}`")
    st.markdown(f"**Turns:** {len(st.session_state.conversation_history)}")

    st.markdown("---")
    if st.button("🗑 Clear conversation", use_container_width=True):
        for key in ("conversation_history", "last_response", "last_is_fallback",
                    "last_error", "session_id"):
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.78rem;color:#6B7280;">Agri-Advisor v0.1.0<br>'
        'T-08 · UI Shell</p>',
        unsafe_allow_html=True,
    )
