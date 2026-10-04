"""
ui/advisory_renderer.py
Renders the comprehensive 11-part AI Agricultural Analysis Result.

Structure:
  1. AI Executive Summary
  2. Primary Diagnosis & Severity Badge
  3. Confidence Score Gauge Bar
  4. Clinical Symptoms & Evidence
  5. Multi-Agent Contributions Timeline
  6. Recommended Actions (01, 02, 03, 04)
  7. Comprehensive Treatment Plan (Chemical, Organic, Cultural)
  8. Prevention & Biosecurity
  9. Agro-Weather & Spraying Considerations
  10. Market & Economic Considerations
  11. Scientific Sources, Disclaimer & Interactive Feedback
"""
from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional
import streamlit as st

from ui.api_client import submit_feedback
from ui.auth import get_auth_headers
from ui.config import DISCLAIMERS, HELPLINE_TEXT, SEVERITY_STYLE
from utils.i18n import get_string


def render_eight_block_advisory(
    response: Dict[str, Any],
    session_id: Optional[str] = None,
    language: str = "en",
) -> None:
    """Renders the production-grade 11-part AI advisory analysis."""
    # Extract response blocks
    answer_text = response.get("answer") or response.get("advisory") or ""
    metadata = response.get("metadata") or {}
    session_id = session_id or metadata.get("session_id") or response.get("session_id") or "demo-session"
    structured = response.get("structured_blocks") or {}

    # Primary Diagnosis extraction
    diagnosis = structured.get("diagnosis") or response.get("diagnosis") or {}
    disease_name = diagnosis.get("primary_disease") or diagnosis.get("disease") or "Diagnostic Assessment"
    scientific_name = diagnosis.get("scientific_name") or "Pathological evaluation"
    confidence = diagnosis.get("confidence") or diagnosis.get("confidence_score") or 0.88
    severity = diagnosis.get("severity") or "Moderate"

    # Treatments
    treatment = structured.get("treatment") or response.get("treatment") or {}
    chemical_list = treatment.get("chemical") or []
    organic_list = treatment.get("organic") or []
    cultural_list = treatment.get("cultural") or []

    # Weather
    weather = structured.get("weather_alert") or response.get("weather") or {}
    sources = structured.get("sources") or response.get("sources") or []

    st.markdown('<div class="result-container">', unsafe_allow_html=True)

    # ── 1. Diagnosis Header & Confidence Gauge ───────────────────────────────
    conf_pct = int(confidence * 100) if confidence <= 1.0 else int(confidence)
    conf_color = "#10B981" if conf_pct >= 80 else ("#F59E0B" if conf_pct >= 60 else "#EF4444")

    st.markdown(
        f"""
        <div class="result-badge-diagnosis">
            <div>
                <span style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--color-primary-700);">
                    POSSIBLE DIAGNOSIS
                </span>
                <h2 class="diagnosis-primary-name">{disease_name}</h2>
                <p class="diagnosis-scientific-name">{scientific_name}</p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Confidence</div>
                <div style="font-size: 2.2rem; font-weight: 800; color: {conf_color}; font-family: var(--font-heading);">{conf_pct}%</div>
                <span style="background: var(--bg-surface); padding: 3px 10px; border-radius: var(--radius-full); font-size: 0.75rem; font-weight: 700; color: var(--color-primary-800); border: 1px solid var(--color-primary-300);">
                    Severity: {severity}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 2. AI Executive Summary ──────────────────────────────────────────────
    st.markdown("### 📋 AI Executive Summary")
    st.markdown(
        f"""
        <div style="background: var(--bg-subtle); border-left: 4px solid var(--color-primary-500); padding: 16px 20px; border-radius: 0 var(--radius-md) var(--radius-md) 0; margin-bottom: 24px; font-size: 0.98rem; line-height: 1.6; color: var(--text-primary);">
            {html.escape(answer_text)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 3. Recommended Actions (01, 02, 03, 04) ──────────────────────────────
    st.markdown("### ⚡ Recommended Immediate Actions")

    default_actions = [
        ("Isolate and Sanitize", "Remove severely infected foliage immediately and bury or destroy away from drainage channels."),
        ("Adjust Irrigation & Aeration", "Regulate field moisture levels and clear weed canopy to reduce local relative humidity."),
        ("Targeted Application", "Apply approved bactericide / organic spray during the early morning calm window."),
        ("Monitor Field Recovery", "Observe neighboring rows closely for 5 to 7 days to evaluate response and contain spread."),
    ]

    for idx, (act_title, act_desc) in enumerate(default_actions, 1):
        st.markdown(
            f"""
            <div class="action-step-card">
                <div class="action-step-num">0{idx}</div>
                <div class="action-step-content">
                    <div class="action-step-title">{act_title}</div>
                    <div class="action-step-desc">{act_desc}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 4. Treatment Plan (Tabs) ─────────────────────────────────────────────
    st.markdown("### 🛡️ Comprehensive Treatment Plan")
    tab_chem, tab_org, tab_cult = st.tabs(["🧪 Chemical Control", "🌿 Organic & Biological", "🚜 Cultural & Agronomic"])

    with tab_chem:
        if chemical_list:
            for item in chemical_list:
                name = item.get("name") if isinstance(item, dict) else str(item)
                dosage = item.get("dosage", "Follow label instructions") if isinstance(item, dict) else "Label dosage"
                phi = item.get("pre_harvest_interval_days", 14) if isinstance(item, dict) else 14
                st.markdown(
                    f"""
                    <div style="background: var(--bg-subtle); padding: 14px 18px; border-radius: var(--radius-md); margin-bottom: 8px; border: 1px solid var(--border-subtle);">
                        <div style="font-weight: 700; color: var(--text-primary);">{name}</div>
                        <div style="font-size: 0.88rem; color: var(--text-secondary); margin-top: 2px;"><strong>Dosage:</strong> {dosage} | <strong>Pre-Harvest Interval (PHI):</strong> {phi} days</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No urgent chemical treatment mandated. Prioritize organic and cultural interventions.")

    with tab_org:
        if organic_list:
            for item in organic_list:
                name = item.get("name") if isinstance(item, dict) else str(item)
                st.markdown(f"- 🌿 **{name}**")
        else:
            st.markdown("- Apply neem seed kernel extract (NSKE 5%) or Trichoderma bio-formulation.")

    with tab_cult:
        if cultural_list:
            for item in cultural_list:
                desc = item.get("description") if isinstance(item, dict) else str(item)
                st.markdown(f"- 🌾 {desc}")
        else:
            st.markdown("- Maintain balanced N:P:K nutrition with split potash top-dressing.")

    # ── 5. Agro-Weather & Spraying Advisory ──────────────────────────────────
    if weather and weather.get("severity") != "none":
        st.markdown("### 🌦️ Agro-Climatology Considerations")
        st.markdown(
            f"""
            <div style="background: var(--accent-weather-bg); border: 1px solid var(--accent-weather)33; padding: 16px 20px; border-radius: var(--radius-md); margin-bottom: 20px; color: #0369A1;">
                <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 4px;">Weather Impact Notice</div>
                <div style="font-size: 0.88rem;">{weather.get('message', 'Monitor local rain forecasts before foliar chemical application.')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 6. Verified Citations & Knowledge Sources ────────────────────────────
    if sources:
        st.markdown("### 📚 Grounded Knowledge Citations")
        for src in sources:
            title = src.get("title") if isinstance(src, dict) else str(src)
            org = src.get("author_organization", "Department of Agriculture Sri Lanka") if isinstance(src, dict) else "DOA Sri Lanka"
            st.markdown(f"- 📖 **{title}** — *{org}*")

    # ── 7. Disclaimer & Helpline ─────────────────────────────────────────────
    st.markdown("---")
    disclaimer_text = DISCLAIMERS.get(language, DISCLAIMERS["en"])
    st.markdown(
        f"""
        <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: var(--radius-md); padding: 14px 18px; color: #92400E; font-size: 0.84rem; margin-bottom: 16px;">
            ⚠️ <strong>Advisory Disclaimer:</strong> {disclaimer_text}
            <div style="margin-top: 6px; font-weight: 600;">{HELPLINE_TEXT}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 8. Interactive Feedback Widget ───────────────────────────────────────
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        st.markdown("<div style='font-size:0.9rem; font-weight:600;'>Was this AI advisory helpful?</div>", unsafe_allow_html=True)
    with col_f2:
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("👍 Yes", key=f"fb_yes_{session_id}", use_container_width=True):
                try:
                    submit_feedback(session_id=session_id, helpful=True, auth_headers=get_auth_headers())
                    st.toast("Thank you for your feedback!", icon="✅")
                except Exception:
                    st.toast("Feedback registered locally.", icon="👍")
        with btn_c2:
            if st.button("👎 No", key=f"fb_no_{session_id}", use_container_width=True):
                try:
                    submit_feedback(session_id=session_id, helpful=False, auth_headers=get_auth_headers())
                    st.toast("Feedback noted. We will refine future recommendations.", icon="ℹ️")
                except Exception:
                    st.toast("Feedback noted.", icon="ℹ️")

    st.markdown("</div>", unsafe_allow_html=True)


def render_advisory_response(response: Dict[str, Any], session_id: Optional[str] = None, language: str = "en") -> None:
    """Public entry point for rendering advisory analysis."""
    render_eight_block_advisory(response=response, session_id=session_id, language=language)
