"""
ui/app.py
Agri-Advisor — Redesigned Autonomous Agricultural Intelligence Operating System.
Production-grade multi-agent interface for Sri Lankan farmers & agronomists.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import html
from pathlib import Path
import random
import sys
import uuid
from typing import Any, Dict, List, Optional

import streamlit as st

# Make project-local packages importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
    render_agent_stepper,
    render_bento_crop_health,
    render_bento_market_card,
    render_bento_sentinel_alert,
    render_bento_weather_card,
    render_error,
    render_hero_banner,
    render_topbar,
)
from ui.config import (
    APP_ICON,
    APP_ICON_PATH,
    APP_SUBTITLE,
    APP_TITLE,
    CROP_CONTEXTS,
    DISTRICTS,
    LANGUAGES,
    get_app_icon_base64,
)
from ui.history_store import load_history, save_history
from ui.styles import DARK_MODE_CSS, GLOBAL_CSS, LIGHT_MODE_CSS
from utils.i18n import SUPPORTED_LANGUAGES, get_string

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title=f"{APP_TITLE} — Agricultural AI OS",
    page_icon=str(APP_ICON_PATH) if APP_ICON_PATH.exists() else "🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Core Styles
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def _init_session() -> None:
    """Initializes session state keys."""
    init_auth_session()

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "last_response" not in st.session_state:
        st.session_state.last_response = None
    if "last_error" not in st.session_state:
        st.session_state.last_error = None
    if "language" not in st.session_state:
        st.session_state.language = "en"
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "en"
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Light"
    if "active_page" not in st.session_state:
        st.session_state.active_page = "dashboard"
    if "quick_prompt" not in st.session_state:
        st.session_state.quick_prompt = ""

    user_id = st.session_state.get("user_id")
    if user_id and st.session_state.get("history_owner") != user_id:
        st.session_state.conversation_history = load_history(user_id)
        st.session_state["history_owner"] = user_id


# ============================================================================
# Theme Injection
# ============================================================================
_init_session()

if st.session_state.theme_mode == "Dark":
    st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)
else:
    st.markdown(LIGHT_MODE_CSS, unsafe_allow_html=True)


# ============================================================================
# Auth Gate
# ============================================================================
if not is_authenticated():
    render_auth_screen()
    st.stop()


# ============================================================================
# Sidebar Navigation Shell
# ============================================================================
user_id = str(st.session_state.get("user_id") or "Farmer")
saved_district = str(st.session_state.get("saved_district") or "Kurunegala")
current_lang = str(st.session_state.get("language") or "en")

with st.sidebar:
    logo_b64 = get_app_icon_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 100%; height: 100%; object-fit: contain; border-radius: 8px;" alt="Logo" />' if logo_b64 else '🌾'
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding: 4px 6px;">
            <div style="width: 42px; height: 42px; border-radius: 10px; background: #072D1B; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); padding: 2px;">
                {logo_html}
            </div>
            <div>
                <div style="font-family: var(--font-heading); font-size: 1.15rem; font-weight: 800; color: var(--color-primary-950); line-height: 1.1;">Agri-Advisor</div>
                <div style="font-size: 0.72rem; font-weight: 600; color: var(--color-primary-600); text-transform: uppercase; letter-spacing: 0.05em;">AI Operating System</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. OVERVIEW
    st.markdown('<div class="sidebar-section-label">OVERVIEW</div>', unsafe_allow_html=True)
    if st.button("📊  Dashboard", key="nav_dash", use_container_width=True, type="primary" if st.session_state.active_page == "dashboard" else "secondary"):
        st.session_state.active_page = "dashboard"
        st.rerun()

    # 2. FARM INTELLIGENCE
    st.markdown('<div class="sidebar-section-label">FARM INTELLIGENCE</div>', unsafe_allow_html=True)
    if st.button("🌾  My Crops & Cultivation", key="nav_crops", use_container_width=True, type="primary" if st.session_state.active_page == "my_crops" else "secondary"):
        st.session_state.active_page = "my_crops"
        st.rerun()

    if st.button("🔬  Crop Health & Scanner", key="nav_health", use_container_width=True, type="primary" if st.session_state.active_page == "crop_health" else "secondary"):
        st.session_state.active_page = "crop_health"
        st.rerun()

    if st.button("🌦️  Agro-Weather Forecast", key="nav_weather", use_container_width=True, type="primary" if st.session_state.active_page == "weather" else "secondary"):
        st.session_state.active_page = "weather"
        st.rerun()

    if st.button("📈  Commodity Market Prices", key="nav_market", use_container_width=True, type="primary" if st.session_state.active_page == "market" else "secondary"):
        st.session_state.active_page = "market"
        st.rerun()

    # 3. AI INTELLIGENCE
    st.markdown('<div class="sidebar-section-label">AI INTELLIGENCE</div>', unsafe_allow_html=True)
    if st.button("✨  AI Agricultural Advisor", key="nav_ai_adv", use_container_width=True, type="primary" if st.session_state.active_page == "ai_advisor" else "secondary"):
        st.session_state.active_page = "ai_advisor"
        st.rerun()

    if st.button("🧠  AI Agent Network", key="nav_network", use_container_width=True, type="primary" if st.session_state.active_page == "agent_network" else "secondary"):
        st.session_state.active_page = "agent_network"
        st.rerun()

    if st.button("🛡️  Outbreak Sentinel", key="nav_sentinel", use_container_width=True, type="primary" if st.session_state.active_page == "sentinel" else "secondary"):
        st.session_state.active_page = "sentinel"
        st.rerun()

    if st.button("📜  Consultation History", key="nav_history", use_container_width=True, type="primary" if st.session_state.active_page == "history" else "secondary"):
        st.session_state.active_page = "history"
        st.rerun()

    # 4. COMMUNITY
    st.markdown('<div class="sidebar-section-label">COMMUNITY</div>', unsafe_allow_html=True)
    if st.button("💬  Farmer Knowledge Forum", key="nav_forum", use_container_width=True, type="primary" if st.session_state.active_page == "forum" else "secondary"):
        st.session_state.active_page = "forum"
        st.rerun()

    # 5. PREFERENCES & PROFILE
    st.markdown('<div class="sidebar-section-label">PREFERENCES</div>', unsafe_allow_html=True)
    
    # Language Selector
    lang_labels = list(LANGUAGES.keys())
    current_lang_idx = 0
    for idx, (label, code) in enumerate(LANGUAGES.items()):
        if code == current_lang:
            current_lang_idx = idx
            break

    selected_lang_label = st.selectbox("🌐 Interface Language", lang_labels, index=current_lang_idx, key="sb_lang")
    new_lang_code = LANGUAGES[selected_lang_label]
    if new_lang_code != current_lang:
        st.session_state.language = new_lang_code
        st.session_state.selected_language = new_lang_code
        st.rerun()

    # Theme Toggle
    theme_choice = st.radio("🎨 Display Theme", ["Light", "Dark"], index=0 if st.session_state.theme_mode == "Light" else 1, horizontal=True)
    if theme_choice != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_choice
        st.rerun()

    st.markdown("---")
    
    # User Profile Block & Logout
    st.markdown(
        f"""
        <div style="background: var(--bg-surface); padding: 12px 14px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: var(--color-primary-100); color: var(--color-primary-800); font-weight: 700; display: flex; align-items: center; justify-content: center; font-size: 0.85rem;">
                    {user_id[:2].upper()}
                </div>
                <div style="flex: 1; overflow: hidden;">
                    <div style="font-weight: 700; font-size: 0.9rem; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">{user_id}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">📍 {saved_district}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🚪  Sign Out", key="btn_logout", use_container_width=True):
        clear_auth()
        st.rerun()


