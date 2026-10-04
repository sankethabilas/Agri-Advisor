"""
ui/styles.py
Agri-Advisor — Premium Agricultural AI SaaS Design System.
Inspired by Apple, Linear, Vercel, and modern fintech/AI platforms.

Features:
  - Curated Forest Green, Emerald, Sage, Warm Neutral, and Dark palettes
  - CSS Custom Properties (Design Tokens) for Light and Dark modes
  - Bento grid layouts, glassmorphism accents, fine borders, and smooth shadows
  - Micro-interactions, animated AI status steppers, and pulse indicators
  - Full responsive layouts (320px to 1920px)
  - Accessible, WCAG-conscious typography & contrast
"""

GLOBAL_CSS = """
<style>
/* ── Google Fonts: Inter & Outfit ────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Root Design Tokens (Light Theme) ─────────────────────────────────────── */
:root {
    --font-main: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --font-heading: 'Outfit', 'Inter', -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;

    /* Primary Brand Palette */
    --color-primary-950: #041d11;
    --color-primary-900: #072d1b;
    --color-primary-800: #0b452b;
    --color-primary-700: #0f623e;
    --color-primary-600: #108e58;
    --color-primary-500: #10b981;
    --color-primary-400: #34d399;
    --color-primary-300: #6ee7b7;
    --color-primary-200: #a7f3d0;
    --color-primary-100: #d1fae5;
    --color-primary-50:  #ecfdf5;

    /* Secondary Palette */
    --color-secondary-500: #84cc16;
    --color-secondary-400: #a3e635;
    --color-secondary-100: #f7fee7;

    /* Neutral Surfaces */
    --bg-app: #f8faf9;
    --bg-surface: #ffffff;
    --bg-surface-elevated: #ffffff;
    --bg-glass: rgba(255, 255, 255, 0.85);
    --bg-subtle: #f1f5f3;
    --bg-sidebar: #f2f7f4;

    /* Text & Foregrounds */
    --text-primary: #0f172a;
    --text-secondary: #334155;
    --text-muted: #64748b;
    --text-subtle: #94a3b8;
    --text-inverse: #ffffff;

    /* Borders & Dividers */
    --border-subtle: rgba(16, 185, 129, 0.12);
    --border-default: rgba(16, 185, 129, 0.22);
    --border-strong: rgba(16, 185, 129, 0.4);
    --border-glass: rgba(255, 255, 255, 0.6);

    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    --shadow-md: 0 4px 12px -2px rgba(10, 45, 27, 0.06), 0 2px 6px -1px rgba(10, 45, 27, 0.03);
    --shadow-lg: 0 10px 25px -3px rgba(10, 45, 27, 0.08), 0 4px 10px -2px rgba(10, 45, 27, 0.04);
    --shadow-glow: 0 0 20px rgba(16, 185, 129, 0.25);

    /* Corner Radii */
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;
    --radius-xl: 24px;
    --radius-full: 9999px;

    /* Accents */
    --accent-weather: #0284c7;
    --accent-weather-bg: #e0f2fe;
    --accent-disease: #ea580c;
    --accent-disease-bg: #ffedd5;
    --accent-market: #d97706;
    --accent-market-bg: #fef3c7;
    --accent-ai: #8b5cf6;
    --accent-ai-bg: #f3e8ff;
    --accent-success: #10b981;
    --accent-success-bg: #d1fae5;
    --accent-error: #ef4444;
    --accent-error-bg: #fee2e2;
}

/* ── Base App & Reset ─────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: var(--font-main) !important;
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.stApp {
    background-color: var(--bg-app) !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(16, 185, 129, 0.05) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(132, 204, 22, 0.04) 0px, transparent 50%) !important;
    background-attachment: fixed !important;
}

/* Hide default streamlit clutter */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0px !important;
}

/* Ensure padding matches production app */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1440px !important;
}

/* ── Typography Enhancements ──────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-heading) !important;
    letter-spacing: -0.025em;
    color: var(--text-primary);
    font-weight: 700;
}

/* ── Top Bar Container ────────────────────────────────────────────────────── */
.topbar-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg-glass);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 12px 20px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
}

.topbar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-badge-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    border-radius: var(--radius-md);
    background: linear-gradient(135deg, var(--color-primary-800), var(--color-primary-600));
    color: #ffffff;
    font-size: 1.25rem;
    box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
}

.brand-text-title {
    font-family: var(--font-heading);
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--color-primary-900);
    letter-spacing: -0.03em;
    margin: 0;
    line-height: 1.2;
}

.brand-text-subtitle {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--color-primary-600);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin: 0;
}

.topbar-actions {
    display: flex;
    align-items: center;
    gap: 14px;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--color-primary-50);
    border: 1px solid var(--color-primary-200);
    color: var(--color-primary-800);
    font-size: 0.78rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: var(--radius-full);
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: var(--color-primary-500);
    box-shadow: 0 0 8px var(--color-primary-500);
    animation: pulse 2s infinite ease-in-out;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
}

/* ── Hero Banner ──────────────────────────────────────────────────────────── */
.hero-card {
    background: linear-gradient(135deg, #072D1B 0%, #0B452B 50%, #0F623E 100%);
    border-radius: var(--radius-xl);
    padding: 32px 36px;
    color: #ffffff;
    margin-bottom: 28px;
    box-shadow: 0 10px 30px -5px rgba(7, 45, 27, 0.4);
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.hero-card::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 350px;
    height: 350px;
    background: radial-gradient(circle, rgba(110, 231, 183, 0.18) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

.hero-card h1 {
    color: #ffffff !important;
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    margin: 0 0 6px 0 !important;
    letter-spacing: -0.03em;
}

.hero-card p {
    color: #d1fae5 !important;
    font-size: 1.05rem !important;
    max-width: 650px;
    margin: 0 !important;
    line-height: 1.5 !important;
    opacity: 0.95;
}

/* ── Bento Grid System ────────────────────────────────────────────────────── */
.bento-grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 20px;
    margin-bottom: 24px;
}

.bento-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 24px;
    box-shadow: var(--shadow-md);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}

.bento-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-strong);
}

.bento-col-4 { grid-column: span 4; }
.bento-col-6 { grid-column: span 6; }
.bento-col-8 { grid-column: span 8; }
.bento-col-12 { grid-column: span 12; }

.bento-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}

.bento-title {
    font-family: var(--font-heading);
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
}

.bento-badge {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.bento-stat-number {
    font-family: var(--font-heading);
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--color-primary-900);
    letter-spacing: -0.04em;
    line-height: 1.1;
}

.bento-stat-label {
    font-size: 0.85rem;
    color: var(--text-muted);
    font-weight: 500;
    margin-top: 4px;
}

/* ── Multi-Agent Visualizer Stepper ───────────────────────────────────────── */
.agent-flow-container {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 22px 24px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-sm);
}

.agent-flow-title {
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-primary-700);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.agent-stepper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 4px;
}

.agent-step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 110px;
    text-align: center;
    position: relative;
}

.agent-step-icon {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    margin-bottom: 8px;
    transition: all 0.3s ease;
    border: 2px solid transparent;
}

.agent-step-active .agent-step-icon {
    background: var(--color-primary-50);
    border-color: var(--color-primary-500);
    color: var(--color-primary-700);
    box-shadow: 0 0 14px rgba(16, 185, 129, 0.4);
    transform: scale(1.08);
}

.agent-step-done .agent-step-icon {
    background: var(--color-primary-500);
    color: #ffffff;
}

.agent-step-waiting .agent-step-icon {
    background: var(--bg-subtle);
    color: var(--text-subtle);
}

.agent-step-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-primary);
}

.agent-step-status {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 2px;
}

/* ── AI Workspace Container ───────────────────────────────────────────────── */
.workspace-box {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-xl);
    padding: 32px;
    box-shadow: var(--shadow-md);
    margin-bottom: 28px;
}

.workspace-header {
    margin-bottom: 24px;
}

.workspace-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--color-primary-950);
    margin: 0 0 6px 0;
    letter-spacing: -0.03em;
}

.workspace-subtitle {
    font-size: 0.98rem;
    color: var(--text-muted);
    margin: 0;
}

.prompt-chips-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 14px 0 20px 0;
}

.prompt-chip {
    background: var(--bg-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-full);
    padding: 6px 14px;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;
}

.prompt-chip:hover {
    background: var(--color-primary-50);
    border-color: var(--color-primary-300);
    color: var(--color-primary-800);
    transform: translateY(-1px);
}

/* ── Result 11-Part Bento Blocks ──────────────────────────────────────────── */
.result-container {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-xl);
    padding: 36px;
    box-shadow: var(--shadow-lg);
    margin-top: 24px;
    margin-bottom: 36px;
}

.result-badge-diagnosis {
    background: linear-gradient(135deg, #ECFDF5, #D1FAE5);
    border: 1px solid var(--color-primary-300);
    border-radius: var(--radius-lg);
    padding: 24px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.diagnosis-primary-name {
    font-family: var(--font-heading);
    font-size: 1.65rem;
    font-weight: 800;
    color: var(--color-primary-950);
    margin: 0 0 4px 0;
}

.diagnosis-scientific-name {
    font-size: 0.95rem;
    font-style: italic;
    color: var(--color-primary-700);
    margin: 0;
}

.action-step-card {
    background: var(--bg-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 16px 20px;
    margin-bottom: 12px;
    display: flex;
    align-items: flex-start;
    gap: 16px;
    transition: all 0.2s ease;
}

.action-step-card:hover {
    background: var(--bg-surface);
    border-color: var(--color-primary-400);
    box-shadow: var(--shadow-sm);
    transform: translateX(3px);
}

.action-step-num {
    font-family: var(--font-heading);
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--color-primary-600);
    background: var(--color-primary-50);
    border: 1px solid var(--color-primary-200);
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.action-step-content {
    flex: 1;
}

.action-step-title {
    font-weight: 700;
    font-size: 0.98rem;
    color: var(--text-primary);
    margin: 0 0 3px 0;
}

.action-step-desc {
    font-size: 0.88rem;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.5;
}

/* ── Agent Network Topology Cards ─────────────────────────────────────────── */
.agent-node-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 22px;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
    height: 100%;
}

.agent-node-card:hover {
    border-color: var(--color-primary-400);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

.agent-node-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.agent-node-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
}

.agent-node-role {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 16px;
    line-height: 1.4;
}

.agent-node-metric {
    display: flex;
    justify-content: space-between;
    font-size: 0.82rem;
    padding: 6px 0;
    border-top: 1px solid var(--border-subtle);
    color: var(--text-secondary);
}

/* ── Streamlit Native Elements Overrides ──────────────────────────────────── */

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    border-radius: var(--radius-md) !important;
    border: 1px solid #d1d5db !important;
    font-size: 0.98rem !important;
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    transition: all 0.2s ease !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--color-primary-500) !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18) !important;
}

/* Buttons */
.stButton > button {
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 8px 18px !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stFormSubmitButton"] > button,
button[kind="primaryFormSubmit"],
.primary-ai-btn {
    background: linear-gradient(135deg, #072D1B 0%, #0F623E 50%, #10B981 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    border: none !important;
    border-radius: var(--radius-lg) !important;
    padding: 14px 28px !important;
    box-shadow: 0 4px 18px rgba(16, 185, 129, 0.35) !important;
    width: 100% !important;
}

div[data-testid="stFormSubmitButton"] > button:hover,
button[kind="primaryFormSubmit"]:hover,
.primary-ai-btn:hover {
    background: linear-gradient(135deg, #041D11 0%, #0B452B 50%, #059669 100%) !important;
    box-shadow: 0 6px 24px rgba(16, 185, 129, 0.5) !important;
    transform: translateY(-2px) !important;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-subtle) !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 1.5rem !important;
}

.sidebar-section-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin: 18px 0 8px 6px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background-color: var(--bg-subtle) !important;
    padding: 5px !important;
    border-radius: var(--radius-lg) !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-md) !important;
    padding: 8px 16px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    color: var(--text-muted) !important;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background-color: var(--bg-surface) !important;
    color: var(--color-primary-900) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Responsive Breakpoints */
@media (max-width: 900px) {
    .bento-col-4, .bento-col-6, .bento-col-8 { grid-column: span 12; }
    .hero-card { padding: 24px 20px; }
    .hero-card h1 { font-size: 1.6rem !important; }
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .agent-stepper { justify-content: flex-start; }
}
</style>
"""

