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

Supported back-ends (auto-selected by available credentials):
    1. Google Cloud Translation  -- set GOOGLE_APPLICATION_CREDENTIALS *or*
                                    TRANSLATION_API_KEY in the environment
    2. MyMemory free API          -- no credentials required; 500 chars/req limit;
                                    used as a fallback when Google is unavailable
    3. Passthrough / English      -- used when target_lang == "en" or all APIs fail

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

Environment variables
---------------------
    TRANSLATION_API_KEY            Google Cloud Translation API key (simple key)
    GOOGLE_APPLICATION_CREDENTIALS Path to a GCP service-account JSON key file
                                   (used by the google-cloud-translate library)

Install dependencies (optional -- only needed if Google Cloud is used):
    pip install google-cloud-translate==3.*
"""
from __future__ import annotations

import logging
import os
import re
import time
import urllib.parse
import urllib.request
import json
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Placeholder template used to protect technical terms during translation
_PLACEHOLDER_TEMPLATE = "__PROTECTED_{index}__"

# Regex that recognises a placeholder token inside translated text
_PLACEHOLDER_RE = re.compile(r"__PROTECTED_\d+__")

# Dosage / concentration patterns, e.g. "2g/L", "500 ml/ha", "0.5 kg/acre"
_DOSAGE_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:g|mg|kg|ml|L|mL|oz|lb|ppm|%)\s*/\s*"
    r"(?:L|mL|ha|acre|plant|tree|litre|liter)\b",
    re.IGNORECASE,
)

# MyMemory free API endpoint
_MYMEMORY_API = "https://api.mymemory.translated.net/get"

# Request timeout for translation API calls (seconds)
_TIMEOUT_SECS = 8

# Maximum text length MyMemory handles reliably per request
_MYMEMORY_MAX_CHARS = 450

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
        if not term or term not in text:
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
        translated_text = translated_text.replace(placeholder, original)

    # Belt-and-suspenders: remove any stray placeholders the API may have
    # mangled (e.g. "__PROTECTED_ 0 __")
    translated_text = _PLACEHOLDER_RE.sub("", translated_text)

    return translated_text


# ---------------------------------------------------------------------------
# Backend helpers (private)
# ---------------------------------------------------------------------------

def _google_api_key() -> str | None:
    """Return the Google Cloud Translation API key, or None if not set."""
    return os.environ.get("TRANSLATION_API_KEY") or None


def _has_google_cloud_library() -> bool:
    """Check whether the google-cloud-translate library is importable."""
    try:
        import google.cloud.translate_v2  # noqa: F401
        return True
    except ImportError:
        return False


def _translate_google_rest(text: str, target_lang: str) -> str:
    """
    Translate *text* to *target_lang* using the Google Cloud Translation
    REST API with a simple API key.

    Raises:
        RuntimeError: on HTTP errors or missing key.
    """
    api_key = _google_api_key()
    if not api_key:
        raise RuntimeError("TRANSLATION_API_KEY not set in environment.")

    endpoint = "https://translation.googleapis.com/language/translate/v2"
    params = urllib.parse.urlencode({
        "q":      text,
        "target": target_lang,
        "format": "text",
        "key":    api_key,
    })
    url = f"{endpoint}?{params}"
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=_TIMEOUT_SECS) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    translations = body.get("data", {}).get("translations", [])
    if not translations:
        raise RuntimeError("Empty translation response from Google API.")
    return translations[0]["translatedText"]


def _translate_google_cloud_library(text: str, target_lang: str) -> str:
    """
    Translate *text* using the ``google-cloud-translate`` Python library
    (uses GOOGLE_APPLICATION_CREDENTIALS service-account JSON).

    Raises:
        Exception: propagated from the library on auth / network errors.
    """
    from google.cloud import translate_v2 as gtranslate  # type: ignore
    client = gtranslate.Client()
    result = client.translate(text, target_language=target_lang)
    return result["translatedText"]


def _translate_mymemory(text: str, target_lang: str, source_lang: str = "en") -> str:
    """
    Translate *text* via the MyMemory free API.

    Splits long text into chunks to stay within the 500-char per-request limit.

    Raises:
        RuntimeError: on HTTP errors or empty response.
    """
    # Split into paragraphs / sentences to respect the char limit
    chunks = _split_for_mymemory(text)
    translated_chunks: list[str] = []

    for chunk in chunks:
        lang_pair = f"{source_lang}|{target_lang}"
        params = urllib.parse.urlencode({"q": chunk, "langpair": lang_pair})
        url = f"{_MYMEMORY_API}?{params}"

        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Agri-Advisor/1.0 (t17-translation)")

        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECS) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        response_status = body.get("responseStatus")
        if response_status != 200:
            raise RuntimeError(
                f"MyMemory API returned status {response_status}: "
                f"{body.get('responseDetails', 'unknown error')}"
            )

        translated_text = body.get("responseData", {}).get("translatedText", "")
        if not translated_text:
            raise RuntimeError("MyMemory returned empty translation.")

        translated_chunks.append(translated_text)
        # Be polite to the free API
        if len(chunks) > 1:
            time.sleep(0.25)

    return " ".join(translated_chunks)


def _split_for_mymemory(text: str) -> list[str]:
    """
    Split *text* into chunks of at most ``_MYMEMORY_MAX_CHARS`` characters,
    breaking on sentence boundaries where possible.
    """
    if len(text) <= _MYMEMORY_MAX_CHARS:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= _MYMEMORY_MAX_CHARS:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            # If a single sentence exceeds the limit, hard-split it
            if len(sentence) > _MYMEMORY_MAX_CHARS:
                for i in range(0, len(sentence), _MYMEMORY_MAX_CHARS):
                    chunks.append(sentence[i: i + _MYMEMORY_MAX_CHARS])
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


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

    Back-end selection order:
        1. Google Cloud Translate REST (TRANSLATION_API_KEY env var)
        2. Google Cloud Translate library (GOOGLE_APPLICATION_CREDENTIALS)
        3. MyMemory free API (no credentials required)
        4. Passthrough: returns original English text with a warning (T-17.7)

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

    # Map internal locale codes to BCP-47 / ISO 639-1 codes Google accepts
    _LANG_MAP = {"si": "si", "ta": "ta"}
    bcp47_lang = _LANG_MAP.get(target_lang, target_lang)

    # -- T-17.5: protect technical terms ------------------------------------
    protected_text, term_mapping = protect_technical_terms(text, technical_terms)

    # -- Try back-end 1: Google Cloud REST API ------------------------------
    if _google_api_key():
        try:
            translated = _translate_google_rest(protected_text, bcp47_lang)
            restored = restore_technical_terms(translated, term_mapping)
            return TranslationResult(
                text=restored,
                success=True,
                backend="google_rest",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Google REST translation failed: %s", exc)

    # -- Try back-end 2: Google Cloud library (service-account JSON) --------
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and _has_google_cloud_library():
        try:
            translated = _translate_google_cloud_library(protected_text, bcp47_lang)
            restored = restore_technical_terms(translated, term_mapping)
            return TranslationResult(
                text=restored,
                success=True,
                backend="google_cloud_library",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Google Cloud library translation failed: %s", exc)

    # -- Try back-end 3: MyMemory free API ----------------------------------
    try:
        translated = _translate_mymemory(protected_text, bcp47_lang)
        restored = restore_technical_terms(translated, term_mapping)
        return TranslationResult(
            text=restored,
            success=True,
            backend="mymemory",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("MyMemory translation failed: %s", exc)

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
