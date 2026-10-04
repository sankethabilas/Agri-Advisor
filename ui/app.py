"""
ui/app.py
Agri-Advisor — Streamlit UI Shell  (Task T-08 + T-17 + T-20 + T-21)

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
    - Logout control  (T-20.5)  -> now lives in the top navigation bar
    - Friendly error messages for invalid credentials / expired tokens  (T-20.6)
    - Authenticated user_id and saved district in query payload  (T-20.7)

T-21 additions (navigation / layout refresh):
    - Fixed top navigation bar:
        left  : sidebar toggle (☰) + logo + "Agri Advisor"
        right : profile avatar + Log Out button (authenticated users only)
    - Single sidebar (one source of truth):
        Navigation links (Crop Management, Market Prices, Weather Updates,
        Community Forum) -> Display Mode -> Session panel -> Language (bottom)
    - The ☰ button drives st.session_state["show_nav_menu"], which shows /
      hides the sidebar.  No duplicate "Navigation" buttons in the page body.
    - Dark-green header banner + central welcome card on the home page.
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

import base64
import html
import re
import sys
import uuid
from pathlib import Path

# Make project-local packages importable when Streamlit launches this file
# directly (for example: `streamlit run ui/app.py`).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Optional branding assets.  If a file below exists it is used, otherwise the
# built-in fallback (APP_ICON emoji / inline SVG illustration) is rendered.
ASSETS_DIR = Path(__file__).resolve().parent / "assets"


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
# Constants
# ============================================================================

THEME_OPTIONS = ("System", "Light", "Dark")

# (page id, i18n key, English fallback label, material icon)
NAV_ITEMS = (
    ("crop",    "nav_crop_management", "Crop Management", ":material/eco:"),
    ("market",  "nav_market_prices",   "Market Prices",   ":material/trending_up:"),
    ("weather", "nav_weather_updates", "Weather Updates", ":material/partly_cloudy_day:"),
    ("forum",   "nav_community_forum", "Community Forum", ":material/forum:"),
)

# ============================================================================
# Session-state initialisation
# ============================================================================


def _init_session() -> None:
    """Initialise all session-state keys on first load (T-08 + T-17 + T-20 + T-21)."""
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

    # T-21: sidebar is open by default; ☰ in the top bar flips this flag
    if "show_nav_menu" not in st.session_state:
        st.session_state.show_nav_menu = True
    if "active_page" not in st.session_state:
        st.session_state.active_page = "crop"

    user_id = st.session_state.get("user_id")
    if user_id and st.session_state.get("history_owner") != user_id:
        st.session_state.conversation_history = load_history(user_id)
        st.session_state.history_owner = user_id


def _sync_widget_state() -> None:
    """
    Copy the latest sidebar widget values into the canonical session keys
    *before* anything is rendered.  The sidebar widgets are rendered after the
    top bar, so without this step the top bar would lag one rerun behind when
    the language or display mode is changed.
    """
    lang_label = st.session_state.get("lang_selector")
    if lang_label in SUPPORTED_LANGUAGES:
        code = SUPPORTED_LANGUAGES[lang_label]
        st.session_state.selected_language = code
        st.session_state.language = code

    mode = st.session_state.get("theme_mode_selector")
    if mode in THEME_OPTIONS:
        st.session_state.theme_mode = mode


_init_session()
_sync_widget_state()


# ============================================================================
# Small helpers
# ============================================================================

def _s(key: str, lang: str, default: str) -> str:
    """get_string() with a safe English fallback for keys not yet in i18n."""
    try:
        value = get_string(key, lang)
    except Exception:  # noqa: BLE001
        return default
    return value if value and value != key else default


def _asset_data_uri(*names: str) -> str | None:
    """Return a data: URI for the first existing file in ui/assets/, else None."""
    mime = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".svg": "image/svg+xml",
    }
    for name in names:
        path = ASSETS_DIR / name
        if path.is_file() and path.suffix.lower() in mime:
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:{mime[path.suffix.lower()]};base64,{encoded}"
    return None


def _initials(user_id: str) -> str:
    letters = re.sub(r"[^A-Za-z0-9]", "", user_id or "")
    return (letters[:2] or "U").upper()


# Built-in welcome illustration (used when ui/assets/welcome_illustration.* is absent)
_WELCOME_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 250" fill="none" stroke-linecap="round" stroke-linejoin="round">
<circle cx="150" cy="150" r="88" fill="#E6F4EA"/>
<g stroke="#1F3D2B" stroke-width="2.4">
<circle cx="150" cy="26" r="9" fill="#FDE68A" stroke="#C99A12"/>
<path d="M150 8v6M150 38v6M132 26h6M162 26h6M137 13l4 4M159 35l4 4M163 13l-4 4M141 35l-4 4" stroke="#C99A12"/>
<path d="M70 38h30M78 32h14" /><path d="M205 30h34M214 24h16"/>
<path d="M12 98Q80 70 150 92T290 80"/><path d="M12 116Q90 88 160 110T290 100"/>
<path d="M12 134Q100 108 170 128T290 120"/>
<path d="M205 70v-18l20-12 20 12v18z" fill="#fff"/><path d="M215 70V58h20v12"/>
<path d="M60 82v-24M60 66l-8-8M60 72l8-8" stroke="#2E7D4F"/>
<path d="M82 84V60M82 70l-7-7M82 76l7-7" stroke="#2E7D4F"/>
<path d="M104 86V66M104 74l-6-6M104 80l6-6" stroke="#2E7D4F"/>
<rect x="112" y="118" width="86" height="112" rx="8" fill="#fff"/>
<path d="M124 190V170M138 190V158M152 190V148M166 190V164" stroke="#E0A526" stroke-width="7"/>
<path d="M124 150l16-14 14 8 28-22" stroke="#2E7D4F"/>
<path d="M124 205h62M124 216h40" stroke="#9CA3AF" stroke-width="2"/>
</g>
<circle cx="214" cy="140" r="19" fill="#FBBF24" stroke="#1F3D2B" stroke-width="2.4"/>
<text x="214" y="148" text-anchor="middle" font-family="Arial,sans-serif" font-size="22" font-weight="700" fill="#1F3D2B">$</text>
<g fill="#FBBF24" stroke="#1F3D2B" stroke-width="2.2">
<ellipse cx="226" cy="226" rx="26" ry="8"/><ellipse cx="226" cy="214" rx="26" ry="8"/><ellipse cx="226" cy="202" rx="26" ry="8"/>
</g>
<g fill="#4CAF72" stroke="#1F3D2B" stroke-width="2.2">
<path d="M62 232V170"/><path d="M62 200q-26-4-30-30 26 2 30 30z"/><path d="M62 184q24-2 30-26-26-2-30 26z"/>
<path d="M62 218q-22 0-28-20 22 0 28 20z"/>
</g>
<g fill="#4CAF72" stroke="#1F3D2B" stroke-width="2.2">
<path d="M262 232v-34"/><path d="M262 214q-18-2-22-20 18 0 22 20z"/><path d="M262 204q18-2 22-20-18 0-22 20z"/>
</g>
</svg>"""


