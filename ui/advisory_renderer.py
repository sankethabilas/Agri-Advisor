"""
ui/advisory_renderer.py
Task T-12 — Advisory Response Rendering in the UI  (Day 3, Agri-Advisor)
Task T-17 — Language Selection & Multi-Language Scaffolding

Renders the eight-block structured advisory layout from an orchestrator
response payload.  All keys are accessed via .get() so that missing
optional blocks never crash the UI.

T-17 additions:
    render_eight_block_advisory now accepts a ``lang`` argument.  When lang
    is not "en", advisory text blocks are translated at render-time via
    utils.translator.translate_advisory_text.  The stored response dict is
    never mutated (pipeline always stays in English, per T-17.4).

Entry point:
    render_eight_block_advisory(response: dict, is_fallback: bool = False, lang: str = "en")

Block map:
    B1  — Diagnosis          (disease_name, scientific_name, severity, confidence)
    B2  — Immediate Treatment (steps with urgency_tags)
    B3  — Prevention          (bulleted long-term guidelines)
    B4  — Weather Advisory    (risk level, action window, colored cards)
    B5  — Sources             (cited publications, sorted by confidence)
    B6  — Disclaimer          (AI notice + helpline)
    B7  — "Why?" Explanation  (expandable AI reasoning context)
    B8  — Partial-response guard (all blocks use .get() / are skipped when absent)

Fixture wire-up:
    The renderer accepts any dict matching the schema defined in
    /tests/fixtures/orchestrator_response.json
"""
from __future__ import annotations
from ui.config import DISCLAIMERS, HELPLINE_TEXT, SEVERITY_STYLE
from ui.auth import clear_auth, get_auth_headers
from ui.api_client import _ApiError, submit_feedback

import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

# Allow utils.* imports when this module is loaded from any entry point
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# T-17: translation helpers (imported lazily in _translate_advisory_block)
# to avoid hard-failing when the utils package is not yet on sys.path in tests
try:
    from utils.translator import translate_advisory_text, TranslationResult  # noqa: F401
    _TRANSLATOR_AVAILABLE = True
except ImportError:
    _TRANSLATOR_AVAILABLE = False

# ============================================================================
# T-17 Translation helper
# ============================================================================


def _translate_block_text(
    text: str,
    lang: str,
    technical_terms: list[str] | None = None,
) -> tuple[str, bool]:
    """
    Translate a single advisory text string at render-time (T-17.3 / T-17.4).

    Returns (translated_text, had_warning) where ``had_warning`` is True
    when the translation API failed and the original English text was returned
    (T-17.7 graceful fallback).

    If ``lang`` is "en" or the translator is not available, the original text
    is returned immediately with no warning.
    """
    if lang == "en" or not text.strip():
        return text, False

    if not _TRANSLATOR_AVAILABLE:
        return text, True  # signal warning so caller can toast once

    result = translate_advisory_text(text, lang, technical_terms)
    return result.text, not result.success


# ============================================================================
# § Internal helpers
# ============================================================================

def _safe_str(value: Any, default: str = "") -> str:
    """Return str(value) or default when value is None/empty."""
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _translate_value(value: Any, lang: str, technical_terms: list[str]) -> tuple[Any, bool]:
    """Translate one narrative value without changing structural fields."""
    if not isinstance(value, str) or not value.strip() or lang == "en":
        return value, False
    return _translate_block_text(value, lang, technical_terms)


