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
from typing import Any

import streamlit as st

from ui.auth import (
    AuthError,
    call_login,
    call_register,
    store_token,
)
from ui.config import DISTRICTS, LANGUAGES, get_app_icon_base64


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
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        logo_b64 = get_app_icon_base64()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 56px; height: 56px; object-fit: contain; border-radius: 12px; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);" alt="Logo" />' if logo_b64 else '<span class="auth-icon">🌾</span>'
        # Header inside card
        st.markdown(
            f"""
            <div class="auth-card">
                <div class="auth-header-block">
                    {logo_html}
                    <h2 class="auth-title">Welcome Back</h2>
                    <p class="auth-subtitle">Sign in to your Agri-Advisor account</p>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # T-20.6: Expired token banner
        if st.session_state.get("token_expired"):
            st.error(
                "⏱️ **Your session has expired.** Please sign in again to continue.",
                icon="🔒",
            )
            # Reset flag so it shows once
            st.session_state["token_expired"] = False

        with st.form(key="login_form", clear_on_submit=False):
            username = st.text_input(
                "👤 Username",
                placeholder="Enter your username",
                max_chars=254,
                key="login_username",
            )
            password = st.text_input(
                "🔑 Password",
                type="password",
                placeholder="Enter your password",
                max_chars=128,
                key="login_password",
            )
            submitted = st.form_submit_button(
                "🔓 Sign In",
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
                        _render_auth_error(exc)

        # ── Switch to register ────────────────────────────────────────────
        st.markdown(
            '<p class="auth-switch-text">New to Agri-Advisor?</p>',
            unsafe_allow_html=True,
        )
        if st.button(
            "✏️ Create an account",
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
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        logo_b64 = get_app_icon_base64()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 56px; height: 56px; object-fit: contain; border-radius: 12px; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);" alt="Logo" />' if logo_b64 else '<span class="auth-icon">🌱</span>'
        st.markdown(
            f"""
            <div class="auth-card">
                <div class="auth-header-block">
                    {logo_html}
                    <h2 class="auth-title">Create Your Account</h2>
                    <p class="auth-subtitle">Join thousands of Sri Lankan farmers</p>
                </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form(key="register_form", clear_on_submit=False):
            # ── Personal info ─────────────────────────────────────────────
            st.markdown("##### 👤 Personal Information")
            full_name = st.text_input(
                "Full Name",
                placeholder="e.g. Saman Perera",
                max_chars=120,
                key="reg_full_name",
            )
            phone_or_email = st.text_input(
                "Phone Number or Email",
                placeholder="e.g. 0771234567 or saman@example.com",
                max_chars=254,
                key="reg_phone_email",
            )

            st.markdown("---")

            # ── Account credentials ───────────────────────────────────────
            st.markdown("##### 🔐 Account Credentials")
            st.info(
                "ℹ️ **Username rules:** 3–254 characters, letters, digits, "
                "`.`, `_`, `@`, `+`, `-` only. Must start with a letter or digit.",
                icon=None,
            )
            username = st.text_input(
                "Username",
                placeholder="e.g. saman_farmer",
                max_chars=254,
                key="reg_username",
            )

            st.info(
                "ℹ️ **Password rules:** Minimum 12 characters.",
                icon=None,
            )
            col_pw1, col_pw2 = st.columns(2)
            with col_pw1:
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Min. 12 characters",
                    max_chars=128,
                    key="reg_password",
                )
            with col_pw2:
                password_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Repeat your password",
                    max_chars=128,
                    key="reg_password_confirm",
                )

            st.markdown("---")

            # ── Farming context ───────────────────────────────────────────
            st.markdown("##### 🌾 Farming Context")
            district = st.selectbox(
                "📍 Your District",
                options=DISTRICTS,
                index=DISTRICTS.index("Anuradhapura"),
                help="Select the district where your farm is located.",
                key="reg_district",
            )

            lang_options = list(LANGUAGES.keys())
            preferred_language = st.selectbox(
                "🌐 Preferred Language",
                options=lang_options,
                index=0,
                help="The language in which you'd like to receive advice.",
                key="reg_language",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "🌱 Create Account",
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
                        _render_auth_error(exc)

        # ── Switch to login ───────────────────────────────────────────────
        st.markdown(
            '<p class="auth-switch-text">Already have an account?</p>',
            unsafe_allow_html=True,
        )
        if st.button(
            "🔓 Sign In",
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

def _render_auth_error(exc: AuthError) -> None:
    """
    Display a friendly, farmer-facing error message for auth failures.

    Maps HTTP status codes to plain-language explanations (T-20.6).
    """
    friendly: dict[int, str] = {
        401: "❌ **Incorrect username or password.** Please check and try again.",
        403: "❌ **Access denied.** Your account may be suspended.",
        409: "❌ **An account with that username already exists.** "
             "Please choose a different username or sign in.",
        422: "❌ **Please check your details.** Make sure your username and "
             "password meet the requirements listed above.",
        429: "❌ **Too many attempts.** Please wait a moment before trying again.",
        500: "❌ **Something went wrong on our end.** Please try again shortly.",
        0:   f"❌ **Connection problem.** {exc.message}",
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