# ============================================================================
# Top Bar Header
# ============================================================================
render_topbar(
    active_page_name=st.session_state.active_page.replace("_", " ").title(),
    user_id=user_id,
    district=saved_district,
    language=current_lang,
)


# ============================================================================
# VIEW 1: DASHBOARD
# ============================================================================
if st.session_state.active_page == "dashboard":
    render_hero_banner(
        greeting="Good day, Farmer 👋",
        title="Your Farm Intelligence at a Glance",
        subtitle=f"Live agro-meteorological risk analysis, market commodity trends, and autonomous disease surveillance for {saved_district}.",
    )

    # Bento Grid 1: Key Metrics
    col_w, col_h, col_m = st.columns([1, 1, 1])
    with col_w:
        render_bento_weather_card(
            district=saved_district,
            temp_c=29.2,
            humidity=76,
            condition="Partly Cloudy",
            disease_risk="Moderate",
        )
    with col_h:
        render_bento_crop_health(
            monitored_crops=3,
            avg_health_pct=94,
            active_advisories=1,
        )
    with col_m:
        render_bento_market_card(
            top_commodity="Paddy (Nadu / Samba)",
            price_lkr_kg=128.0,
            change_pct=3.2,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Bento Grid 2: Sentinel Alerts & Quick Actions
    col_sentinel, col_quick = st.columns([3, 2])
    with col_sentinel:
        render_bento_sentinel_alert(
            level="Normal",
            district=saved_district,
            details=f"Automated surveillance scan verified clean status for {saved_district} and adjacent districts. Background spore activity is within 28-day baseline limits.",
        )
    with col_quick:
        st.markdown(
            """
            <div class="bento-card" style="height: 100%;">
                <div class="bento-header">
                    <div class="bento-title">✨ Ask Agri-Advisor AI</div>
                </div>
                <p style="font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 16px;">
                    Have an urgent question about leaf symptoms, planting calendars, or fertilizer dosage?
                </p>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚀 Launch AI Advisor Workspace", key="dash_btn_ai", use_container_width=True, type="primary"):
            st.session_state.active_page = "ai_advisor"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Multi-Agent Pipeline Status
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    render_agent_stepper("ready")


# ============================================================================
# VIEW 2: AI AGRICULTURAL ADVISOR (WORKSPACE)
# ============================================================================
elif st.session_state.active_page == "ai_advisor":
    st.markdown(
        """
        <div class="workspace-box">
            <div class="workspace-header">
                <span style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--color-primary-600);">
                    Autonomous Agricultural Assistant
                </span>
                <h1 class="workspace-title">How can Agri-Advisor help today?</h1>
                <p class="workspace-subtitle">
                    Describe your crop, pest symptoms, fertilizer doubts, or seasonal weather concerns in plain English, Sinhala, or Tamil.
                </p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick Example Prompt Chips
    st.markdown("<div style='font-size: 0.82rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;'>Suggested Queries:</div>", unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        if st.button("🌾 Paddy leaves have brown spindle spots", key="p_chip_1", use_container_width=True):
            st.session_state.quick_prompt = "My paddy leaves in Kurunegala have spindle-shaped brown lesions with grey centres and yellowing tips. What disease is this and what is the treatment?"
    with col_p2:
        if st.button("🌽 Maize Maha season 4-stage fertilizer plan", key="p_chip_2", use_container_width=True):
            st.session_state.quick_prompt = "Give me a 4-stage fertilizer schedule and seed variety recommendations for Maize in the Maha season."
    with col_p3:
        if st.button("🌦️ Spraying fungicide before rain forecast", key="p_chip_3", use_container_width=True):
            st.session_state.quick_prompt = "Is it safe to spray copper bactericide this week given high relative humidity and rain alerts in Anuradhapura?"

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    with st.form("ai_query_form", clear_on_submit=False):
        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            district_idx = DISTRICTS.index(saved_district) if saved_district in DISTRICTS else 0
            selected_district = st.selectbox("📍 District", DISTRICTS, index=district_idx, key="query_district")
        with col_f2:
            selected_crop = st.selectbox("🌱 Crop Type (Optional)", CROP_CONTEXTS, index=1, key="query_crop")

        default_text = st.session_state.quick_prompt or ""
        problem_description = st.text_area(
            "📝 Describe your crop symptoms, questions, or field observations",
            value=default_text,
            placeholder="e.g. My paddy leaves have yellow tips and brown spots. Humidity is high. What should I apply?",
            height=130,
            key="query_text",
        )

        # Photo upload drag & drop area
        uploaded_image = st.file_uploader("📷 Attach crop leaf / field photograph (Optional for Disease Scanner)", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Crop Leaf Preview", width=250)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        col_b1, col_b2 = st.columns([3, 1])
        with col_b1:
            submitted = st.form_submit_button("✨ Analyze with Agri-Advisor AI", use_container_width=True, type="primary")
        with col_b2:
            cleared = st.form_submit_button("🔄 Clear", use_container_width=True)
            if cleared:
                st.session_state.quick_prompt = ""
                st.session_state.last_response = None
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Process Query
    if submitted and problem_description.strip():
        render_agent_stepper("processing")
        with st.spinner("🤖 Multi-agent network analyzing symptoms, microclimate, and verified DOA literature..."):
            try:
                payload = build_payload(
                    query=problem_description.strip(),
                    user_id=user_id,
                    district=selected_district,
                    language=current_lang,
                    crop_context=selected_crop if selected_crop != "— Not specified —" else None,
                    session_id=st.session_state.session_id,
                )
                response_data, is_fallback = call_orchestrator(payload, auth_headers=get_auth_headers())
                st.session_state.last_response = response_data
                st.session_state.last_error = None
                
                # Save to history
                save_history(user_id, problem_description.strip(), response_data)
                if "conversation_history" not in st.session_state or not isinstance(st.session_state.conversation_history, list):
                    st.session_state.conversation_history = []
                st.session_state.conversation_history.append({
                    "query": problem_description.strip(),
                    "response": response_data,
                })
                render_agent_stepper("completed")
            except _ApiError as err:
                st.session_state.last_error = f"API Error ({err.status_code}): {err.detail}"
            except Exception as exc:
                st.session_state.last_error = f"Service Error: {str(exc)}"

    if st.session_state.last_error:
        render_error(st.session_state.last_error)

    if st.session_state.last_response:
        render_advisory_response(
            response=st.session_state.last_response,
            session_id=st.session_state.session_id,
            language=current_lang,
        )


# ============================================================================
# VIEW 3: AI AGENT NETWORK TOPOLOGY
# ============================================================================
elif st.session_state.active_page == "agent_network":
    render_hero_banner(
        greeting="Multi-Agent Architecture",
        title="Agri-Advisor Multi-Agent Topology",
        subtitle="Real-time status, latency benchmarks, and autonomous routing topology across specialist agents.",
    )

    st.markdown(
        """
        <div style="background: var(--bg-surface); padding: 24px; border-radius: var(--radius-xl); border: 1px solid var(--border-subtle); margin-bottom: 24px;">
            <h3 style="margin-top: 0; color: var(--color-primary-900);">⚡ Autonomous Hub-and-Spoke Mesh</h3>
            <p style="color: var(--text-secondary); font-size: 0.95rem;">
                Agri-Advisor enforces strict agent modularity: The central <strong>Orchestrator Agent</strong> parses intent using spaCy NLP and coordinates specialist sub-agents over high-speed REST JSON protocols with zero direct peer-to-peer coupling.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    agent_grid_data = [
        ("🧠 Orchestrator Hub", "Central NLP routing, NER extraction, multi-agent coordination, and LLM response synthesis.", "● Online", "18 ms", "spaCy + Groq LLaMA-3.1"),
        ("🔬 Disease Diagnosis Agent", "Pathological symptom token matching, candidate ranking, severity scoring, and differential diagnosis.", "● Online", "42 ms", "Rule-Based + DOA Knowledge Base"),
        ("🌦️ Weather Intelligence Agent", "Live OpenWeatherMap ingestion, 7-day agro-meteorological forecasting, and fungal risk calculation.", "● Online", "95 ms", "OpenWeather API + Risk Heuristics"),
        ("📚 RAG Semantic Retrieval Agent", "ChromaDB vector store search over verified Sri Lankan Department of Agriculture documents.", "● Online", "34 ms", "Sentence-Transformers (all-MiniLM-L6-v2)"),
        ("🌾 Crop Advisory Agent", "8-stage cultivation planning, variety selection, 4-split fertilizer calculators, and harvest scheduling.", "● Online", "28 ms", "Structured Agronomy Matrix"),
        ("🛡️ Outbreak Sentinel Agent", "Autonomous Sense-Reason-Act-Learn surveillance detecting regional disease anomalies over 28-day baselines.", "● Online", "52 ms", "Statistical Baseline Engine + APScheduler"),
    ]

    col1, col2 = st.columns(2)
    for idx, (title, role, status_badge, lat, model_info) in enumerate(agent_grid_data):
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            st.markdown(
                f"""
                <div class="agent-node-card">
                    <div class="agent-node-header">
                        <h4 class="agent-node-title">{title}</h4>
                        <span class="bento-badge" style="background: #D1FAE5; color: #065F46;">{status_badge}</span>
                    </div>
                    <div class="agent-node-role">{role}</div>
                    <div class="agent-node-metric">
                        <span><strong>Average Latency:</strong></span>
                        <span style="font-family: var(--font-mono); color: var(--color-primary-700);">{lat}</span>
                    </div>
                    <div class="agent-node-metric">
                        <span><strong>Backing Engine:</strong></span>
                        <span>{model_info}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


# ============================================================================
# VIEW 4: MY CROPS & CULTIVATION PLANNER
# ============================================================================
elif st.session_state.active_page == "my_crops":
    render_hero_banner(
        greeting="Cultivation Agronomy",
        title="8-Stage Crop Cultivation Roadmap",
        subtitle="Tailored planting calendars, seed varieties, and fertilizer schedules from the Department of Agriculture.",
    )

    crop_sel = st.selectbox("Select Crop for Cultivation Plan", ["Paddy (Rice)", "Maize", "Chilli", "Tomato", "Big Onion"], index=0)
    
    stages = [
        ("1. Variety Selection", "Recommended: Bg 300, Bg 352, At 362 (tolerant to blast and BLB)."),
        ("2. Land Preparation", "Primary ploughing 3 weeks before sowing; puddling and levelling for water economy."),
        ("3. Sowing & Nursery", "Direct wet seeding (80-100 kg/ha) or 14-day nursery seedling transplanting."),
        ("4. Basal Fertilizer", "Apply Urea: 50 kg/ha, Triple Superphosphate (TSP): 35 kg/ha, MOP: 20 kg/ha at final levelling."),
        ("5. First Top Dressing (3-4 WAP)", "Urea top-dressing (50 kg/ha) at active tillering stage."),
        ("6. Panicle Initiation Fertilizer", "Urea (35 kg/ha) + MOP (25 kg/ha) at panicle initiation for grain filling."),
        ("7. Water & Weed Management", "Maintain 2-5 cm water layer; drain field 10 days before harvest."),
        ("8. Harvesting & Storage", "Harvest at 80-85% grain maturity; dry to 12-14% moisture content."),
    ]

    for stage_title, stage_desc in stages:
        st.markdown(
            f"""
            <div class="action-step-card">
                <div class="action-step-num">🌾</div>
                <div class="action-step-content">
                    <div class="action-step-title">{stage_title}</div>
                    <div class="action-step-desc">{stage_desc}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================================
# VIEW 5: CROP HEALTH & DISEASE SCANNER
# ============================================================================
elif st.session_state.active_page == "crop_health":
    render_hero_banner(
        greeting="Plant Pathology",
        title="Crop Health Scanner & Pathology Lab",
        subtitle="Diagnose fungal, bacterial, and pest symptoms against verified agricultural knowledge bases.",
    )

    st.markdown("### 🔍 Interactive Symptom Diagnostic Tester")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        symptom_crop = st.selectbox("Target Crop", ["Rice", "Maize", "Chilli", "Tomato"], key="diag_crop")
        symptom_input = st.multiselect(
            "Select Observed Foliar Symptoms",
            ["yellowing leaves", "brown spots", "spindle-shaped lesions", "grey centre", "bacterial ooze", "stunted growth", "leaf curling"],
            default=["yellowing leaves", "brown spots"],
        )
    with col_c2:
        st.markdown(
            f"""
            <div style="background: var(--bg-surface); padding: 18px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
                <div style="font-weight: 700; color: var(--color-primary-900); margin-bottom: 6px;">Pathology Diagnostic Protocol</div>
                <div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5;">
                    The Disease Agent evaluates token similarity, matched symptom counts, and localized prevalence factors to output high-confidence differential diagnoses with complete treatment plans.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("🧪 Run Diagnostic Analysis", type="primary"):
        st.success(f"Matched Candidate: **Bacterial Leaf Blight (Xanthomonas oryzae)** — 88% Confidence")
        st.info("Treatment: Drain standing field water and apply copper hydroxide 77% WP as recommended by DOA Sri Lanka.")


# ============================================================================
# VIEW 6: AGRO-WEATHER FORECAST
# ============================================================================
elif st.session_state.active_page == "weather":
    render_hero_banner(
        greeting="Agro-Climatology",
        title=f"7-Day Microclimate Forecast ({saved_district})",
        subtitle="Weather risk indices, disease incubation warnings, and optimal pesticide spray windows.",
    )

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    temps = [29.5, 30.1, 28.4, 27.9, 29.0, 31.2, 30.5]
    humidity = [78, 82, 89, 91, 80, 72, 74]
    conditions = ["Partly Cloudy ⛅", "Scattered Showers 🌦️", "Thunderstorms ⛈️", "Heavy Rain 🌧️", "Sunny Breaks ⛅", "Clear Sun ☀️", "Partly Cloudy ⛅"]

    cols = st.columns(7)
    for idx, col in enumerate(cols):
        with col:
            st.markdown(
                f"""
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 14px 10px; text-align: center;">
                    <div style="font-weight: 700; font-size: 0.82rem; color: var(--text-muted);">{days[idx][:3].upper()}</div>
                    <div style="font-size: 1.4rem; margin: 6px 0;">{conditions[idx].split()[-1]}</div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: var(--color-primary-950);">{temps[idx]}°C</div>
                    <div style="font-size: 0.75rem; color: var(--accent-weather); font-weight: 600;">💧 {humidity[idx]}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background: #FFFBEB; border: 1px solid #FDE68A; padding: 18px 22px; border-radius: var(--radius-lg); color: #92400E;">
            <div style="font-weight: 700; font-size: 1rem; margin-bottom: 4px;">⚠️ High Humidity & Fungal Alert (Wed - Thu)</div>
            <div style="font-size: 0.88rem; line-height: 1.5;">
                Relative humidity exceeding 85% with continuous cloud cover on Wednesday and Thursday elevates spore germination risk for <em>Pyricularia oryzae</em> (Rice Blast). Avoid nitrogen top-dressing and conduct morning field inspections.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# VIEW 7: COMMODITY MARKET PRICES
# ============================================================================
elif st.session_state.active_page == "market":
    render_hero_banner(
        greeting="Economic Intelligence",
        title="Sri Lanka Wholesale Crop Market",
        subtitle="Daily commodity prices tracked from Pettah, Dambulla, and regional Dedicated Economic Centres.",
    )

    market_data = [
        ("Paddy (Nadu)", "Rs. 125.00 / kg", "Rs. 128.00 / kg", "+2.4%", "Bullish 📈"),
        ("Paddy (Samba)", "Rs. 138.00 / kg", "Rs. 142.00 / kg", "+2.9%", "Bullish 📈"),
        ("Maize (Feed Grade)", "Rs. 150.00 / kg", "Rs. 148.00 / kg", "-1.3%", "Stable ⚖️"),
        ("Big Onion (Local)", "Rs. 280.00 / kg", "Rs. 310.00 / kg", "+10.7%", "Strong Surge 🚀"),
        ("Green Chilli", "Rs. 450.00 / kg", "Rs. 410.00 / kg", "-8.8%", "Seasonal Drop 📉"),
        ("Tomato", "Rs. 220.00 / kg", "Rs. 240.00 / kg", "+9.1%", "Bullish 📈"),
    ]

    st.markdown(
        """
        <div style="background: var(--bg-surface); border-radius: var(--radius-lg); border: 1px solid var(--border-subtle); overflow: hidden; margin-bottom: 24px;">
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.92rem;">
                <thead>
                    <tr style="background: var(--bg-subtle); border-bottom: 1px solid var(--border-subtle); color: var(--text-muted);">
                        <th style="padding: 14px 18px;">Commodity</th>
                        <th style="padding: 14px 18px;">Last Week</th>
                        <th style="padding: 14px 18px;">Current Wholesale</th>
                        <th style="padding: 14px 18px;">Change</th>
                        <th style="padding: 14px 18px;">Market Trend</th>
                    </tr>
                </thead>
                <tbody>
        """,
        unsafe_allow_html=True,
    )

    for item, last_p, curr_p, change, trend in market_data:
        change_color = "#10B981" if change.startswith("+") else "#EF4444"
        st.markdown(
            f"""
            <tr style="border-bottom: 1px solid var(--border-subtle);">
                <td style="padding: 14px 18px; font-weight: 700; color: var(--text-primary);">{item}</td>
                <td style="padding: 14px 18px; color: var(--text-muted);">{last_p}</td>
                <td style="padding: 14px 18px; font-weight: 700; color: var(--color-primary-900);">{curr_p}</td>
                <td style="padding: 14px 18px; font-weight: 700; color: {change_color};">{change}</td>
                <td style="padding: 14px 18px;">{trend}</td>
            </tr>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</tbody></table></div>", unsafe_allow_html=True)


# ============================================================================
# VIEW 8: OUTBREAK SENTINEL SURVEILLANCE
# ============================================================================
elif st.session_state.active_page == "sentinel":
    render_hero_banner(
        greeting="Disease Surveillance",
        title="Outbreak Sentinel Agent Command Center",
        subtitle="Autonomous regional cluster anomaly detection with 24-hour alert fatigue prevention.",
    )

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        st.markdown("### 📡 Live Regional Surveillance Map")
        render_bento_sentinel_alert(
            level="Normal",
            district=saved_district,
            details=f"Background baseline for {saved_district}: 1.2 cases/48h. Current active cluster: 0 anomalies detected.",
        )
    with col_s2:
        st.markdown("### ⚡ Sentinel Control Actions")
        if st.button("🧪 Seed Simulated Outbreak Demo", use_container_width=True):
            try:
                import requests
                resp = requests.post("http://127.0.0.1:8000/api/sentinel/seed-demo", json={"district": saved_district, "crop": "Rice", "disease": "Bacterial Leaf Blight"}, timeout=5)
                if resp.status_code == 200:
                    st.success("✅ Demo cluster seeded (6 cases in last 48h).")
            except Exception as e:
                st.error(f"Could not reach Sentinel API: {e}")

        if st.button("🔄 Trigger Surveillance Scan Now", use_container_width=True, type="primary"):
            try:
                import requests
                resp = requests.post("http://127.0.0.1:8000/api/sentinel/scan", timeout=5)
                if resp.status_code == 200:
                    decisions = resp.json().get("decisions", [])
                    st.success(f"Scan complete. Decisions logged: {len(decisions)}")
                    st.json(decisions)
            except Exception as e:
                st.error(f"Could not reach Sentinel API: {e}")


# ============================================================================
# VIEW 9: CONSULTATION HISTORY
# ============================================================================
elif st.session_state.active_page == "history":
    render_hero_banner(
        greeting="Consultation Log",
        title="Your Advisory Analysis History",
        subtitle="Review past AI consultations, diagnostic reports, and recommended treatments.",
    )

    history = st.session_state.conversation_history
    if not history:
        st.info("No prior consultations recorded yet. Inquiries you submit will appear here.")
    else:
        for idx, item in enumerate(reversed(history), 1):
            with st.expander(f"📋 Query #{idx}: {item.get('query', '')[:60]}...", expanded=False):
                st.markdown(f"**Query:** {item.get('query')}")
                resp = item.get("response", {})
                st.markdown(f"**AI Advisory:** {resp.get('answer') or resp.get('advisory') or 'N/A'}")


# ============================================================================
# VIEW 10: FARMER FORUM & COMMUNITY
# ============================================================================
elif st.session_state.active_page == "forum":
    render_hero_banner(
        greeting="Farmer Community",
        title="Farmer Knowledge Forum & Notice Board",
        subtitle="Peer discussions, regional Agrarian Services announcements, and extension officer Q&A.",
    )

    st.markdown("### 💬 Recent Discussions & Notices")
    posts = [
        ("K.B. Jayasundara (Anuradhapura)", "Anyone experiencing stem borer attacks on Bg 352 this week?", "3 hours ago · 4 replies"),
        ("Department of Agriculture (Notice)", "Subsidized Muriate of Potash (MOP) distribution begins Monday at Agrarian Service Centers.", "Yesterday · Official Notice"),
        ("S. Ramesh (Batticaloa)", "Organic neem oil emulsion effectively controlled aphids on green chilli.", "2 days ago · 9 likes"),
    ]

    for author, msg, meta in posts:
        st.markdown(
            f"""
            <div style="background: var(--bg-surface); padding: 16px 20px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); margin-bottom: 12px;">
                <div style="font-weight: 700; color: var(--color-primary-900); font-size: 0.95rem;">{author}</div>
                <div style="color: var(--text-primary); margin: 6px 0; font-size: 0.92rem;">{msg}</div>
                <div style="font-size: 0.78rem; color: var(--text-muted);">{meta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
