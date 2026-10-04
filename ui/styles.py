"""
ui/styles.py
Custom CSS injected into the Streamlit app for the Agri-Advisor design system.

Design goals (from /docs/ui-spec.md §5):
  - Base font size ≥ 16 px
  - High contrast (outdoor phone use)
  - Minimal, clean layout
  - No technical jargon in visible text
"""

GLOBAL_CSS = """
<style>
/* ── Google Font ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Reset & base ────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Increase base body text to satisfy the ≥16 px rule */
.stApp p, .stApp li, .stApp label,
.stApp .stTextInput > label,
.stApp .stTextArea > label,
.stApp .stSelectbox > label {
    font-size: 1rem !important;
    line-height: 1.6 !important;
    color: #1F2937 !important;
}

/* ── Header banner ───────────────────────────────────────────────────────── */
.agri-header {
    background: linear-gradient(135deg, #14532D 0%, #166534 50%, #15803D 100%);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(21, 128, 61, 0.3);
}
.agri-header h1 {
    color: #FFFFFF !important;
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    letter-spacing: -0.5px;
}
.agri-header p {
    color: #BBF7D0 !important;
    font-size: 1rem !important;
    margin: 4px 0 0 0 !important;
}

/* ── Input labels ────────────────────────────────────────────────────────── */
.stTextArea textarea {
    font-size: 1rem !important;
    min-height: 120px;
    border-radius: 8px !important;
    border: 2px solid #D1FAE5 !important;
}
.stTextArea textarea:focus {
    border-color: #15803D !important;
    box-shadow: 0 0 0 3px rgba(21, 128, 61, 0.15) !important;
}
.stSelectbox div[data-baseweb="select"] > div {
    border-radius: 8px !important;
    border: 2px solid #D1FAE5 !important;
    font-size: 1rem !important;
}
.stTextInput input {
    font-size: 1rem !important;
    border-radius: 8px !important;
    border: 2px solid #D1FAE5 !important;
}

/* ── Primary action button ───────────────────────────────────────────────── */
div[data-testid="stFormSubmitButton"] > button,
button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg, #15803D, #16A34A) !important;
    color: #FFFFFF !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 32px !important;
    width: 100% !important;
    box-shadow: 0 3px 12px rgba(21, 128, 61, 0.35) !important;
    transition: all 0.2s ease !important;
    cursor: pointer;
}
div[data-testid="stFormSubmitButton"] > button:hover,
button[kind="primaryFormSubmit"]:hover {
    background: linear-gradient(135deg, #166534, #15803D) !important;
    box-shadow: 0 5px 18px rgba(21, 128, 61, 0.45) !important;
    transform: translateY(-1px);
}

/* Generic secondary buttons */
.stButton > button {
    border-radius: 8px !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}

/* ── Advisory response container ─────────────────────────────────────────── */
.advisory-container {
    background: #FFFFFF;
    border: 1px solid #D1FAE5;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    margin-top: 16px;
}

/* Markdown heading sizes inside the advisory */
.advisory-container h3 { font-size: 1.3rem !important; color: #14532D !important; }
.advisory-container h4 { font-size: 1.1rem !important; color: #166534 !important; }

/* ── Info / warning boxes ────────────────────────────────────────────────── */
.stAlert {
    border-radius: 8px !important;
    font-size: 0.95rem !important;
}

/* ── Expanders ───────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #374151 !important;
}

/* ── Spinner text ────────────────────────────────────────────────────────── */
.stSpinner p {
    font-size: 1rem !important;
    color: #374151 !important;
}

/* ── Character counter ───────────────────────────────────────────────────── */
.char-counter {
    font-size: 0.78rem;
    color: #9CA3AF;
    text-align: right;
    margin-top: -8px;
    margin-bottom: 4px;
}
.char-counter.warn { color: #D97706; font-weight: 600; }
.char-counter.error { color: #DC2626; font-weight: 700; }

/* ── Dividers ────────────────────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid #E5E7EB !important;
    margin: 20px 0 !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
:root {
    --app-sidebar-width: 300px;
    --app-sidebar-mobile-width: min(86vw, 320px);
    --app-sidebar-bg: #EEFBF1;
    --app-sidebar-border: #D5EADB;
    --app-sidebar-text: #1F2937;
    --app-sidebar-muted: #6B7280;
    --app-sidebar-hover: #E1F5E7;
    --app-sidebar-active: #D6F0DD;
}

section[data-testid="stSidebar"] {
    background: var(--app-sidebar-bg) !important;
    border-right: 1px solid var(--app-sidebar-border) !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding: 1rem !important;
}

section[data-testid="stSidebar"] .stButton {
    width: 100% !important;
    margin-bottom: 0.4rem !important;
}

section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    min-height: 42px !important;
    justify-content: flex-start !important;
    text-align: left !important;
    padding: 0.6rem 0.75rem !important;
    border: 0 !important;
    border-radius: 8px !important;
    color: var(--app-sidebar-text) !important;
    background: transparent !important;
    box-shadow: none !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--app-sidebar-hover) !important;
}

section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    color: #14532D !important;
    background: var(--app-sidebar-active) !important;
    font-weight: 700 !important;
}

@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        width: var(--app-sidebar-mobile-width) !important;
        min-width: var(--app-sidebar-mobile-width) !important;
        max-width: var(--app-sidebar-mobile-width) !important;
        box-shadow: 5px 0 20px rgba(0, 0, 0, 0.2) !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding: 0.85rem !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        min-height: 46px !important;
    }
}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #F9FAFB; }
::-webkit-scrollbar-thumb { background: #A7F3D0; border-radius: 3px; }

/* ── T-12: Eight-block advisory layout ───────────────────────────────────── */

/* Block section headers */
.advisory-block-header {
    border-left: 4px solid #16A34A;
    padding-left: 12px;
    margin: 24px 0 10px 0;
}
.advisory-block-header h3 {
    font-size: 1.15rem !important;
    color: #14532D !important;
    font-weight: 700 !important;
    margin: 0 !important;
}

/* Block 1 — Diagnosis card gradient */
.diagnosis-card {
    background: linear-gradient(135deg, #F0FDF4, #DCFCE7);
    border: 1px solid #BBF7D0;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 8px;
}
.diagnosis-card .disease-name {
    font-size: 1.4rem;
    font-weight: 800;
    color: #14532D;
    margin-bottom: 4px;
}

/* Block 2 — Treatment step cards */
.treatment-step {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 14px 18px;
    margin-bottom: 10px;
    background: #FFFFFF;
    border: 1px solid #D1FAE5;
    border-radius: 10px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
    transition: box-shadow 0.2s ease;
}
.treatment-step:hover {
    box-shadow: 0 3px 12px rgba(21, 128, 61, 0.12);
}
.treatment-step .step-num {
    background: #14532D;
    color: #FFFFFF;
    font-weight: 800;
    font-size: 1rem;
    min-width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

/* Urgency badges */
.urgency-badge {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    white-space: nowrap;
}

/* Block 3 — Prevention list */
.prevention-list {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 10px;
    padding: 16px 20px;
    list-style: none;
    margin: 0;
}
.prevention-list li {
    padding: 6px 0;
    color: #1F2937;
    font-size: 0.95rem;
    line-height: 1.55;
}

/* Block 4 — Weather alert card */
.weather-alert-card {
    border-radius: 10px;
    padding: 18px 22px;
    margin-top: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* Block 5 — Source citation cards */
.source-card {
    padding: 12px 16px;
    margin-bottom: 10px;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    transition: border-color 0.15s ease;
}
.source-card:hover { border-color: #A7F3D0; }
.source-card a { color: #1D4ED8; text-decoration: none; font-weight: 600; }
.source-card a:hover { text-decoration: underline; }

/* Block 6 — Disclaimer */
.disclaimer-card {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 16px 20px;
}

/* Block 7 — Confidence progress bar */
.confidence-bar-container {
    margin: 6px 0 12px 0;
}
.confidence-bar-track {
    background: #E5E7EB;
    border-radius: 6px;
    height: 10px;
    overflow: hidden;
}
.confidence-bar-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 0.6s ease;
}

/* Streamlit metric tweak for weather risk display */
[data-testid="stMetric"] {
    background: #FAFAFA;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 10px 14px !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: #14532D !important;
}

/* ── T-20: Authentication screens ───────────────────────────────────────── */

/* Full-page auth background */
.auth-bg {
    min-height: 100vh;
    background: linear-gradient(160deg, #052e16 0%, #14532d 40%, #1a6b3c 70%, #166534 100%);
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Glass card */
.auth-card {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid rgba(187, 247, 208, 0.6);
    border-radius: 20px;
    padding: 40px 36px;
    box-shadow:
        0 20px 60px rgba(0, 0, 0, 0.25),
        0 4px 16px rgba(21, 128, 61, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(12px);
    margin: 20px auto;
    max-width: 480px;
}

/* Card header block */
.auth-header-block {
    text-align: center;
    margin-bottom: 28px;
}

.auth-icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 10px;
    filter: drop-shadow(0 2px 6px rgba(21, 128, 61, 0.4));
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-6px); }
}

.auth-title {
    font-size: 1.75rem !important;
    font-weight: 800 !important;
    color: #14532D !important;
    margin: 0 0 6px 0 !important;
    letter-spacing: -0.5px;
}

.auth-subtitle {
    font-size: 0.95rem !important;
    color: #6B7280 !important;
    margin: 0 !important;
}

/* Switch link text */
.auth-switch-text {
    text-align: center;
    color: #6B7280 !important;
    font-size: 0.88rem !important;
    margin: 14px 0 6px 0 !important;
}

/* ── Logout button — red tint in sidebar ───────────────────────────────── */
.logout-btn > button {
    background: linear-gradient(135deg, #DC2626, #B91C1C) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
.logout-btn > button:hover {
    background: linear-gradient(135deg, #B91C1C, #991B1B) !important;
    box-shadow: 0 4px 14px rgba(220, 38, 38, 0.4) !important;
    transform: translateY(-1px);
}

/* ── Auth hero strip above the card ────────────────────────────────────── */
.auth-hero {
    background: linear-gradient(135deg, #14532D 0%, #166534 50%, #15803D 100%);
    border-radius: 12px;
    padding: 18px 24px;
    text-align: center;
    margin-bottom: 16px;
    box-shadow: 0 4px 16px rgba(21, 128, 61, 0.3);
}
.auth-hero h1 {
    color: #FFFFFF !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
}
.auth-hero p {
    color: #BBF7D0 !important;
    font-size: 0.9rem !important;
    margin: 4px 0 0 0 !important;
}

/* ── Authenticated user chip in header ─────────────────────────────────── */
.user-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(220, 252, 231, 0.9);
    border: 1px solid #86EFAC;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.88rem;
    font-weight: 600;
    color: #14532D;
    white-space: nowrap;
}

/* ── Theme-aware Streamlit surfaces ─────────────────────────────────────── */
:root {
    color-scheme: light;
    --ui-page: #F8FAFC;
    --ui-surface: #FFFFFF;
    --ui-surface-muted: #F0FDF4;
    --ui-text: #1F2937;
    --ui-text-muted: #6B7280;
    --ui-border: #D1D5DB;
    --ui-input-border: #A7F3D0;
}

.stApp {
    background: transparent !important;
    color: inherit !important;
}
.stApp p, .stApp li, .stApp label,
.stApp [data-testid="stMarkdownContainer"],
.stApp .stCaption {
    color: inherit !important;
}
.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div {
    background: var(--ui-surface) !important;
    color: var(--ui-text) !important;
    border-color: var(--ui-input-border) !important;
}
.advisory-container, .treatment-step, .source-card,
[data-testid="stMetric"] {
    background: var(--ui-surface) !important;
    color: var(--ui-text) !important;
    border-color: var(--ui-border) !important;
}
[data-testid="stSidebar"] {
    background: var(--ui-surface-muted) !important;
    border-right: 1px solid var(--ui-border);
}
.streamlit-expanderHeader, .stSpinner p {
    color: var(--ui-text) !important;
}

</style>
"""

