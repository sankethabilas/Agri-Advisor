"""Prompt construction, LLM synthesis, translation, and fallback templates for Outbreak Sentinel.

Strict Guardrails:
1. The LLM NEVER decides outbreak status.
2. The LLM is used ONLY for formatting simple farmer-friendly copy & officer briefs.
3. Every farmer-facing alert MUST include the mandatory advisory disclaimer.
4. If the LLM is unavailable or fails, rule-based templates are used immediately.
"""

import logging
from typing import Dict, List, Optional

from sentinel_agent.config import settings

logger = logging.getLogger("sentinel_agent.prompts")

MANDATORY_DISCLAIMER = (
    "This is advisory only. For severe cases, consult your local agriculture extension "
    "officer or visit the nearest agriculture office."
)

COMPACT_DISCLAIMER = "Advisory only. For severe cases, visit your nearest Agrarian Services Office."

# Pluggable Translation Dictionary Stub
# TODO: Integrate with IndicTrans2 or Google Cloud Translation API for production
TRANSLATION_STUB: Dict[str, Dict[str, str]] = {
    "si": {
        "ALERT": "අවධානයයි",
        "OUTBREAK_ALERT": "කෘෂි අවවාදයයි: රෝග අවදානම",
        "WATCH_ALERT": "කෘෂිකර්ම නිලධාරී දැනුම්දීම: විමසිලිමත්ව සිටින්න",
        "DISCLAIMER": "මෙය උපදේශනාත්මක පමණි. දැඩි හානි සඳහා ප්‍රාදේශීය කෘෂිකර්ම උපදේශක හමුවන්න.",
        "RICE": "වී වගාව",
        "RICE_BLB": "කොළ පාළුව / බැක්ටීරියා කොළ අංගමාරය",
    },
    "ta": {
        "ALERT": "எச்சரிக்கை",
        "OUTBREAK_ALERT": "விவசாய எச்சரிக்கை: நோய் பரவல் அபாயம்",
        "WATCH_ALERT": "விவசாய அதிகாரி தகவல்: கண்காணிப்பு தேவை",
        "DISCLAIMER": "இது ஆலோசனைக் குறிப்பு மட்டுமே. தீவிர பாதிப்புகளுக்கு உங்கள் விவசாய விரிவாக்கல் அதிகாரியை அணுகவும்.",
        "RICE": "நெல் பயிர்",
        "RICE_BLB": "பாக்டீரியல் இலைக்கருகல் நோய்",
    },
}


def translate(text: str, target_lang: str) -> str:
    """Translates alert text into target language (en, si, ta).

    Pluggable architecture with clear extension point for IndicTrans2 / Google Translate.
    """
    import re
    lang = (target_lang or "en").lower().strip()
    if lang == "en":
        return text

    # Simple keyword/pattern replacement stub for demonstration
    if lang in TRANSLATION_STUB:
        mapping = TRANSLATION_STUB[lang]
        translated = text
        for en_word, native_word in mapping.items():
            translated = re.sub(r"(?i)\b" + re.escape(en_word) + r"\b", native_word, translated)
        title = mapping.get("OUTBREAK_ALERT", "ALERT")
        disc = mapping.get("DISCLAIMER", MANDATORY_DISCLAIMER)
        return f"{title}: {translated}\n{disc}"

    return text


def build_farmer_template_alert(
    district: str,
    crop: str,
    disease: str,
    guidance: str,
    sources: List[str],
    language: str = "en",
) -> str:
    """Deterministic fallback alert message under 320 characters."""
    source_str = sources[0] if sources else "DOA Sri Lanka"
    msg = (
        f"AGRI-ALERT: High risk of {disease} reported for {crop} in {district} area. "
        f"Action: {guidance[:90]}. "
        f"Src: {source_str[:25]}. {COMPACT_DISCLAIMER}"
    )
    if language != "en":
        return translate(msg, language)
    return msg[:320]


def build_officer_template_alert(
    district: str,
    crop: str,
    disease: str,
    level: str,
    case_count: int,
    baseline: float,
    weather_level: str,
    reason: str,
    language: str = "en",
) -> str:
    """Deterministic officer notification."""
    msg = (
        f"[SENTINEL {level.upper()}]: {district} - {crop} ({disease}). "
        f"Cases: {case_count} (48h baseline: {baseline:.1f}). "
        f"Weather Risk: {weather_level}. Reason: {reason}"
    )
    return msg


def generate_farmer_alert_llm(
    district: str,
    crop: str,
    disease: str,
    guidance_context: str,
    sources: List[str],
    language: str = "en",
) -> str:
    """Uses LLM strictly for wording farmer-friendly alert text (with instant fallback)."""
    # Attempt LLM call if configured
    if settings.groq_api_key or settings.openai_api_key:
        try:
            if settings.llm_provider == "groq" and settings.groq_api_key:
                from groq import Groq

                client = Groq(api_key=settings.groq_api_key)
                prompt = (
                    f"Write a short, urgent SMS alert (max 200 characters) for smallholder farmers in {district}, "
                    f"Sri Lanka growing {crop}. Alert them about an outbreak risk of {disease}. "
                    f"Include 1 practical action based on: {guidance_context[:200]}. "
                    f"Keep it very simple and non-technical."
                )
                response = client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.2,
                )
                content = response.choices[0].message.content.strip()
                if content:
                    src = sources[0] if sources else "DOA Sri Lanka"
                    formatted = f"{content}\nSrc: {src}. {COMPACT_DISCLAIMER}"
                    return translate(formatted[:320], language)
        except Exception as err:
            logger.warning("LLM synthesis failed, falling back to template: %s", err)

    # Fallback to guaranteed template
    return build_farmer_template_alert(
        district=district,
        crop=crop,
        disease=disease,
        guidance=guidance_context,
        sources=sources,
        language=language,
    )
