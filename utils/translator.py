# -*- coding: utf-8 -*-
"""
utils/translator.py
Agri-Advisor -- Task T-17.3, T-17.4, T-17.5, T-17.6, T-17.7

Dynamic text translation for advisory output blocks.

Architecture
------------
The Orchestrator request/response pipeline always operates in English (T-17.4).
Translation is applied ONLY at render-time by calling ``translate_advisory_text``
on individual text strings before they are passed to Streamlit markdown.

Translation backend:
    ``deep-translator`` GoogleTranslator is used for both dynamic advisory
    output and static UI text. English bypasses the backend entirely.

Technical-term protection (T-17.5)
-----------------------------------
Before sending text to any translation API:
    protect_technical_terms()  replaces exact-match terms with __PROTECTED_N__ tokens
After translation:
    restore_technical_terms()  re-inserts original terms verbatim

This ensures disease names (e.g. "Bacterial Leaf Blight"), chemical names
(e.g. "Mancozeb"), and dosage strings (e.g. "2 g/L") survive translation
unchanged.

Script rendering (T-17.6)
--------------------------
All translated strings are returned as plain UTF-8 Python str objects.
Callers should render them with ``st.markdown(text, unsafe_allow_html=False)``
(or the equivalent) so Streamlit's built-in UTF-8 handling displays Sinhala
and Tamil glyphs correctly.  No manual encoding/decoding is required here.

Graceful fallback (T-17.7)
---------------------------
Every public function wraps API calls in try-except.  On any error:
    - A user-visible warning is signalled via the returned ``TranslationResult``
    - The original English text is returned so the UI never shows an empty block

Dynamic response translation uses the configured ``LLMClient`` from
``orchestrator.llm_client`` and therefore follows the existing LLM provider
configuration. Static UI translation uses MyMemory directly.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

logger = logging.getLogger(__name__)

# In-memory cache for rendered translations to prevent repeated API calls & rate limits
_TRANSLATION_CACHE: dict[tuple[str, str,
                               tuple[str, ...]], TranslationResult] = {}
_STATIC_TRANSLATION_CACHE: dict[tuple[str, str], TranslationResult] = {}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Placeholder template used to protect technical terms during translation
_PLACEHOLDER_TEMPLATE = "__PROTECTED_{index}__"

# Dosage / concentration patterns, e.g. "2g/L", "500 ml/ha", "0.5 kg/acre"
_DOSAGE_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:g|mg|kg|ml|L|mL|oz|lb|ppm|%)\s*/\s*"
    r"(?:L|mL|ha|acre|plant|tree|litre|liter)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Default technical terms always protected (regardless of caller-supplied list)
# These are common agri / chemistry terms that must never be mistranslated.
# ---------------------------------------------------------------------------
ALWAYS_PROTECT: list[str] = [
    # Diseases
    "Bacterial Leaf Blight",
    "Brown Plant Hopper",
    "Rice Blast",
    "Sheath Blight",
    "Tungro",
    "Leaf Scald",
    "Narrow Brown Leaf Spot",
    "False Smut",
    "White Ear",
    "Blast",
    # Fungicides / pesticides
    "Mancozeb",
    "Carbendazim",
    "Tricyclazole",
    "Propiconazole",
    "Chlorothalonil",
    "Iprodione",
    "Thiram",
    "Metalaxyl",
    "Captafol",
    "Copper Oxychloride",
    "Imidacloprid",
    "Thiamethoxam",
    "Buprofezin",
    "Cypermethrin",
    "Lambda-cyhalothrin",
    "Glyphosate",
    # Units / measurements (handled by _DOSAGE_RE as well, belt-and-suspenders)
    "g/L",
    "ml/L",
    "kg/ha",
    "g/ha",
    "ml/ha",
    "ppm",
    # Sri Lanka institutions
    "Rice Research Institute",
    "Department of Agriculture",
    "DOA",
]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class TranslationResult:
    """
    Returned by ``translate_advisory_text``.

    Attributes:
        text:         The translated text (or original on failure).
        success:      True if the API call succeeded.
        backend:      Name of the backend that produced the translation.
        warn_message: Non-empty when fallback occurred; pass to ``st.toast``.
    """
    text: str
    success: bool = True
    backend: str = "passthrough"
    warn_message: str = ""


# ---------------------------------------------------------------------------
# T-17.5  Technical-term protection helpers
# ---------------------------------------------------------------------------

def protect_technical_terms(
    text: str,
    terms_list: list[str] | None = None,
) -> tuple[str, dict[str, str]]:
    """
    Replace each technical term in *text* with a unique ``__PROTECTED_N__``
    placeholder so the translation API cannot corrupt it.

    The function first substitutes dosage patterns (via regex), then the
    combined list of ``ALWAYS_PROTECT`` + caller-supplied *terms_list*.
    Longer terms are matched before shorter ones to avoid partial replacements.

    Args:
        text:       Input English text.
        terms_list: Optional additional terms to protect (disease names,
                    chemical names specific to this advisory).

    Returns:
        (protected_text, mapping)  where *mapping* is
        ``{placeholder: original_term}`` and is required by
        ``restore_technical_terms``.
    """
    mapping: dict[str, str] = {}
    counter = 0

    # -- Step 1: protect dosage/concentration patterns via regex -------------
    def _dosage_replacer(m: re.Match) -> str:
        nonlocal counter
        ph = _PLACEHOLDER_TEMPLATE.format(index=counter)
        mapping[ph] = m.group(0)
        counter += 1
        return ph

    text = _DOSAGE_RE.sub(_dosage_replacer, text)

    # -- Step 2: protect named terms (longest first to avoid partial matches) -
    all_terms: list[str] = sorted(
        set(ALWAYS_PROTECT + (terms_list or [])),
        key=len,
        reverse=True,
    )

    for term in all_terms:
        if not term or term.lower() not in text.lower():
            continue
        ph = _PLACEHOLDER_TEMPLATE.format(index=counter)
        # Use word-boundary-aware replacement for single-word terms
        escaped = re.escape(term)
        pattern = re.compile(r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE)
        new_text, n = pattern.subn(ph, text)
        if n > 0:
            mapping[ph] = term  # preserve original capitalisation
            text = new_text
            counter += 1

    return text, mapping


def restore_technical_terms(
    translated_text: str,
    mapping: dict[str, str],
) -> str:
    """
    Re-insert original technical terms by replacing ``__PROTECTED_N__``
    placeholders with their original strings.

    Args:
        translated_text: Text as returned by the translation API.
        mapping:         The mapping dict produced by ``protect_technical_terms``.

    Returns:
        Final text with all placeholders replaced by original terms.
    """
    if not mapping:
        return translated_text

    for placeholder, original in mapping.items():
        # Handle case/space alterations from MT engines (e.g. "__PROTECTED_0__", "__ protected_0 __")
        idx_match = re.search(r"\d+", placeholder)
        if idx_match:
            idx = idx_match.group(0)
            pattern = re.compile(
                rf"__\s*PROTECTED\s*_\s*{idx}\s*__", re.IGNORECASE)
            translated_text = pattern.sub(original, translated_text)
        else:
            translated_text = translated_text.replace(placeholder, original)

    # Belt-and-suspenders: remove any stray placeholders the API may have mangled
    translated_text = re.sub(
        r"__\s*PROTECTED\s*_\s*\d+\s*__", "", translated_text, flags=re.IGNORECASE)

    return translated_text


# ---------------------------------------------------------------------------
# Backend helper
# ---------------------------------------------------------------------------

def _translate_with_deep_translator(text: str, target_lang: str) -> str:
    """Translate text through deep-translator without Google Cloud billing."""
    if GoogleTranslator is None:
        raise RuntimeError("deep-translator is not installed.")
    translated = GoogleTranslator(
        source="en", target=target_lang).translate(text)
    if not translated or not translated.strip():
        raise RuntimeError("deep-translator returned an empty translation.")
    return translated


# ---------------------------------------------------------------------------
# T-17.3 / T-17.4  Main public translation function
# ---------------------------------------------------------------------------

def translate_advisory_text(
    text: str,
    target_lang: str,
    technical_terms: list[str] | None = None,
) -> TranslationResult:
    """
    Translate *text* to *target_lang*, protecting technical terms.

    This function is called ONLY at UI render-time (T-17.4).
    The Orchestrator pipeline always receives and produces English; this
    function is never called on API request payloads.

    Dynamic response text is translated by ``deep-translator``.

    Technical-term protection:
        Before translation: ``protect_technical_terms`` is called.
        After translation:  ``restore_technical_terms`` is called.

    Args:
        text:            English advisory text to translate.
        target_lang:     ISO 639-1 target language code ("si" or "ta").
                         If "en", the original text is returned immediately.
        technical_terms: Additional disease / chemical names to protect;
                         merged with ``ALWAYS_PROTECT``.

    Returns:
        ``TranslationResult`` with ``.text`` always populated (never empty).
    """
    # -- Guard: no translation needed for English ---------------------------
    if not text or not text.strip():
        return TranslationResult(text=text, backend="passthrough")

    if target_lang == "en":
        return TranslationResult(text=text, backend="passthrough")

    # -- Cache check --------------------------------------------------------
    cache_key = (text, target_lang, tuple(sorted(technical_terms or [])))
    if cache_key in _TRANSLATION_CACHE and _TRANSLATION_CACHE[cache_key].success:
        return _TRANSLATION_CACHE[cache_key]

    # -- T-17.5: protect technical terms ------------------------------------
    protected_text, term_mapping = protect_technical_terms(
        text, technical_terms)

    try:
        translated = _translate_with_deep_translator(
            protected_text, target_lang)
        restored = restore_technical_terms(translated.strip(), term_mapping)
        result = TranslationResult(
            text=restored,
            success=True,
            backend="deep-translator",
        )
        _TRANSLATION_CACHE[cache_key] = result
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("deep-translator advisory translation failed: %s", exc)

    # -- T-17.7: Graceful fallback ------------------------------------------
    # All backends failed; return original English text with a warning signal.
    return TranslationResult(
        text=text,
        success=False,
        backend="passthrough",
        warn_message=(
            "Translation service unavailable \u2014 "
            "showing original English advisory."
        ),
    )


def translate_static_text(
    text: str,
    target_lang: str,
    technical_terms: list[str] | None = None,
) -> TranslationResult:
    """Translate static UI copy with deep-translator for the selected locale."""
    if not text or not text.strip() or target_lang == "en":
        return TranslationResult(text=text, backend="passthrough")

    cache_key = (text, target_lang)
    cached = _STATIC_TRANSLATION_CACHE.get(cache_key)
    if cached is not None:
        return cached

    protected_text, term_mapping = protect_technical_terms(
        text, technical_terms)
    try:
        translated = _translate_with_deep_translator(
            protected_text, target_lang)
        restored = restore_technical_terms(translated, term_mapping)
        result = TranslationResult(
            text=restored,
            success=True,
            backend="deep-translator",
        )
        _STATIC_TRANSLATION_CACHE[cache_key] = result
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("deep-translator static translation failed: %s", exc)
        return TranslationResult(
            text=text,
            success=False,
            backend="passthrough",
            warn_message="Static translation service unavailable.",
        )


# ---------------------------------------------------------------------------
# Convenience batch function
# ---------------------------------------------------------------------------

def translate_block(
    block_texts: dict[str, str],
    target_lang: str,
    technical_terms: list[str] | None = None,
) -> tuple[dict[str, str], bool]:
    """
    Translate a dictionary of ``{key: text}`` pairs to *target_lang*.

    Skips empty strings.  Returns the translated dict and a boolean flag
    indicating whether any translation warning was raised.

    Args:
        block_texts:     Dict mapping block keys to English text strings.
        target_lang:     Target locale code.
        technical_terms: Terms to protect across all blocks.

    Returns:
        (translated_dict, had_warning)
    """
    if target_lang == "en":
        return block_texts, False

    translated: dict[str, str] = {}
    had_warning = False

    for key, text in block_texts.items():
        if not text or not text.strip():
            translated[key] = text
            continue
        result = translate_advisory_text(text, target_lang, technical_terms)
        translated[key] = result.text
        if not result.success:
            had_warning = True

    return translated, had_warning
