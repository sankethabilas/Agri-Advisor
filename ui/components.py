"""
ui/components.py
Production-grade reusable components for the Agri-Advisor Agricultural Operating System.
"""
from __future__ import annotations

import html
from typing import Any, Dict, List, Optional
import streamlit as st

from ui.api_client import submit_feedback
from ui.auth import get_auth_headers
from ui.config import DISCLAIMERS, HELPLINE_TEXT, SEVERITY_STYLE, get_app_icon_base64
from ui.advisory_renderer import render_advisory_response, render_eight_block_advisory
from utils.i18n import get_string


def render_topbar(
    active_page_name: str,
    user_id: Optional[str] = None,
    district: Optional[str] = None,
    language: str = "en",
) -> None:
    """Renders the minimal, premium top navigation header."""
    user_label = user_id or "Farmer"
    district_label = district or "Sri Lanka"
    logo_b64 = get_app_icon_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 100%; height: 100%; object-fit: contain; border-radius: 6px;" alt="Logo" />' if logo_b64 else '🌾'

    st.markdown(
        f"""
        <div class="topbar-container">
            <div class="topbar-brand">
                <div class="brand-badge-logo" style="background: #072D1B; padding: 2px;">{logo_html}</div>
                <div>
                    <h2 class="brand-text-title">Agri-Advisor OS</h2>
                    <p class="brand-text-subtitle">Autonomous Agricultural Intelligence</p>
                </div>
            </div>
            <div class="topbar-actions">
                <div class="status-pill">
                    <span class="status-dot"></span>
                    <span>7 Agents Active</span>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted); font-weight: 500; border-left: 1px solid var(--border-subtle); padding-left: 14px;">
                    📍 <strong>{district_label}</strong> &nbsp;|&nbsp; 👤 {user_label}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero_banner(
    greeting: str = "Good day 👋",
    title: str = "Your farm intelligence at a glance.",
    subtitle: str = "Real-time agro-meteorology, disease surveillance, and AI advisory calibrated for Sri Lanka.",
) -> None:
    """Renders the cinematic agricultural SaaS hero card."""
    st.markdown(
        f"""
        <div class="hero-card">
            <span style="font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--color-primary-300);">
                {greeting}
            </span>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agent_stepper(current_stage: str = "ready") -> None:
    """Visually exposes the live multi-agent collaboration pipeline."""
    agents = [
        ("🧠", "Orchestrator", "Intent & Routing"),
        ("🌾", "Crop Agent", "Cultivation"),
        ("🔬", "Disease Agent", "Pathology"),
        ("🌦️", "Weather Agent", "Microclimate"),
        ("📈", "Market Agent", "Economics"),
        ("📚", "RAG Agent", "DOA Corpus"),
        ("🛡️", "Sentinel", "Surveillance"),
        ("💡", "Synthesis", "Final Advisory"),
    ]

    items_html = ""
    for icon, name, sub in agents:
        status_class = "agent-step-done" if current_stage == "completed" else (
            "agent-step-active" if current_stage == "processing" else "agent-step-waiting"
        )
        status_text = "Verified" if current_stage == "completed" else (
            "Analyzing" if current_stage == "processing" else "Ready"
        )

        items_html += f"""
        <div class="agent-step-item {status_class}">
            <div class="agent-step-icon">{icon}</div>
            <div class="agent-step-label">{name}</div>
            <div class="agent-step-status">{status_text}</div>
        </div>
        """

    st.markdown(
        f"""
        <div class="agent-flow-container">
            <div class="agent-flow-title">
                <span>⚡ Multi-Agent Intelligence Pipeline</span>
            </div>
            <div class="agent-stepper">
                {items_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bento_weather_card(
    district: str = "Colombo",
    temp_c: float = 29.5,
    humidity: int = 78,
    condition: str = "Partly Cloudy",
    disease_risk: str = "Moderate",
) -> None:
    """Renders the Weather Bento Card."""
    risk_color = "#EA580C" if disease_risk.lower() in ("high", "moderate") else "#10B981"
    risk_bg = "#FFEDD5" if disease_risk.lower() in ("high", "moderate") else "#D1FAE5"

    st.markdown(
        f"""
        <div class="bento-card" style="height: 100%;">
            <div class="bento-header">
                <div class="bento-title">🌦️ Agro-Weather</div>
                <span class="bento-badge" style="background: var(--accent-weather-bg); color: var(--accent-weather);">
                    {district}
                </span>
            </div>
            <div style="display: flex; align-items: baseline; gap: 12px; margin: 12px 0;">
                <div class="bento-stat-number">{temp_c:.1f}°C</div>
                <div style="font-size: 1rem; color: var(--text-secondary); font-weight: 500;">{condition}</div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px;">
                <div style="background: var(--bg-subtle); padding: 8px 12px; border-radius: var(--radius-md);">
                    <div style="font-size: 0.75rem; color: var(--text-muted);">Relative Humidity</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">{humidity}%</div>
                </div>
                <div style="background: {risk_bg}; padding: 8px 12px; border-radius: var(--radius-md);">
                    <div style="font-size: 0.75rem; color: {risk_color};">Fungal Risk</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: {risk_color};">{disease_risk}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bento_crop_health(
    monitored_crops: int = 3,
    avg_health_pct: int = 92,
    active_advisories: int = 1,
) -> None:
    """Renders the Crop Health Bento Card."""
    st.markdown(
        f"""
        <div class="bento-card" style="height: 100%;">
            <div class="bento-header">
                <div class="bento-title">🌾 Crop Health Index</div>
                <span class="bento-badge" style="background: var(--accent-success-bg); color: var(--accent-success);">
                    Good Standing
                </span>
            </div>
            <div style="display: flex; align-items: baseline; gap: 10px; margin: 12px 0;">
                <div class="bento-stat-number">{avg_health_pct}%</div>
                <div style="font-size: 0.88rem; color: var(--color-primary-600); font-weight: 600;">Optimal Vigor</div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px;">
                <div style="background: var(--bg-subtle); padding: 8px 12px; border-radius: var(--radius-md);">
                    <div style="font-size: 0.75rem; color: var(--text-muted);">Monitored Plots</div>
                    <div style="font-size: 0.95rem; font-weight: 700;">{monitored_crops} Fields</div>
                </div>
                <div style="background: var(--bg-subtle); padding: 8px 12px; border-radius: var(--radius-md);">
                    <div style="font-size: 0.75rem; color: var(--text-muted);">Active Advisories</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: var(--color-primary-700);">{active_advisories} Active</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bento_market_card(
    top_commodity: str = "Paddy (Nadu)",
    price_lkr_kg: float = 125.0,
    change_pct: float = 2.4,
) -> None:
    """Renders the Market Prices Bento Card."""
    trend_color = "#10B981" if change_pct >= 0 else "#EF4444"
    trend_sign = "+" if change_pct >= 0 else ""

    st.markdown(
        f"""
        <div class="bento-card" style="height: 100%;">
            <div class="bento-header">
                <div class="bento-title">📈 Commodity Market</div>
                <span class="bento-badge" style="background: var(--accent-market-bg); color: var(--accent-market);">
                    Pettah / Dambulla
                </span>
            </div>
            <div style="margin: 12px 0;">
                <div style="font-size: 0.88rem; color: var(--text-muted); font-weight: 500;">{top_commodity}</div>
                <div style="display: flex; align-items: baseline; gap: 8px;">
                    <div class="bento-stat-number">Rs. {price_lkr_kg:.0f}</div>
                    <div style="font-size: 0.85rem; font-weight: 700; color: {trend_color};">
                        {trend_sign}{change_pct:.1f}% vs last week
                    </div>
                </div>
            </div>
            <div style="background: var(--bg-subtle); padding: 8px 12px; border-radius: var(--radius-md); font-size: 0.8rem; color: var(--text-secondary);">
                💡 <em>Price trending upward. Consider forward contracts.</em>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bento_sentinel_alert(
    level: str = "Normal",
    district: str = "Anuradhapura",
    details: str = "Surveillance scans normal. No active regional outbreaks.",
) -> None:
    """Renders the Outbreak Sentinel Alert Bento Card."""
    is_outbreak = level.lower() == "outbreak"
    is_watch = level.lower() == "watch"

    bg = "#FEE2E2" if is_outbreak else ("#FEF3C7" if is_watch else "#ECFDF5")
    color = "#991B1B" if is_outbreak else ("#92400E" if is_watch else "#065F46")
    badge_text = "CRITICAL OUTBREAK" if is_outbreak else ("WATCH ADVISORY" if is_watch else "CLEAN STATUS")

    st.markdown(
        f"""
        <div class="bento-card" style="background: {bg}; border-color: {color}33;">
            <div class="bento-header">
                <div class="bento-title" style="color: {color};">🛡️ Outbreak Sentinel</div>
                <span class="bento-badge" style="background: {color}; color: #ffffff;">
                    {badge_text}
                </span>
            </div>
            <div style="font-size: 0.95rem; font-weight: 700; color: {color}; margin-bottom: 4px;">
                {district} Surveillance Zone
            </div>
            <div style="font-size: 0.85rem; color: {color}; opacity: 0.9; line-height: 1.4;">
                {details}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_error(error_msg: str) -> None:
    """Renders a refined, accessible error card."""
    st.markdown(
        f"""
        <div style="background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: var(--radius-md); padding: 16px 20px; color: #991B1B; margin-bottom: 16px;">
            <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 4px;">⚠️ Notice</div>
            <div style="font-size: 0.88rem;">{html.escape(error_msg)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
