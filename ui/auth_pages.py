"""
ui/auth_pages.py
Agri-Advisor — T-20.1 / T-20.2: Registration and Login page renderers.

render_auth_screen()
    Entry point called by app.py when the user is not authenticated.
    Displays either the Login or Registration form based on
    st.session_state["auth_page"].

render_login_page()
    T-20.2: Login form with client-side validation.

render_register_page()
    T-20.1: Registration form (name, phone/email, password, district, language).
"""
from __future__ import annotations

import re

import streamlit as st

from ui.auth import (
    AuthError,
    call_login,
    call_register,
    store_token,
)
from ui.config import DISTRICTS, LANGUAGES
from utils.i18n import get_string


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_PASSWORD_LEN = 12
_USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@+-]{2,253}$")


def _auth_card_wrapper(content_fn, *args, **kwargs):
    """Wrap a form inside a centred glass-morphism auth card."""
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        content_fn(*args, **kwargs)
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# T-20.2 — Login page
# ---------------------------------------------------------------------------

def render_login_page() -> None:
    """Render the login form with client-side validation (T-20.2)."""
    lang = st.session_state.get("selected_language", "en")
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        # Header inside card
        st.markdown(
            """
            <div class="auth-card">
                <div class="auth-header-block">
                    <span class="auth-icon">🌾</span>
                    <h2 class="auth-title">{get_string('auth_login_title', lang)}</h2>
                    <p class="auth-subtitle">{get_string('auth_login_subtitle', lang)}</p>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # T-20.6: Expired token banner
        if st.session_state.get("token_expired"):
            st.error(
                get_string("err_auth_expired", lang),
                icon="🔒",
            )
            # Reset flag so it shows once
            st.session_state["token_expired"] = False

        with st.form(key="login_form", clear_on_submit=False):
            username = st.text_input(
                get_string("lbl_username", lang),
                placeholder=get_string("ph_username", lang),
                max_chars=254,
                key="login_username",
            )
            password = st.text_input(
                get_string("lbl_password", lang),
                type="password",
                placeholder=get_string("ph_password", lang),
                max_chars=128,
                key="login_password",
            )
            submitted = st.form_submit_button(
                get_string("btn_login", lang),
                use_container_width=True,
                type="primary",
            )

        if submitted:
            # ── Client-side validation ────────────────────────────────────
            errors: list[str] = []
            if not username.strip():
                errors.append("Username is required.")
            if not password:
                errors.append("Password is required.")

            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            else:
                # ── API call ──────────────────────────────────────────────
                with st.spinner("Signing in…"):
                    try:
                        data = call_login(username.strip(), password)
                        store_token(
                            token=data["access_token"],
                            user_id=data.get("user_id", username.strip()),
                        )
                        st.success("✅ Signed in successfully!")
                        st.rerun()
                    except AuthError as exc:
                        _render_auth_error(exc, lang)

        # ── Switch to register ────────────────────────────────────────────
        st.markdown(
            f'<p class="auth-switch-text">{get_string("auth_switch_new", lang)}</p>',
            unsafe_allow_html=True,
        )
        if st.button(
            get_string("btn_go_register", lang),
            key="go_to_register",
            use_container_width=True,
        ):
            st.session_state["auth_page"] = "register"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# T-20.1 — Registration page
# ---------------------------------------------------------------------------

def render_register_page() -> None:
    """
    Render the registration form (T-20.1).

    Fields:
        - Full name
        - Phone or email
        - Username
        - Password + confirm
        - District
        - Preferred language
    """
    lang = st.session_state.get("selected_language", "en")
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            """
            <div class="auth-card">
                <div class="auth-header-block">
                    <span class="auth-icon">🌱</span>
                    <h2 class="auth-title">{get_string('auth_register_title', lang)}</h2>
                    <p class="auth-subtitle">{get_string('auth_register_subtitle', lang)}</p>
                </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form(key="register_form", clear_on_submit=False):
            # ── Personal info ─────────────────────────────────────────────
            st.markdown(f"##### {get_string('lbl_personal_info', lang)}")
            full_name = st.text_input(
                get_string("lbl_full_name", lang),
                placeholder=get_string("ph_full_name", lang),
                max_chars=120,
                key="reg_full_name",
            )
            phone_or_email = st.text_input(
                get_string("lbl_phone_email", lang),
                placeholder=get_string("ph_phone_email", lang),
                max_chars=254,
                key="reg_phone_email",
            )

            st.markdown("---")

            # ── Account credentials ───────────────────────────────────────
            st.markdown(f"##### {get_string('lbl_account_creds', lang)}")
            st.info(
                get_string("info_register_username", lang),
                icon=None,
            )
            username = st.text_input(
                get_string("lbl_username", lang),
                placeholder=get_string("ph_username", lang),
                max_chars=254,
                key="reg_username",
            )

            st.info(
                get_string("info_register_password", lang),
                icon=None,
            )
            col_pw1, col_pw2 = st.columns(2)
            with col_pw1:
                password = st.text_input(
                    get_string("lbl_password", lang),
                    type="password",
                    placeholder=get_string("ph_password", lang),
                    max_chars=128,
                    key="reg_password",
                )
            with col_pw2:
                password_confirm = st.text_input(
                    get_string("lbl_confirm_password", lang),
                    type="password",
                    placeholder=get_string("ph_confirm_password", lang),
                    max_chars=128,
                    key="reg_password_confirm",
                )

            st.markdown("---")

            # ── Farming context ───────────────────────────────────────────
            st.markdown(f"##### {get_string('lbl_farming_context', lang)}")
            district = st.selectbox(
                get_string("lbl_district", lang),
                options=DISTRICTS,
                index=DISTRICTS.index("Anuradhapura"),
                help="Select the district where your farm is located.",
                key="reg_district",
            )

            lang_options = list(LANGUAGES.keys())
            preferred_language = st.selectbox(
                get_string("lbl_preferred_language", lang),
                options=lang_options,
                index=0,
                help="The language in which you'd like to receive advice.",
                key="reg_language",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                get_string("btn_register", lang),
                use_container_width=True,
                type="primary",
            )

        if submitted:
            errors = _validate_registration(
                full_name=full_name,
                phone_or_email=phone_or_email,
                username=username,
                password=password,
                password_confirm=password_confirm,
            )
            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            else:
                with st.spinner("Creating your account…"):
                    try:
                        call_register(username.strip(), password)
                        # Auto-login after successful registration
                        login_data = call_login(username.strip(), password)
                        store_token(
                            token=login_data["access_token"],
                            user_id=login_data.get("user_id", username.strip()),
                            district=district,
                        )
                        # Also save preferred language
                        lang_code = LANGUAGES.get(preferred_language, "en")
                        st.session_state["selected_language"] = lang_code
                        st.session_state["language"] = lang_code

                        st.success(
                            f"✅ Account created! Welcome, **{full_name or username.strip()}**!"
                        )
                        st.rerun()
                    except AuthError as exc:
                        _render_auth_error(exc, lang)

        # ── Switch to login ───────────────────────────────────────────────
        st.markdown(
            f'<p class="auth-switch-text">{get_string("auth_switch_have_account", lang)}</p>',
            unsafe_allow_html=True,
        )
        if st.button(
            get_string("btn_go_login", lang),
            key="go_to_login",
            use_container_width=True,
        ):
            st.session_state["auth_page"] = "login"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_registration(
    full_name: str,
    phone_or_email: str,
    username: str,
    password: str,
    password_confirm: str,
) -> list[str]:
    """
    Client-side registration validation.

    Returns:
        List of human-readable error strings (empty = valid).
    """
    errors: list[str] = []

    if not full_name.strip():
        errors.append("Full name is required.")

    if not phone_or_email.strip():
        errors.append("Phone number or email is required.")

    if not username.strip():
        errors.append("Username is required.")
    elif not _USERNAME_RE.match(username.strip()):
        errors.append(
            "Username must be 3–254 characters and contain only letters, digits, "
            "'.', '_', '@', '+', '-'. It must start with a letter or digit."
        )

    if not password:
        errors.append("Password is required.")
    elif len(password) < _MIN_PASSWORD_LEN:
        errors.append(f"Password must be at least {_MIN_PASSWORD_LEN} characters long.")

    if password and password != password_confirm:
        errors.append("Passwords do not match. Please re-enter.")

    return errors


# ---------------------------------------------------------------------------
# T-20.6 — Friendly error display
# ---------------------------------------------------------------------------

def _render_auth_error(exc: AuthError, lang: str = "en") -> None:
    """
    Display a friendly, farmer-facing error message for auth failures.

    Maps HTTP status codes to plain-language explanations (T-20.6).
    """
    friendly: dict[int, str] = {
        401: get_string("err_auth_invalid", lang),
        403: "❌ **Access denied.** Your account may be suspended.",
        409: get_string("err_auth_duplicate", lang),
        422: "❌ **Please check your details.** Make sure your username and "
             "password meet the requirements listed above.",
        429: get_string("err_auth_rate_limit", lang),
        500: get_string("err_auth_server", lang),
        0:   get_string("err_auth_network", lang),
    }
    message = friendly.get(
        exc.status_code,
        f"❌ **Sign-in failed (code {exc.status_code}).** {exc.message}",
    )
    st.error(message)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render_auth_screen() -> None:
    """
    Top-level auth screen dispatcher.

    Called by app.py when is_authenticated() returns False.
    Routes to login or register based on session_state["auth_page"].
    """
    page = st.session_state.get("auth_page", "login")
    if page == "register":
        render_register_page()
    else:
        render_login_page()