# Explicit Light mode is injected after GLOBAL_CSS so it wins over browser and
# operating-system defaults. Keep the colors in variables for consistent
# contrast across Streamlit surfaces and HTML advisory cards.
LIGHT_MODE_CSS = """
<style>
:root {
    color-scheme: light;
    --ui-page: #F8FAFC;
    --ui-surface: #FFFFFF;
    --ui-surface-muted: #F0FDF4;
    --ui-text: #1F2937;
    --ui-text-muted: #6B7280;
    --ui-border: #D1D5DB;
    --ui-input-border: #A7F3D0;
}
.stApp, .stAppHeader, header[data-testid="stHeader"] {
    background: var(--ui-page) !important;
    color: var(--ui-text) !important;
}
.stApp p, .stApp li, .stApp label,
.stApp [data-testid="stMarkdownContainer"], .stApp .stCaption,
.streamlit-expanderHeader, .stSpinner p {
    color: var(--ui-text) !important;
}
.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div,
[data-baseweb="popover"] {
    background: var(--ui-surface) !important;
    color: var(--ui-text) !important;
    border-color: var(--ui-input-border) !important;
}
.advisory-container, .treatment-step, .source-card,
[data-testid="stMetric"], .auth-card {
    background: var(--ui-surface) !important;
    color: var(--ui-text) !important;
    border-color: var(--ui-border) !important;
}
[data-testid="stSidebar"] { background: var(--ui-surface-muted) !important; }
hr { border-top-color: var(--ui-border) !important; }
</style>
"""

