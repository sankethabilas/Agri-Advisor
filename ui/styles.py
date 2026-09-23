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
[data-testid="stSidebar"] {
    background: #F0FDF4 !important;
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
</style>
"""
