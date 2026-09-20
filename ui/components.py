"""
ui/components.py
Reusable Streamlit rendering components for the Agri-Advisor advisory response.
Each function is responsible for one "block" of the eight-block layout defined
in /docs/ui-spec.md, Section 4.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import streamlit as st

from ui.config import DISCLAIMERS, HELPLINE_TEXT, SEVERITY_STYLE


# ============================================================================
# § Utility helpers
# ============================================================================

def _severity_badge(severity: str) -> str:
    """Return an HTML badge string for a given weather severity level."""
    s = SEVERITY_STYLE.get(severity.lower(), SEVERITY_STYLE["none"])
    weight = "700" if s["bold"] else "500"
    return (
        f'<span style="background:{s["bg"]};color:{s["color"]};'
        f'font-weight:{weight};padding:2px 10px;border-radius:12px;'
        f'font-size:0.85rem;">{s["label"]}</span>'
    )


def _confidence_badge(label: str) -> str:
    """Return an HTML badge for High / Medium / Low diagnosis confidence."""
    mapping = {
        "high":   ("#166534", "#DCFCE7"),
        "medium": ("#92400E", "#FEF3C7"),
        "low":    ("#9A3412", "#FEE2E2"),
    }
    color, bg = mapping.get(label.lower(), ("#374151", "#F3F4F6"))
    return (
        f'<span style="background:{bg};color:{color};font-weight:600;'
        f'padding:2px 10px;border-radius:12px;font-size:0.82rem;">{label.capitalize()}</span>'
    )


def _format_datetime(iso_str: str) -> str:
    """Convert an ISO-8601 timestamp to a human-friendly string."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%a %d %b, %I:%M %p %Z")
    except (ValueError, AttributeError):
        return iso_str


# ============================================================================
# § Block 5 — Weather Advisory
# ============================================================================

def render_weather_alert(weather_alert: dict[str, Any]) -> None:
    """Block 5: Weather Advisory card (omitted entirely when severity == 'none')."""
    severity = (weather_alert.get("severity") or "none").lower()
    if severity == "none":
        return

    s = SEVERITY_STYLE.get(severity, SEVERITY_STYLE["none"])
    border_color = s["bg"] if severity in ("none", "low", "moderate") else s["color"]

    st.markdown("---")
    st.markdown("#### 🌦 Weather Advisory")

    badge_html = _severity_badge(severity)
    title      = weather_alert.get("title", "Weather Alert")
    message    = weather_alert.get("message", "")
    impact     = weather_alert.get("impact_warning", "")
    valid_until_raw = weather_alert.get("valid_until", "")
    valid_until = _format_datetime(valid_until_raw) if valid_until_raw else ""

    card_html = f"""
    <div style="
        border-left: 5px solid {s['bg']};
        background: #FAFAFA;
        padding: 16px 20px;
        border-radius: 8px;
        margin-bottom: 12px;
    ">
        <div style="margin-bottom:8px;">{badge_html}&nbsp;&nbsp;
            <strong style="font-size:1.05rem;">{title}</strong>
        </div>
        <p style="margin:4px 0;color:#374151;">{message}</p>
        {f'<p style="margin:8px 0;padding:8px 12px;background:#FEF3C7;border-radius:6px;'
         f'font-weight:600;color:#92400E;">⚠️ {impact}</p>' if impact else ""}
        {f'<p style="margin:4px 0;font-size:0.82rem;color:#6B7280;">Valid until: {valid_until}</p>'
         if valid_until else ""}
    </div>
    """
    st.html(card_html)


# ============================================================================
# § Block 6 — Sources
# ============================================================================

def render_sources(sources: list[dict[str, Any]]) -> None:
    """Block 6: Knowledge sources list (omitted when sources is empty)."""
    if not sources:
        return

    # Sort descending by confidence_score
    sorted_sources = sorted(
        sources,
        key=lambda s: s.get("confidence_score", 0.0),
        reverse=True,
    )

    st.markdown("---")
    with st.expander("📚 Knowledge Sources", expanded=False):
        for i, src in enumerate(sorted_sources, 1):
            title   = src.get("title", "Unknown Source")
            org     = src.get("author_organization", "")
            section = src.get("section", "")
            url     = src.get("reference_url")

            title_html = (
                f'<a href="{url}" target="_blank" style="color:#1d4ed8;text-decoration:none;">{title}</a>'
                if url else title
            )
            section_html = f' <span style="color:#6B7280;font-size:0.82rem;">({section})</span>' if section else ""
            org_html = f'<span style="color:#6B7280;font-size:0.85rem;"> — {org}</span>' if org else ""

            st.html(
                f'<div style="margin-bottom:10px;">'
                f'<strong style="font-size:0.95rem;">{i}. {title_html}</strong>'
                f'{section_html}{org_html}'
                f'</div>'
            )


# ============================================================================
# § Block 7 — Disclaimer
# ============================================================================

def render_disclaimer(language: str) -> None:
    """Block 7: Static AI disclaimer notice."""
    text = DISCLAIMERS.get(language, DISCLAIMERS["en"])
    st.markdown("---")
    st.info(f"ℹ️ **Important Notice**\n\n{text}")


# ============================================================================
# § Block 8 — Follow-up Prompt & Helpline
# ============================================================================