# Applied as a separate style block so the sidebar selector can force dark mode
# even when the operating system is configured for light mode.
DARK_MODE_CSS = """
<style>
:root {
    color-scheme: dark;
    --ui-page: #111827;
    --ui-surface: #1F2937;
    --ui-surface-muted: #17251D;
    --ui-text: #F3F4F6;
    --ui-text-muted: #D1D5DB;
    --ui-border: #4B5563;
    --ui-input-border: #15803D;
}
.stApp, .stAppHeader, header[data-testid="stHeader"] {
    background: #111827 !important;
    color: #F3F4F6 !important;
}
[data-testid="stSidebar"] { background: #17251D !important; }
.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div,
[data-baseweb="popover"] {
    background: #1F2937 !important;
    color: #F9FAFB !important;
    border-color: #15803D !important;
}
.auth-card, .advisory-container, .treatment-step, .source-card,
[data-testid="stMetric"] {
    background: #1F2937 !important;
    color: #F3F4F6 !important;
    border-color: #4B5563 !important;
}
[data-testid="stMarkdownContainer"] div[style*="background:#FFFFFF"],
[data-testid="stMarkdownContainer"] div[style*="background: #FFFFFF"],
[data-testid="stMarkdownContainer"] div[style*="background:#FAFAFA"],
[data-testid="stMarkdownContainer"] div[style*="background: #FAFAFA"] {
    background: #263445 !important;
    border-color: #4B5563 !important;
}
[data-testid="stMarkdownContainer"] div[style*="background:#F0FDF4"],
[data-testid="stMarkdownContainer"] div[style*="background: #F0FDF4"],
[data-testid="stMarkdownContainer"] div[style*="background:#EFF6FF"],
[data-testid="stMarkdownContainer"] div[style*="background: #EFF6FF"],
[data-testid="stMarkdownContainer"] div[style*="background:#F9FAFB"],
[data-testid="stMarkdownContainer"] div[style*="background: #F9FAFB"] {
    background: #1F2937 !important;
    border-color: #4B5563 !important;
}
[data-testid="stMarkdownContainer"] [style*="color:#1F2937"],
[data-testid="stMarkdownContainer"] [style*="color: #1F2937"],
[data-testid="stMarkdownContainer"] [style*="color:#374151"],
[data-testid="stMarkdownContainer"] [style*="color: #374151"] {
    color: #E5E7EB !important;
}
[data-testid="stMarkdownContainer"] [style*="color:#14532D"],
[data-testid="stMarkdownContainer"] [style*="color: #14532D"],
[data-testid="stMarkdownContainer"] [style*="color:#166534"],
[data-testid="stMarkdownContainer"] [style*="color: #166534"] {
    color: #BBF7D0 !important;
}
[data-testid="stMarkdownContainer"] [style*="color:#6B7280"],
[data-testid="stMarkdownContainer"] [style*="color: #6B7280"] {
    color: #CBD5E1 !important;
}
.auth-title, .advisory-container h3, .advisory-container h4,
.advisory-block-header h3 { color: #BBF7D0 !important; }
.auth-subtitle, .auth-switch-text, .char-counter,
.streamlit-expanderHeader, .stSpinner p { color: #D1D5DB !important; }
.diagnosis-card, .prevention-list {
    background: #163A27 !important;
    border-color: #166534 !important;
}
hr { border-top-color: #4B5563 !important; }
</style>
"""