def _welcome_illustration_uri() -> str:
    uri = _asset_data_uri(
        "welcome_illustration.svg", "welcome_illustration.png",
        "welcome_illustration.jpg", "welcome_illustration.webp",
    )
    if uri:
        return uri
    return "data:image/svg+xml;base64," + base64.b64encode(
        _WELCOME_SVG.encode("utf-8")
    ).decode("ascii")


def _logo_html(css_class: str = "aa-logo") -> str:
    """Brand mark: ui/assets/logo.* when present, otherwise APP_ICON."""
    uri = _asset_data_uri("logo.svg", "logo.png", "logo.webp", "logo.jpg")
    if uri:
        return f'<img class="{css_class}" src="{uri}" alt="logo"/>'
    return f'<span class="topnav-mark">{html.escape(str(APP_ICON))}</span>'


# ============================================================================
# Shell CSS  (top bar + sidebar + banner + welcome card)
#   Injected AFTER GLOBAL_CSS / theme CSS so these layout rules win.
# ============================================================================

_LIGHT_VARS = (
    "--aa-bg:#F6FAF7;--aa-nav-bg:#EEFBF1;--aa-side-bg:#EEFBF1;--aa-card:#FFFFFF;"
    "--aa-text:#1F2937;--aa-muted:#6B7280;--aa-border:#D5EADB;"
    "--aa-active:#D6F0DD;--aa-hover:#E1F5E7;--aa-avatar-ring:#FFFFFF;"
)
_DARK_VARS = (
    "--aa-bg:#0E1712;--aa-nav-bg:#12201A;--aa-side-bg:#12201A;--aa-card:#182A21;"
    "--aa-text:#E7F1EA;--aa-muted:#9DB3A5;--aa-border:#25402F;"
    "--aa-active:#1F3A2B;--aa-hover:#1A3024;--aa-avatar-ring:#25402F;"
)