DARK_MODE_CSS = """
<style>
/* ── Dark Theme Overrides (Refined Apple/Vercel Dark Palette) ─────────────── */
:root {
    --bg-app: #06140e;
    --bg-surface: #0b2218;
    --bg-surface-elevated: #113324;
    --bg-glass: rgba(11, 34, 24, 0.85);
    --bg-subtle: #0f2d20;
    --bg-sidebar: #081a13;

    --text-primary: #f1f5f9;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    --text-subtle: #64748b;

    --border-subtle: rgba(16, 185, 129, 0.15);
    --border-default: rgba(16, 185, 129, 0.3);
    --border-strong: rgba(16, 185, 129, 0.5);

    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 16px -2px rgba(0, 0, 0, 0.5);
    --shadow-lg: 0 10px 30px -3px rgba(0, 0, 0, 0.7);

    --accent-weather-bg: #0c4a6e;
    --accent-disease-bg: #7c2d12;
    --accent-market-bg: #78350f;
    --accent-ai-bg: #4c1d95;
    --accent-success-bg: #064e3b;
    --accent-error-bg: #7f1d1d;
}

.stApp {
    background-color: var(--bg-app) !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(16, 185, 129, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(6, 78, 59, 0.12) 0px, transparent 50%) !important;
}

.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    background-color: #0d281d !important;
    border-color: rgba(16, 185, 129, 0.25) !important;
    color: #f1f5f9 !important;
}

.result-badge-diagnosis {
    background: linear-gradient(135deg, #072D1B, #0E482F) !important;
    border-color: var(--color-primary-600) !important;
}

.diagnosis-primary-name {
    color: #34d399 !important;
}

.action-step-card {
    background: #0d281d !important;
}

.action-step-title {
    color: #f8fafc !important;
}

.action-step-desc {
    color: #cbd5e1 !important;
}
</style>
"""

LIGHT_MODE_CSS = """
<style>
/* ── Explicit Light Theme Reinforcement ──────────────────────────────────── */
:root {
    --bg-app: #f8faf9;
    --bg-surface: #ffffff;
    --text-primary: #0f172a;
}
</style>
"""