def _format_iso(iso_str: str) -> str:
    """Convert ISO-8601 timestamp to a human-readable string."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%a %d %b %Y, %I:%M %p %Z")
    except (ValueError, AttributeError):
        return iso_str


def _severity_badge_html(severity: str) -> str:
    """Return an inline HTML severity badge."""
    s = SEVERITY_STYLE.get(severity.lower(), SEVERITY_STYLE["none"])
    weight = "700" if s["bold"] else "500"
    return (
        f'<span style="background:{s["bg"]};color:{s["color"]};'
        f'font-weight:{weight};padding:3px 12px;border-radius:14px;'
        f'font-size:0.82rem;letter-spacing:0.3px;">{s["label"]}</span>'
    )


def _diagnosis_severity_badge(severity: str) -> str:
    """Return an inline HTML badge for diagnosis severity (Low/Moderate/High/Critical)."""
    mapping = {
        "low":      ("#166534", "#DCFCE7"),
        "moderate": ("#92400E", "#FEF3C7"),
        "high":     ("#9A3412", "#FED7AA"),
        "critical": ("#FFFFFF", "#DC2626"),
    }
    color, bg = mapping.get(severity.lower(), ("#374151", "#F3F4F6"))
    return (
        f'<span style="background:{bg};color:{color};font-weight:700;'
        f'padding:3px 12px;border-radius:14px;font-size:0.82rem;">'
        f'{severity.capitalize()}</span>'
    )


def _urgency_badge_html(tag: str) -> str:
    """Return an urgency badge HTML for treatment steps."""
    tag_lower = tag.lower().strip()
    styles: dict[str, tuple[str, str]] = {
        "immediate action": ("#9A3412", "#FEE2E2"),
        "high priority":    ("#92400E", "#FEF3C7"),
        "recommended":      ("#166534", "#DCFCE7"),
        "optional":         ("#374151", "#F3F4F6"),
    }
    color, bg = styles.get(tag_lower, ("#374151", "#F3F4F6"))
    return (
        f'<span style="background:{bg};color:{color};font-weight:600;'
        f'font-size:0.75rem;padding:2px 8px;border-radius:10px;'
        f'white-space:nowrap;">{tag}</span>'
    )


def _confidence_bar(confidence: float, label: str = "") -> None:
    """Render a styled progress bar + percentage for confidence score."""
    pct = round(confidence * 100)
    # Color ramp: low → amber, medium → green, high → deep green
    if pct >= 85:
        bar_color = "#16A34A"
    elif pct >= 60:
        bar_color = "#D97706"
    else:
        bar_color = "#DC2626"

    caption = label or f"{pct}% confidence"
    st.markdown(
        f"""
        <div style="margin:6px 0 12px 0;">
          <div style="display:flex;justify-content:space-between;
                      font-size:0.82rem;color:#6B7280;margin-bottom:4px;">
            <span>{caption}</span>
            <span style="font-weight:700;color:{bar_color};">{pct}%</span>
          </div>
          <div style="background:#E5E7EB;border-radius:6px;height:10px;overflow:hidden;">
            <div style="width:{pct}%;background:{bar_color};
                        height:100%;border-radius:6px;
                        transition:width 0.6s ease;"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _block_header(icon: str, title: str, subtitle: str = "") -> None:
    """Render a consistent block section header."""
    sub_html = (
        f'<p style="margin:2px 0 0 0;font-size:0.88rem;color:#6B7280;">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(
        f"""
        <div style="margin:24px 0 10px 0;border-left:4px solid #16A34A;
                    padding-left:12px;">
          <h3 style="margin:0;font-size:1.15rem;color:#14532D;font-weight:700;">
            {icon}&nbsp;{title}
          </h3>
          {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# § Block 1 — Diagnosis
# ============================================================================

def render_block1_diagnosis(diagnosis: dict[str, Any]) -> None:
    """
    Block 1: Disease Diagnosis card.
    Renders disease name, scientific name, severity badge, and confidence bar.
    Gracefully omitted when `diagnosis` dict is absent or empty.
    """
    if not diagnosis:
        return

    disease_name = _safe_str(diagnosis.get("disease_name"), "Unknown Disease")
    scientific_name = _safe_str(diagnosis.get("scientific_name"))
    severity = _safe_str(diagnosis.get("severity"), "Unknown")
    confidence = float(diagnosis.get("confidence") or 0.0)
    conf_label = _safe_str(diagnosis.get("confidence_label"), "")
    symptoms = diagnosis.get("symptoms_confirmed") or []
    differentials = diagnosis.get("differential_diagnoses") or []

    _block_header("🔬", "Block 1 — Disease Diagnosis")

    sev_badge = _diagnosis_severity_badge(severity)
    sci_html = (
        f'<em style="color:#6B7280;font-size:0.9rem;">({scientific_name})</em>'
        if scientific_name else ""
    )

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#F0FDF4,#DCFCE7);
                    border:1px solid #BBF7D0;border-radius:12px;
                    padding:20px 24px;margin-bottom:8px;">
          <div style="font-size:1.4rem;font-weight:800;color:#14532D;margin-bottom:4px;">
            {disease_name}&nbsp;&nbsp;{sci_html}
          </div>
          <div style="margin:8px 0;">
            <span style="font-size:0.88rem;color:#374151;margin-right:10px;">
              Severity:
            </span>
            {sev_badge}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Confidence progress bar
    bar_label = (
        f"Diagnosis confidence — {conf_label}" if conf_label
        else "Diagnosis confidence"
    )
    _confidence_bar(confidence, bar_label)

    # Confirmed symptoms
    if symptoms:
        with st.expander("✅ Confirmed Symptoms", expanded=False):
            for sym in symptoms:
                st.markdown(f"- {sym}")

    # Differential diagnoses
    if differentials:
        with st.expander("🔍 Differential Diagnoses Considered", expanded=False):
            for diff in differentials:
                d_name = _safe_str(diff.get("disease"), "Unknown")
                d_conf = float(diff.get("confidence") or 0.0)
                d_factor = _safe_str(diff.get("distinguishing_factor"))
                d_pct = round(d_conf * 100)
                st.markdown(
                    f'**{d_name}** — <span style="color:#6B7280;">{d_pct}% confidence</span>',
                    unsafe_allow_html=True,
                )
                if d_factor:
                    st.markdown(
                        f'<p style="font-size:0.87rem;color:#374151;margin:2px 0 10px 12px;">'
                        f'ℹ️ {d_factor}</p>',
                        unsafe_allow_html=True,
                    )


# ============================================================================
# § Block 2 — Immediate Treatment
# ============================================================================

def render_block2_immediate_treatment(immediate_treatment: dict[str, Any]) -> None:
    """
    Block 2: Immediate Treatment numbered list with urgency badges.
    Gracefully omitted when `immediate_treatment` dict is absent or has no steps.
    """
    if not immediate_treatment:
        return

    steps = immediate_treatment.get("steps") or []
    urgency = _safe_str(immediate_treatment.get("urgency"), "")
    action_win = _safe_str(immediate_treatment.get("action_window"), "")

    if not steps:
        return

    subtitle = " · ".join(filter(None, [urgency, action_win]))
    _block_header("💊", "Block 2 — Immediate Treatment", subtitle)

    for step in steps:
        priority = step.get("priority", "—")
        action = _safe_str(step.get("action"), "Action")
        detail = _safe_str(step.get("detail"))
        urgency_tag = _safe_str(step.get("urgency_tag"), "")

        badge_html = _urgency_badge_html(urgency_tag) if urgency_tag else ""

        st.markdown(
            f"""
            <div style="display:flex;align-items:flex-start;gap:14px;
                        padding:14px 18px;margin-bottom:10px;
                        background:#FFFFFF;border:1px solid #D1FAE5;
                        border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
              <div style="background:#14532D;color:#FFFFFF;font-weight:800;
                          font-size:1rem;min-width:32px;height:32px;
                          border-radius:50%;display:flex;align-items:center;
                          justify-content:center;flex-shrink:0;">{priority}</div>
              <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;
                            margin-bottom:4px;">
                  <span style="font-weight:700;color:#14532D;font-size:0.97rem;">
                    {action}
                  </span>
                  {badge_html}
                </div>
                <p style="margin:0;font-size:0.91rem;color:#374151;line-height:1.55;">
                  {detail}
                </p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================================
# § Block 3 — Prevention
# ============================================================================

def render_block3_prevention(prevention: list[str]) -> None:
    """
    Block 3: Long-term prevention guidelines as a styled bulleted list.
    Gracefully omitted when `prevention` list is absent or empty.
    """
    if not prevention:
        return

    _block_header("🛡️", "Block 3 — Prevention Guidelines",
                  "Long-term measures to prevent recurrence")

    items_html = "".join(
        f"""
        <li style="padding:6px 0;color:#1F2937;font-size:0.95rem;line-height:1.55;">
          <span style="color:#16A34A;font-weight:700;margin-right:6px;">✓</span>
          {item}
        </li>
        """
        for item in prevention
    )

    st.markdown(
        f"""
        <div style="background:#F0FDF4;border:1px solid #BBF7D0;
                    border-radius:10px;padding:16px 20px;">
          <ul style="list-style:none;margin:0;padding:0;">
            {items_html}
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# § Block 4 — Weather Advisory
# ============================================================================

def render_block4_weather_advisory(weather_alert: dict[str, Any]) -> None:
    """
    Block 4: Weather Advisory with colored risk cards and action window.
    Gracefully omitted when severity == 'none' or block is absent.
    """
    if not weather_alert:
        return

    severity = _safe_str(weather_alert.get("severity"), "none").lower()
    if severity == "none":
        return

    s = SEVERITY_STYLE.get(severity, SEVERITY_STYLE["none"])
    title = _safe_str(weather_alert.get("title"), "Weather Alert")
    message = _safe_str(weather_alert.get("message"))
    impact_warning = _safe_str(weather_alert.get("impact_warning"))
    action_window = _safe_str(weather_alert.get("action_window"))
    risk_level = _safe_str(weather_alert.get("risk_level"))
    risk_score_raw = weather_alert.get("disease_risk_score")
    valid_until_raw = _safe_str(weather_alert.get("valid_until"))
    valid_until = _format_iso(valid_until_raw) if valid_until_raw else ""

    _block_header("🌦️", "Block 4 — Weather Advisory")

    badge_html = _severity_badge_html(severity)

    # Risk score metric strip
    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric("⚠️ Risk Level", risk_level or severity.capitalize())
    with metric_cols[1]:
        if risk_score_raw is not None:
            score_pct = round(float(risk_score_raw) * 100)
            st.metric("🦠 Disease Risk Score", f"{score_pct}%")
    with metric_cols[2]:
        if valid_until:
            st.metric("🕐 Alert Valid Until", valid_until)

    # Main alert card
    impact_block = (
        f"""
        <div style="margin-top:12px;padding:10px 14px;
                    background:{s['bg']};border-radius:8px;">
          <span style="font-weight:700;color:{s['color']};font-size:0.9rem;">
            ⚠️&nbsp;{impact_warning}
          </span>
        </div>
        """
        if impact_warning else ""
    )

    action_block = (
        f"""
        <div style="margin-top:10px;padding:8px 14px;
                    background:#F0FDF4;border-radius:8px;
                    border-left:3px solid #16A34A;">
          <span style="font-size:0.88rem;color:#166534;">
            📅&nbsp;<strong>Action Window:</strong>&nbsp;{action_window}
          </span>
        </div>
        """
        if action_window else ""
    )

    st.markdown(
        f"""
        <div style="border-left:5px solid {s['bg']};background:#FAFAFA;
                    padding:18px 22px;border-radius:10px;margin-top:4px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.06);">
          <div style="margin-bottom:8px;">
            {badge_html}&nbsp;&nbsp;
            <strong style="font-size:1.05rem;color:#1F2937;">{title}</strong>
          </div>
          <p style="margin:4px 0;color:#374151;font-size:0.95rem;">{message}</p>
          {impact_block}
          {action_block}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# § Block 5 — Sources
# ============================================================================

def render_block5_sources(sources: list[dict[str, Any]]) -> None:
    """
    Block 5: Knowledge sources list sorted by confidence_score.
    Gracefully omitted when `sources` list is absent or empty.
    """
    if not sources:
        return

    sorted_sources = sorted(
        sources,
        key=lambda s: float(s.get("confidence_score") or 0.0),
        reverse=True,
    )

    _block_header("📚", "Block 5 — Knowledge Sources",
                  f"{len(sorted_sources)} reference(s) used — sorted by relevance")

    with st.expander("View Sources", expanded=False):
        for i, src in enumerate(sorted_sources, 1):
            title = _safe_str(src.get("title"), "Unknown Source")
            org = _safe_str(src.get("author_organization"))
            section = _safe_str(src.get("section"))
            url = src.get("reference_url")
            score = float(src.get("confidence_score") or 0.0)
            score_pct = round(score * 100)

            title_html = (
                f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
                f'style="color:#1D4ED8;text-decoration:none;font-weight:600;">'
                f'{title}</a>'
                if url else f'<span style="font-weight:600;">{title}</span>'
            )
            section_html = (
                f'<span style="color:#6B7280;font-size:0.82rem;"> — {section}</span>'
                if section else ""
            )
            org_html = (
                f'<div style="color:#6B7280;font-size:0.83rem;margin-top:2px;">'
                f'🏛 {org}</div>'
                if org else ""
            )

            st.markdown(
                f"""
                <div style="padding:12px 16px;margin-bottom:10px;background:#FFFFFF;
                            border:1px solid #E5E7EB;border-radius:8px;">
                  <div style="display:flex;justify-content:space-between;
                              align-items:flex-start;flex-wrap:wrap;gap:6px;">
                    <div style="flex:1;">
                      <span style="color:#6B7280;font-size:0.8rem;margin-right:6px;">
                        [{i}]
                      </span>
                      {title_html}{section_html}
                      {org_html}
                    </div>
                    <div style="background:#DCFCE7;color:#166534;font-weight:700;
                                font-size:0.8rem;padding:3px 10px;border-radius:10px;
                                white-space:nowrap;">{score_pct}% match</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================================
# § Block 6 — Disclaimer & Helpline
# ============================================================================

def render_block6_disclaimer(
    disclaimer: dict[str, Any] | None,
    language: str = "en",
) -> None:
    """
    Block 6: AI disclaimer notice with helpline contact.
    Uses the structured `disclaimer` dict from the response when present,
    otherwise falls back to the config-level DISCLAIMERS lookup.
    """
    _block_header("ℹ️", "Block 6 — Disclaimer & Helpline")

    if disclaimer:
        text = _safe_str(disclaimer.get("text"),
                         DISCLAIMERS.get(language, DISCLAIMERS["en"]))
        helpline = _safe_str(disclaimer.get("helpline"), "")
        website = _safe_str(disclaimer.get("website"), "")
    else:
        text = DISCLAIMERS.get(language, DISCLAIMERS["en"])
        helpline = ""
        website = ""

    helpline_html = (
        f'<div style="margin-top:10px;font-size:0.9rem;color:#374151;">'
        f'☎️&nbsp;<strong>{helpline}</strong>'
        f'{"&nbsp;&nbsp;|&nbsp;&nbsp;🌐&nbsp;" + website if website else ""}'
        f'</div>'
        if helpline else f'<div style="margin-top:10px;font-size:0.9rem;">{HELPLINE_TEXT}</div>'
    )

    st.markdown(
        f"""
        <div style="background:#EFF6FF;border:1px solid #BFDBFE;
                    border-radius:10px;padding:16px 20px;">
          <p style="margin:0 0 4px 0;font-size:0.93rem;color:#1E3A5F;
                    line-height:1.6;">
            {text}
          </p>
          {helpline_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# § Block 7 — "Why?" Explanation Control
# ============================================================================

def render_block7_why_explanation(why_explanation: dict[str, Any]) -> None:
    """
    Block 7: Expandable 'Why did the AI recommend this?' control.
    Uses st.expander as the toggle mechanism.
    Gracefully omitted when `why_explanation` dict is absent or empty.
    """
    if not why_explanation:
        return

    _block_header("🤔", "Block 7 — Why This Advisory?",
                  "AI reasoning & confidence breakdown")

    summary = _safe_str(why_explanation.get("summary"))
    model_reasoning = _safe_str(why_explanation.get("model_reasoning"))
    agents_used = why_explanation.get("agents_used") or []
    conf_breakdown = why_explanation.get("confidence_breakdown") or {}

    friendly_agents: dict[str, str] = {
        "disease_agent": "🔬 Disease Identification",
        "weather_agent": "🌦 Weather Advisory",
        "rag_agent":     "📚 Knowledge Base (RAG)",
    }

    with st.expander("🔎 Why did Agri-Advisor give this recommendation?", expanded=False):
        if summary:
            st.markdown(
                f'<p style="color:#1F2937;font-size:0.95rem;line-height:1.65;'
                f'margin-bottom:12px;">{summary}</p>',
                unsafe_allow_html=True,
            )

        if model_reasoning:
            st.markdown("**🤖 Model Reasoning:**")
            st.markdown(
                f'<div style="background:#F9FAFB;border-left:3px solid #6B7280;'
                f'padding:10px 14px;border-radius:0 6px 6px 0;'
                f'font-size:0.88rem;color:#374151;line-height:1.6;">'
                f'{model_reasoning}</div>',
                unsafe_allow_html=True,
            )

        if conf_breakdown:
            st.markdown("**📊 Confidence by Agent:**")
            for agent_key, score in conf_breakdown.items():
                label = friendly_agents.get(
                    agent_key, agent_key.replace("_", " ").title())
                _confidence_bar(float(score), label)

        if agents_used:
            names = [friendly_agents.get(a, a) for a in agents_used]
            st.markdown(
                f'<p style="font-size:0.83rem;color:#6B7280;margin-top:8px;">'
                f'Systems consulted: {" · ".join(names)}</p>',
                unsafe_allow_html=True,
            )


# ============================================================================
# § Block 8 — Partial-Response Fallback / Raw Answer
# ============================================================================

def render_block8_raw_answer_fallback(answer: str) -> None:
    """
    Block 8: Partial-response safety net.
    Renders the raw markdown `answer` field when structured blocks are
    absent — ensuring the farmer always sees useful output even if the
    orchestrator returned a minimal response.
    """
    if not answer:
        return

    _block_header("📋", "Advisory Response",
                  "Structured blocks not available — showing full AI response")
    st.markdown(answer, unsafe_allow_html=True)


# ============================================================================
# § Orchestrator metadata ribbon
# ============================================================================

def _render_metadata_ribbon(metadata: dict[str, Any]) -> None:
    """Collapsed ribbon showing agents consulted and response latency."""
    agents = metadata.get("agents_consulted") or []
    latency = metadata.get("latency_ms")
    intent = _safe_str(metadata.get("intent"))

    if not (agents or latency or intent):
        return

    friendly_agents: dict[str, str] = {
        "disease_agent": "Disease Identification",
        "weather_agent": "Weather Advisory",
        "rag_agent":     "Knowledge Base",
    }
    with st.expander("🔍 Response Details", expanded=False):
        cols = st.columns(3)
        with cols[0]:
            if agents:
                names = [friendly_agents.get(a, a) for a in agents]
                st.markdown(f"**Systems:** {', '.join(names)}")
        with cols[1]:
            if intent:
                st.markdown(f"**Intent:** {intent.replace('_', ' ').title()}")
        with cols[2]:
            if latency:
                st.markdown(f"**Response Time:** {latency} ms")


# ============================================================================
# § Main 8-block renderer (public API)
# ============================================================================

def render_eight_block_advisory(
    response: dict[str, Any],
    is_fallback: bool = False,
    lang: str = "en",
) -> None:
    """
    Render the complete eight-block advisory layout.

    Accepts any dict matching /tests/fixtures/orchestrator_response.json.
    All blocks are guarded with .get() so that missing keys are silently
    skipped -- never raising a KeyError (Block 8 partial-response contract).

    Args:
        response:    Orchestrator response dict (may be partial).
        is_fallback: True when fixture data is being shown (offline mode).
        lang:        T-17 target locale code ("en", "si", "ta").
                     Advisory text blocks are translated at render-time.
                     The response dict is NEVER mutated.
    """
    # ── Demo mode banner ─────────────────────────────────────────────────────
    if is_fallback:
        st.warning(
            "⚠️ **Demo Mode** — The Agri-Advisor server is not running. "
            "Displaying sample advisory data so you can explore the interface.",
            icon="🔌",
        )

    if not response.get("diagnosis") and not response.get("immediate_treatment"):
        st.warning(
            "Some specialist agents did not return details. The available advisory "
            "information is shown below; ask a follow-up question for more detail.",
            icon="ℹ️",
        )

    # ── Extract top-level keys defensively (Block 8 guard) ───────────────────
    answer = _safe_str(response.get("answer"))
    diagnosis = response.get("diagnosis") or {}
    immediate_treatment = response.get("immediate_treatment") or {}
    prevention = response.get("prevention") or []
    weather_alert = response.get("weather_alert") or {}
    sources = response.get("sources") or []
    disclaimer = response.get("disclaimer")          # may be None
    why_explanation = response.get("why_explanation") or {}
    metadata = response.get("metadata") or {}
    language = _safe_str(metadata.get("language"), "en")
    session_id = metadata.get("session_id")

    # Detect whether the response is "structured" (has any Block 1–7 data)
    has_structured_blocks = any([diagnosis, immediate_treatment, prevention])

    # ── T-17: Build technical-term protection list ────────────────────────────
    _tech_terms: list[str] = []
    if diagnosis:
        if dn := diagnosis.get("disease_name"):
            _tech_terms.append(str(dn))
        if sn := diagnosis.get("scientific_name"):
            _tech_terms.append(str(sn))
    for step in (immediate_treatment.get("steps") or []):
        for k in ("chemical_name", "product"):
            if step.get(k):
                _tech_terms.append(str(step[k]))

    # T-17.7 sentinel: did any translation call degrade to fallback?
    _translation_warning = False

    # ── T-17.4: Translate narrative text fields at render-time ───────────────
    # Structural fields (severity, confidence, urgency_tag, source URLs) are
    # kept in English to preserve meaning and avoid mis-translation artefacts.

    # B3 Prevention: translate each item string / tip dict
    _translated_prevention: list = []
    for item in prevention:
        if isinstance(item, str):
            t, w = _translate_block_text(item, lang, _tech_terms)
            _translation_warning = _translation_warning or w
            _translated_prevention.append(t)
        elif isinstance(item, dict):
            tip_key = next(
                (k for k in ("tip", "text", "description") if item.get(k)), None
            )
            if tip_key:
                t, w = _translate_block_text(
                    str(item[tip_key]), lang, _tech_terms)
                _translation_warning = _translation_warning or w
                new_item = {**item, tip_key: t}
                _translated_prevention.append(new_item)
            else:
                _translated_prevention.append(item)
        else:
            _translated_prevention.append(item)

    # T-24.7: translate narrative fields from the live treatment and weather
    # blocks while leaving labels, scores, units, and severity values intact.
    _translated_diagnosis = dict(diagnosis)
    for key in ("symptoms_confirmed",):
        translated_items = []
        for item in diagnosis.get(key) or []:
            translated_item, warning = _translate_value(
                item, lang, _tech_terms)
            _translation_warning = _translation_warning or warning
            translated_items.append(translated_item)
        if translated_items:
            _translated_diagnosis[key] = translated_items

    _translated_treatment = dict(immediate_treatment)
    translated_steps = []
    for step in immediate_treatment.get("steps") or []:
        translated_step = dict(step)
        for key in ("action", "detail"):
            translated_value, warning = _translate_value(
                step.get(key), lang, _tech_terms)
            _translation_warning = _translation_warning or warning
            translated_step[key] = translated_value
        translated_steps.append(translated_step)
    if translated_steps:
        _translated_treatment["steps"] = translated_steps
    translated_window, warning = _translate_value(
        immediate_treatment.get("action_window"), lang, _tech_terms
    )
    _translation_warning = _translation_warning or warning
    if translated_window:
        _translated_treatment["action_window"] = translated_window

    _translated_weather = dict(weather_alert)
    for key in ("title", "message", "impact_warning", "action_window"):
        translated_value, warning = _translate_value(
            weather_alert.get(key), lang, _tech_terms)
        _translation_warning = _translation_warning or warning
        if translated_value:
            _translated_weather[key] = translated_value

    # B7 Why explanation: translate narrative keys
    _translated_why: dict = dict(why_explanation)
    for narrative_key in ("narrative", "explanation", "reasoning", "summary"):
        if why_explanation.get(narrative_key):
            t, w = _translate_block_text(
                str(why_explanation[narrative_key]), lang, _tech_terms
            )
            _translation_warning = _translation_warning or w
            _translated_why[narrative_key] = t

    # B8 Raw answer: translate if no structured blocks
    _translated_answer = answer
    if not has_structured_blocks and answer:
        _translated_answer, w = _translate_block_text(
            answer, lang, _tech_terms)
        _translation_warning = _translation_warning or w

    # Disclaimer: prefer pre-translated static string; fall back to dynamic
    _disclaimer = disclaimer
    if lang != "en" and not _disclaimer:
        _disclaimer = DISCLAIMERS.get(lang) or DISCLAIMERS.get("en")

    # ── T-17.7: Single toast if translation degraded ──────────────────────────
    if _translation_warning and lang != "en":
        st.toast(
            "⚠️ Translation service unavailable — showing original English advisory.",
            icon="🌐",
        )

    # ── Report heading (T-17.6: st.markdown with UTF-8 str) ──────────────────
    st.markdown("---")
    st.markdown("## 🌾 Agricultural Advisory Report")

    # ── Metadata ribbon ──────────────────────────────────────────────────────
    if metadata:
        _render_metadata_ribbon(metadata)

    st.markdown("---")

    # ── Block 1: Diagnosis ───────────────────────────────────────────────────
    render_block1_diagnosis(_translated_diagnosis)

    # ── Block 2: Immediate Treatment ─────────────────────────────────────────
    render_block2_immediate_treatment(_translated_treatment)

    # ── Block 3: Prevention ──────────────────────────────────────────────────
    render_block3_prevention(_translated_prevention)

    # ── Block 4: Weather Advisory ────────────────────────────────────────────
    render_block4_weather_advisory(_translated_weather)

    # ── Block 5: Sources ─────────────────────────────────────────────────────
    render_block5_sources(sources)

    # ── Block 6: Disclaimer ──────────────────────────────────────────────────
    render_block6_disclaimer(_disclaimer, language)

    # ── Block 7: "Why?" Explanation ──────────────────────────────────────────
    render_block7_why_explanation(_translated_why)

    # ── Block 8: Partial-response fallback ───────────────────────────────────
    if not has_structured_blocks:
        render_block8_raw_answer_fallback(_translated_answer)

    # ── Follow-up prompt & feedback ───────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "💬 **Have another question?** Type your follow-up in the box above and "
        "click **Ask Agri-Advisor** — your conversation context will be remembered."
    )
    st.markdown(
        f'<p style="color:#374151;font-size:0.9rem;margin-top:8px;">{HELPLINE_TEXT}</p>',
        unsafe_allow_html=True,
    )

    st.markdown("**Was this advice helpful?**")
    col_yes, col_no, _ = st.columns([1, 1, 5])
    with col_yes:
        if st.button("👍 Yes", key=f"helpful_yes_{session_id}"):
            _submit_feedback(session_id, True)
    with col_no:
        if st.button("👎 No", key=f"helpful_no_{session_id}"):
            _submit_feedback(session_id, False)


def _submit_feedback(session_id: str | None, helpful: bool) -> None:
    """Send FR-50 feedback once the live advisory has a session identity."""
    if not session_id:
        st.error("This advisory has no session ID, so feedback cannot be submitted.")
        return
    try:
        submit_feedback(session_id, helpful, get_auth_headers())
        st.toast(
            "Thank you for your feedback!" if helpful else "Sorry to hear that. We'll keep improving!",
            icon="✅" if helpful else "🙏",
        )
    except _ApiError as exc:
        if exc.status_code == 401:
            clear_auth()
            st.rerun()
        st.error("Feedback could not be submitted. Please try again later.")