_SHELL_CSS = """
<style>
:root{--aa-nav-h:64px;--aa-side-w:300px;}
__THEME_VARS__

/* ---- Streamlit chrome we replace ------------------------------------- */
header[data-testid="stHeader"]{display:none !important;}
[data-testid="stSidebarHeader"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stExpandSidebarButton"]{display:none !important;}
.stApp{background:var(--aa-bg) !important;}
.block-container,[data-testid="stMainBlockContainer"]{
    padding-top:calc(var(--aa-nav-h) + 1.75rem) !important;}

/* ---- Top navigation bar ---------------------------------------------- */
div[data-testid="stHorizontalBlock"]:has(.topnav-brand){
    position:fixed;top:0;left:0;right:0;width:100% !important;
    height:var(--aa-nav-h);z-index:1000;margin:0;padding:0 1.25rem;
    display:flex;flex-wrap:nowrap !important;align-items:center;gap:.5rem !important;
    background:var(--aa-nav-bg);border-bottom:1px solid var(--aa-border);
    box-shadow:0 1px 6px rgba(20,83,45,.08);}
div[data-testid="stHorizontalBlock"]:has(.topnav-brand) > div{
    flex:0 0 auto !important;width:auto !important;min-width:0 !important;}
div[data-testid="stHorizontalBlock"]:has(.topnav-brand) > div:has(.topnav-brand){
    flex:1 1 auto !important;}
.topnav-brand{display:flex;align-items:center;gap:.6rem;color:var(--aa-text);
    font-size:1.2rem;font-weight:700;white-space:nowrap;}
.topnav-mark{font-size:1.6rem;line-height:1;}
.aa-logo{height:34px;width:auto;}
.topnav-avatar{width:40px;height:40px;border-radius:50%;overflow:hidden;
    display:flex;align-items:center;justify-content:center;
    background:#16A34A;color:#fff;font-weight:700;font-size:.95rem;
    border:2px solid var(--aa-avatar-ring);box-shadow:0 1px 4px rgba(0,0,0,.2);}
.topnav-avatar img{width:100%;height:100%;object-fit:cover;}
/* ☰ toggle (first column) */
div[data-testid="stHorizontalBlock"]:has(.topnav-brand) > div:first-child button{
    background:transparent !important;border:none !important;box-shadow:none !important;
    color:var(--aa-text) !important;font-size:1.6rem !important;line-height:1 !important;
    padding:.25rem .65rem !important;min-height:0 !important;}
div[data-testid="stHorizontalBlock"]:has(.topnav-brand) > div:first-child button:hover{
    background:var(--aa-hover) !important;}
/* Log Out (last column, authenticated only) */
div[data-testid="stHorizontalBlock"]:has(.topnav-brand) > div:last-child button{
    background:var(--aa-card) !important;color:var(--aa-text) !important;
    border:1px solid var(--aa-text) !important;border-radius:8px !important;
    padding:.35rem 1.1rem !important;font-weight:500 !important;box-shadow:none !important;}
div[data-testid="stHorizontalBlock"]:has(.topnav-brand) > div:last-child button:hover{
    background:var(--aa-hover) !important;}
div[data-testid="stHorizontalBlock"]:has(.topnav-brand) > div:first-child:last-child button{
    border:none !important;}

/* ---- Sidebar ---------------------------------------------------------- */
section[data-testid="stSidebar"]{
    position:fixed !important;top:var(--aa-nav-h) !important;left:0 !important;bottom:0 !important;
    height:auto !important;width:var(--aa-side-w) !important;min-width:var(--aa-side-w) !important;
    max-width:var(--aa-side-w) !important;transform:none !important;margin-left:0 !important;
    visibility:visible !important;z-index:900 !important;
    background:var(--aa-side-bg) !important;border-right:1px solid var(--aa-border);}
section[data-testid="stSidebar"] > div{width:100% !important;height:100% !important;}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding-top:.5rem;}
section[data-testid="stSidebar"] label p,
section[data-testid="stSidebar"] .side-heading{color:var(--aa-text);}
.side-heading{font-weight:700;font-size:1rem;margin:.4rem 0 .3rem 0;}
.side-hint{font-size:.85rem;color:var(--aa-muted);margin-bottom:.6rem;}
/* navigation links */
[class*="st-key-nav_"] button{
    justify-content:flex-start !important;text-align:left !important;width:100% !important;
    background:transparent !important;border:none !important;box-shadow:none !important;
    color:var(--aa-text) !important;font-weight:500 !important;border-radius:8px !important;
    padding:.45rem .6rem !important;}
[class*="st-key-nav_"] button:hover{background:var(--aa-hover) !important;}
[class*="st-key-nav_"] button[kind="primary"],
[class*="st-key-nav_"] [data-testid="stBaseButton-primary"]{
    background:var(--aa-active) !important;font-weight:700 !important;}

/* ---- Main area offset (sidebar is fixed, so push the content) --------- */
__SIDEBAR_RULES__

/* ---- Header banner + welcome card ------------------------------------ */
.aa-hero{max-width:820px;margin:0 auto 1.6rem auto;padding:2.4rem 1rem;border-radius:12px;
    background:linear-gradient(135deg,#14532D 0%,#15803D 100%);color:#fff;
    display:flex;justify-content:center;align-items:center;gap:.6rem;
    font-size:1.55rem;font-weight:700;box-shadow:0 6px 18px rgba(20,83,45,.25);}
.aa-hero .aa-logo{height:30px;}
.aa-welcome{max-width:430px;margin:0 auto 1.8rem auto;padding:2rem 1.6rem;text-align:center;
    background:var(--aa-card);border:1px solid var(--aa-border);border-radius:22px;
    box-shadow:0 8px 24px rgba(0,0,0,.07);}
.aa-welcome img{width:100%;max-width:260px;height:auto;}
.aa-welcome-title{margin:.8rem 0 .4rem 0;font-size:1.65rem;font-weight:800;color:var(--aa-text);}
.aa-welcome-text{margin:0;color:var(--aa-muted);font-size:.98rem;line-height:1.55;}

@media (max-width: 768px){
    section[data-testid="stSidebar"]{width:min(var(--aa-side-w),88vw) !important;
        min-width:0 !important;box-shadow:4px 0 18px rgba(0,0,0,.18);}
    [data-testid="stMain"],section.main{padding-left:0 !important;}
    .topnav-brand{font-size:1.05rem;}
}
</style>
"""