def render_followup(session_id: str | None = None) -> None:
    """Block 8: Follow-up prompt, helpline, and feedback controls."""
    st.markdown("---")
    st.markdown(
        "💬 **Have another question?** Type your follow-up in the box above and "
        "click **Ask Agri-Advisor** — your conversation context will be remembered."
    )
    st.markdown(
        f'<p style="color:#374151;font-size:0.9rem;margin-top:8px;">{HELPLINE_TEXT}</p>',
        unsafe_allow_html=True,
    )

    # "Was this helpful?" feedback widget
    st.markdown("**Was this advice helpful?**")
    col_yes, col_no, _ = st.columns([1, 1, 5])
    with col_yes:
        if st.button("👍 Yes", key=f"helpful_yes_{session_id}"):
            st.toast("Thank you for your feedback!", icon="✅")
    with col_no:
        if st.button("👎 No", key=f"helpful_no_{session_id}"):
            st.toast("Sorry to hear that. We'll keep improving!", icon="🙏")


# ============================================================================
# § Full Advisory Response renderer
# ============================================================================

def render_advisory_response(response: dict[str, Any], is_fallback: bool = False) -> None:
    """
    Render the complete eight-block advisory response layout as defined in
    /docs/ui-spec.md Section 4.
    """
    if is_fallback:
        st.warning(
            "⚠️ **Demo Mode** — The Agri-Advisor server is not running. "
            "Displaying sample advisory data so you can explore the interface.",
            icon="🔌",
        )

    answer        = response.get("answer", "")
    sources       = response.get("sources", [])
    weather_alert = response.get("weather_alert", {})
    metadata      = response.get("metadata", {})
    language      = metadata.get("language", "en")
    session_id    = metadata.get("session_id")

    # ── Blocks 1–4, 7–8 come from the synthesized `answer` markdown ─────────
    if answer:
        st.markdown("### 📋 Advisory Response")

        # Detect and badge confidence labels inline (High / Medium / Low)
        def _badge_replace(m: re.Match) -> str:  # type: ignore[type-arg]
            label = m.group(0)
            return f"{label} {_confidence_badge(label)}"

        badged_answer = re.sub(
            r"\b(High|Medium|Low)\b(?=.*confidence)",
            _badge_replace,
            answer,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )

        st.markdown(badged_answer, unsafe_allow_html=True)

    # Metadata ribbon (agents consulted, latency) – shown collapsed, no raw IDs
    agents = metadata.get("agents_consulted", [])
    latency = metadata.get("latency_ms")
    if agents or latency:
        with st.expander("🔍 Response details", expanded=False):
            if agents:
                friendly_names = {
                    "disease_agent": "Disease Identification",
                    "weather_agent": "Weather Advisory",
                    "rag_agent":     "Knowledge Base",
                }
                names = [friendly_names.get(a, a) for a in agents]
                st.markdown(f"**Systems consulted:** {', '.join(names)}")
            if latency:
                st.markdown(f"**Response time:** {latency} ms")

    # ── Block 5 — Weather Alert ──────────────────────────────────────────────
    render_weather_alert(weather_alert)

    # ── Block 6 — Sources ───────────────────────────────────────────────────
    render_sources(sources)

    # ── Block 7 — Disclaimer ────────────────────────────────────────────────
    render_disclaimer(language)

    # ── Block 8 — Follow-up & Helpline ──────────────────────────────────────
    render_followup(session_id)


# ============================================================================
# § Error renderer
# ============================================================================

def render_error(status_code: int, body: dict[str, Any]) -> None:
    """
    Render plain-language error messages mapped to HTTP codes (ui-spec.md §6).
    Never exposes raw error.code, request_id, or stack traces to the farmer.
    """
    friendly: dict[int, str] = {
        400: "Please check your input — make sure your question and district are filled in.",
        401: "Your session has expired. Please log in again.",
        403: "You don't have access to this feature.",
        404: "We couldn't find advice for that crop or district. "
             "Try selecting a different district or rephrasing your question.",
        422: "There's a problem with your input. "
             "Please check the district and question fields and try again.",
        429: "You've sent too many requests. Please wait a moment and try again.",
        500: "Something went wrong on our end. Please try again shortly.",
        502: "Something went wrong on our end. Please try again shortly.",
        503: "The advisory service is temporarily unavailable. Please try again shortly.",
    }
    message = friendly.get(status_code, "An unexpected error occurred. Please try again.")
    st.error(f"❌ {message}")

    # Debug details hidden in an expander (for devs, never primary text)
    with st.expander("Technical details (for support use)", expanded=False):
        st.code(f"HTTP {status_code}\n{body}", language="text")


# ============================================================================
# § Conversation history renderer
# ============================================================================

def render_conversation_history(history: list[dict[str, Any]]) -> None:
    """Render the multi-turn conversation history above the response area."""
    if not history:
        return

    st.markdown("---")
    st.markdown("#### 🗂 Conversation History")

    with st.expander(f"Previous exchanges ({len(history)})", expanded=False):
        for idx, turn in enumerate(reversed(history), 1):
            q = turn.get("query", "")
            district = turn.get("district", "")
            summary = turn.get("answer_summary", "")

            st.markdown(
                f"""
<div style="border-left:3px solid #4ADE80;padding:8px 14px;margin-bottom:10px;background:#F0FDF4;border-radius:0 6px 6px 0;">
  <p style="margin:0 0 4px 0;font-size:0.8rem;color:#6B7280;">Turn {len(history) - idx + 1} · {district}</p>
  <p style="margin:0 0 4px 0;font-weight:600;color:#166534;">Q: {q}</p>
  {f'<p style="margin:0;font-size:0.9rem;color:#374151;">{summary}</p>' if summary else ""}
</div>
""",
                unsafe_allow_html=True,
            )