_SIDEBAR_OPEN_RULES = """
section[data-testid="stSidebar"]{display:flex !important;}
[data-testid="stMain"],section.main{padding-left:var(--aa-side-w);}
"""
_SIDEBAR_CLOSED_RULES = """
section[data-testid="stSidebar"]{display:none !important;}
[data-testid="stMain"],section.main{padding-left:0;}
"""


def _shell_css(theme_mode: str, sidebar_open: bool) -> str:
    """Build the shell CSS for the active display mode and sidebar state."""
    if theme_mode == "Dark":
        theme_vars = f":root{{{_DARK_VARS}}}"
    elif theme_mode == "Light":
        theme_vars = f":root{{{_LIGHT_VARS}}}"
    else:  # System -> follow the OS preference
        theme_vars = (
            f":root{{{_LIGHT_VARS}}}"
            f"@media (prefers-color-scheme: dark){{:root{{{_DARK_VARS}}}}}"
        )
    side_rules = _SIDEBAR_OPEN_RULES if sidebar_open else _SIDEBAR_CLOSED_RULES
    return (
        _SHELL_CSS
        .replace("__THEME_VARS__", theme_vars)
        .replace("__SIDEBAR_RULES__", side_rules)
    )


# ============================================================================
# Navigation callbacks
# ============================================================================

def toggle_navigation() -> None:
    """☰ handler: show / hide the sidebar (stored in session state)."""
    st.session_state.show_nav_menu = not st.session_state.get("show_nav_menu", True)


def _set_page(page_id: str) -> None:
    """Sidebar link handler: switch the active page."""
    st.session_state.active_page = page_id


# ============================================================================
# Top navigation bar
# ============================================================================

def _render_top_nav() -> None:
    """
    Fixed top bar.
      left  : ☰ sidebar toggle · logo · application title
      right : profile avatar · Log Out   (only when signed in)
    """
    _lang = st.session_state.get("selected_language", "en")
    authed = is_authenticated()

    if authed:
        c_toggle, c_brand, c_avatar, c_logout = st.columns(
            [1, 1, 1, 1], vertical_alignment="center"
        )
    else:
        c_toggle, c_brand = st.columns([1, 1], vertical_alignment="center")

    with c_toggle:
        st.button(
            "☰",
            key="topnav_sidebar_toggle",
            on_click=toggle_navigation,
            help="Show / hide the sidebar",
        )

    with c_brand:
        tagline = html.escape(get_string("app_tagline", _lang))
        st.markdown(
            f'<div class="topnav-brand" title="{tagline}">'
            f'{_logo_html()}<span>{html.escape(get_string("app_title", _lang))}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    if authed:
        user_id = str(st.session_state.get("user_id") or "")
        with c_avatar:
            avatar_src = st.session_state.get("profile_image")  # URL or data URI
            if avatar_src:
                inner = f'<img src="{html.escape(str(avatar_src), quote=True)}" alt="profile"/>'
            else:
                inner = html.escape(_initials(user_id))
            st.markdown(
                f'<div class="topnav-avatar" title="{html.escape(user_id)}">{inner}</div>',
                unsafe_allow_html=True,
            )
        with c_logout:
            # T-20.5: logout control (moved here from the sidebar)
            if st.button(get_string("btn_logout", _lang), key="btn_logout"):
                clear_auth()
                st.rerun()


# ============================================================================
# Sidebar  (always rendered; CSS shows / hides it from the ☰ state)
# ============================================================================

def _render_sidebar():
    """
    Sidebar order:  Navigation -> Display Mode -> Session panel slot -> Language.
    Returns the container that _fill_session_slot() populates at the end of the
    run (so session info is always fresh).
    """
    _lang = st.session_state.get("selected_language", "en")
    active = st.session_state.get("active_page", "crop")

    with st.sidebar:
        st.markdown(
            f'<div class="side-heading">{html.escape(_s("nav_heading", _lang, "Navigation"))}</div>',
            unsafe_allow_html=True,
        )
        if is_authenticated():
            for page_id, key, default, icon in NAV_ITEMS:
                st.button(
                    _s(key, _lang, default),
                    key=f"nav_{page_id}",
                    icon=icon,
                    type="primary" if page_id == active else "secondary",
                    use_container_width=True,
                    on_click=_set_page,
                    args=(page_id,),
                )
        else:
            st.markdown("**🔐 Sign in or create an account**")
            st.markdown(
                '<div class="side-hint">Start here to ask about your crops</div>',
                unsafe_allow_html=True,
            )

        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.selectbox(
            _s("lbl_display_mode", _lang, "Display Mode"),
            options=THEME_OPTIONS,
            index=THEME_OPTIONS.index(st.session_state.get("theme_mode", "System")),
            key="theme_mode_selector",
            help="Choose Light or Dark, or follow your device setting.",
        )

        # Session info + clear-conversation are filled in at the end of the run
        session_slot = st.container()

        # Language selector — bottom of the sidebar
        lang_options = list(SUPPORTED_LANGUAGES.keys())
        current_label = next(
            (label for label, code in SUPPORTED_LANGUAGES.items() if code == _lang),
            lang_options[0],
        )
        st.selectbox(
            "🌐 " + get_string("lbl_language", _lang),
            options=lang_options,
            index=lang_options.index(current_label),
            key="lang_selector",
        )
    return session_slot


def _fill_session_slot(slot) -> None:
    """Session panel + clear-conversation button (T-08 / T-17 / T-20.7)."""
    if not is_authenticated():
        return
    _slang = st.session_state.get("selected_language", "en")

    with slot:
        with st.expander(get_string("sidebar_heading", _slang), expanded=False):
            auth_user = html.escape(str(st.session_state.get("user_id", "")))
            saved_district = html.escape(str(st.session_state.get("saved_district", "—")))
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

            # Clear conversation
            if st.button(get_string("btn_clear", _slang), use_container_width=True, key="btn_clear_conv"):
                for key in ("conversation_history", "last_response", "last_is_fallback",
                            "last_error", "session_id"):
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.history_owner = st.session_state.get("user_id")
                save_history(st.session_state.get("user_id"), [])
                st.rerun()

            st.markdown(
                '<p style="font-size:0.78rem;color:#6B7280;">Agri-Advisor v0.1.0<br>'
                'T-08 · T-17 · T-20 · T-21 · UI Shell</p>',
                unsafe_allow_html=True,
            )


# ============================================================================
# Main-area building blocks
# ============================================================================

def _render_banner() -> None:
    """Dark-green header banner with the brand name."""
    _lang = st.session_state.get("selected_language", "en")
    st.markdown(
        f'<div class="aa-hero">{_logo_html()}'
        f'<span>{html.escape(get_string("app_title", _lang))}</span></div>',
        unsafe_allow_html=True,
    )


def _render_welcome_card(
    title: str | None = None, body: str | None = None
) -> None:
    """Central welcome card: illustration + welcome text."""
    _lang = st.session_state.get("selected_language", "en")
    app_name = get_string("app_title", _lang)
    title = title or _s("welcome_title", _lang, f"Welcome to {app_name}")
    body = body or _s(
        "welcome_body", _lang,
        "Describe a crop problem below and get a diagnosis, treatment steps "
        "and weather-aware advice for your district.",
    )
    st.markdown(
        f'<div class="aa-welcome">'
        f'<img src="{_welcome_illustration_uri()}" alt="Agri Advisor illustration"/>'
        f'<div class="aa-welcome-title">{html.escape(title)}</div>'
        f'<p class="aa-welcome-text">{html.escape(body)}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_placeholder_page(page_id: str) -> None:
    """Landing card for sections that are not built yet (Market / Weather / Forum)."""
    _lang = st.session_state.get("selected_language", "en")
    for pid, key, default, _icon in NAV_ITEMS:
        if pid == page_id:
            label = _s(key, _lang, default)
            break
    else:
        label = page_id.title()
    _render_welcome_card(
        title=label,
        body=_s("coming_soon", _lang,
                "This section is coming soon. Use Crop Management to get advisory now."),
    )


# ============================================================================
# Page shell: CSS -> top bar -> sidebar
# ============================================================================

# Inject global CSS after the display mode is known. Streamlit reruns the
# script when the selector changes, so the theme updates without JavaScript.
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
if st.session_state.theme_mode == "Dark":
    st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)
elif st.session_state.theme_mode == "Light":
    st.markdown(LIGHT_MODE_CSS, unsafe_allow_html=True)
st.markdown(
    _shell_css(
        st.session_state.theme_mode,
        bool(st.session_state.get("show_nav_menu", True)),
    ),
    unsafe_allow_html=True,
)

_render_top_nav()
_session_slot = _render_sidebar()


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

# T-17: resolve active language code for all form strings
_lang = st.session_state.get("selected_language", "en")

# T-21: header banner on every page
_render_banner()

# T-21: non-advisory sections get a placeholder card
if st.session_state.get("active_page", "crop") != "crop":
    _render_placeholder_page(st.session_state.active_page)
    _fill_session_slot(_session_slot)
    st.stop()

# T-21: welcome card on the home page until the first advisory is requested
if (
    not st.session_state.conversation_history
    and st.session_state.last_response is None
    and st.session_state.last_error is None
):
    _render_welcome_card()


# ============================================================================
# Input form
# ============================================================================

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
        _fill_session_slot(_session_slot)
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
# Sidebar — session info (filled last so it reflects this run's results)
# ============================================================================

_fill_session_slot(_session_slot)
