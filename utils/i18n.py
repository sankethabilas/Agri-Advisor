# -*- coding: utf-8 -*-
"""
utils/i18n.py
Agri-Advisor -- Task T-17.1 & T-17.2: Static UI String Table.

All user-visible UI copy (labels, placeholders, buttons, block headings,
error messages) lives here.  Dynamic advisory *content* is translated at
render-time by utils.translator (T-17.3/T-17.4); this module covers
only static shell strings.

Usage
-----
    from utils.i18n import get_string, get_all_strings, SUPPORTED_LANGUAGES

    submit_label = get_string("btn_submit", lang_code)
    all_strings  = get_all_strings(lang_code)   # full dict, en-backed

Key naming convention
---------------------
    lbl_*    form labels / section headings
    ph_*     placeholder text for inputs
    btn_*    button labels
    blk_*    eight-block advisory section headings
    err_*    error / warning messages
    info_*   informational / toast strings

Every key MUST exist in all three locales. Missing keys fall back to "en"
then to the raw key string so the UI never silently breaks.
"""
from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Supported locales
# ---------------------------------------------------------------------------
SUPPORTED_LANGUAGES: Final[dict[str, str]] = {
    "English":          "en",
    "Sinhala":          "si",
    "Tamil":            "ta",
}

# Reverse map  code -> display label  (useful for UI badges / session panel)
LANGUAGE_LABELS: Final[dict[str, str]] = {v: k for k, v in SUPPORTED_LANGUAGES.items()}

# ---------------------------------------------------------------------------
# Master string table
# ---------------------------------------------------------------------------
UI_STRINGS: Final[dict[str, dict[str, str]]] = {

    # ========================================================================
    # ENGLISH  (en)
    # ========================================================================
    "en": {
        # -- App shell -------------------------------------------------------
        "app_title":                "Agri-Advisor",
        "app_subtitle":             "Smart Farming Assistant",
        "app_tagline":              "Helping Sri Lankan farmers grow better crops",

        # -- Language selector -----------------------------------------------
        "lbl_language":             "\U0001f310 Language",

        # -- Input form labels -----------------------------------------------
        "lbl_district":             "\U0001f4cd Your District",
        "lbl_crop":                 "\U0001f33e Crop Type (optional)",
        "lbl_query":                "Describe your crop problem",
        "lbl_char_counter":         "{count} / 1\u202f000 characters",

        # -- Input placeholders ---------------------------------------------
        "ph_query": (
            "e.g. My paddy has yellowing leaves with small brown spots. "
            "What disease is this and how should I treat it?"
        ),

        # -- Buttons --------------------------------------------------------
        "btn_submit":               "\U0001f50d Ask Agri-Advisor",
        "btn_clear":                "\U0001f5d1 Clear conversation",
        "btn_helpful_yes":          "\U0001f44d Yes",
        "btn_helpful_no":           "\U0001f44e No",

        # -- Advisory report headings ---------------------------------------
        "report_heading":           "\U0001f33e Agricultural Advisory Report",
        "report_followup": (
            "\U0001f4ac **Have another question?** Type your follow-up in the "
            "box above and click **Ask Agri-Advisor** \u2014 your conversation "
            "context will be remembered."
        ),
        "report_feedback":          "**Was this advice helpful?**",

        # -- Eight-block section headings (T-17.2) --------------------------
        "blk_diagnosis":            "Block 1 \u2014 Disease Diagnosis",
        "blk_treatment":            "Block 2 \u2014 Immediate Treatment",
        "blk_prevention":           "Block 3 \u2014 Prevention",
        "blk_weather":              "Block 4 \u2014 Weather Advisory",
        "blk_sources":              "Block 5 \u2014 Sources",
        "blk_disclaimer":           "Block 6 \u2014 Disclaimer",
        "blk_why":                  "Block 7 \u2014 Why? Explanation",
        "blk_raw_answer":           "Advisory",

        # -- Block sub-labels -----------------------------------------------
        "lbl_severity":             "Severity:",
        "lbl_confidence":           "Confidence:",
        "lbl_symptoms":             "Symptoms confirmed:",
        "lbl_differentials":        "Differential diagnoses:",
        "lbl_urgency":              "Urgency:",
        "lbl_application":          "Application:",
        "lbl_dosage":               "Dosage:",
        "lbl_frequency":            "Frequency:",
        "lbl_action_window":        "Action window:",
        "lbl_risk":                 "Risk level:",
        "lbl_source_type":          "Type:",
        "lbl_systems":              "Systems:",
        "lbl_intent":               "Intent:",
        "lbl_response_time":        "Response Time:",

        # -- Sidebar / session panel ----------------------------------------
        "sidebar_heading":          "\u2699\ufe0f Session Info",
        "lbl_user_id":              "**User ID:**",
        "lbl_session_id":           "**Session ID:**",
        "lbl_language_code":        "**Language:**",
        "lbl_turns":                "**Turns:**",

        # -- Demo / fallback banners ----------------------------------------
        "demo_mode_warning": (
            "\u26a0\ufe0f **Demo Mode** \u2014 The Agri-Advisor server is not running. "
            "Displaying sample advisory data so you can explore the interface."
        ),

        # -- Error messages -------------------------------------------------
        "err_empty_query":          "\u274c Please describe your crop problem before submitting.",
        "err_api_unavailable":      "\U0001f534 The advisory service is currently unreachable.",
        "err_unknown":              "\u26a0\ufe0f An unexpected error occurred. Please try again.",
        "err_char_limit":           "Character limit reached (1\u202f000 max).",

        # -- Translation / i18n notices (T-17.7) ----------------------------
        "info_translation_warn": (
            "\u26a0\ufe0f Translation service unavailable \u2014 "
            "showing original English advisory."
        ),
        "info_translation_partial": (
            "\u2139\ufe0f Some sections could not be translated and are shown in English."
        ),

        # -- Misc -----------------------------------------------------------
        "lbl_details_expander":     "\U0001f50d Response Details",
        "lbl_why_expander":         "\U0001f4a1 Why did Agri-Advisor suggest this?",
        "lbl_helpful_toast_yes":    "Thank you for your feedback!",
        "lbl_helpful_toast_no":     "Sorry to hear that. We\u2019ll keep improving!",
        "lbl_no_sources":           "No peer-reviewed sources were cited for this advisory.",
    },

    # ========================================================================
    # SINHALA  (si)
    # ========================================================================
    "si": {
        "app_title":                "\u0d9a\u0dd8\u0dc2\u0dd2-\u0d8b\u0db4\u0daf\u0dda\u0dc1\u0d9a",
        "app_subtitle":             "\u0dc3\u0dca\u0db8\u0dcf\u0dbb\u0dca\u0da7\u0dca \u0d9c\u0ddc\u0dc0\u0dd2\u0dad\u0dd0\u0db1\u0dca \u0dc3\u0dc4\u0dcf\u0dba\u0d9a\u0dba\u0dcf",
        "app_tagline":              "\u0dc1\u0dca\u200d\u0dbb\u0dd3 \u0dbd\u0dcf\u0d82\u0d9a\u0dd2\u0d9a \u0d9c\u0ddc\u0dc5\u0dd3\u0db1\u0dca\u0da7 \u0dc0\u0dda\u0daf\u0dcf \u0dc4\u0ddc\u0d82\u0daf \u0db6\u0ddc\u0d9c \u0dc5\u0d9c\u0dcf \u0d9a\u0dd2\u0dbb\u0dd3\u0db8\u0da7 \u0dc3\u0dc4\u0dcf\u0dba",
        "lbl_language":             "\U0001f310 \u0db7\u0dcf\u0dc2\u0dcf\u0dc0",
        "lbl_district":             "\U0001f4cd \u0d94\u0db6\u0dda \u0daf\u0dd2\u0dc3\u0dca\u0dad\u0dca\u200d\u0dbb\u0dd2\u0d9a\u0dca\u0d9a\u0dba",
        "lbl_crop":                 "\U0001f33e \u0db6\u0ddd\u0d9c \u0dc0\u0dbb\u0dca\u0d9c\u0dba (\u0d85\u0dad\u0dca\u200d\u0dba\u0dc5\u0dc1\u0dca\u200d\u0dba \u0db1\u0ddc\u0dc0\u0dda)",
        "lbl_query":                "\u0d94\u0db6\u0dda \u0db6\u0ddd\u0d9c \u0d9c\u0dd0\u0da7\u0dbd\u0dd4\u0dc0 \u0dc5\u0dd2\u0dc3\u0dca\u0dad\u0dbb \u0d9a\u0dbb\u0db1\u0dca\u0db1",
        "lbl_char_counter":         "{count} / 1\u202f000 \u0d85\u0d9a\u0dca\u0dc2\u0dbb",
        "ph_query": (
            "\u0d8b\u0daf\u0dcf: \u0db8\u0d9c\u0dda \u0dc5\u0dd3 \u0dc4\u0ddc\u0dbd\u0dca \u0d9a\u0dc4 \u0db4\u0dd0\u0dc4\u0dd0 \u0d9c\u0db1\u0dca\u0db1\u0dcf \u0d85\u0dad\u0dbb \u0d9a\u0dd4\u0dda\u0daf\u0dcf \u0daf\u0dd4\u0db9\u0dd4\u0dbb\u0dd4 \u0dbd\u0db4 \u0d87\u0dad. "
            "\u0db8\u0dd9\u0dba \u0d9a\u0dd4\u0db8\u0db1 \u0dbb\u0ddd\u0d9c\u0dba\u0daf, \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0d9a\u0dcf\u0dbb \u0d9a\u0dbb\u0db1\u0dca\u0db1\u0dda \u0d9a\u0dda\u0dc3\u0daf?"
        ),
        "btn_submit":               "\U0001f50d \u0d9a\u0dd8\u0dc2\u0dd2-\u0d8b\u0db4\u0daf\u0dda\u0dc1\u0d9a\u0dba\u0dd9\u0db1\u0dca \u0d85\u0dc3\u0db1\u0dca\u0db1",
        "btn_clear":                "\U0001f5d1 \u0dc3\u0d82\u0dc5\u0dcf\u0daf\u0dba \u0db8\u0d9a\u0db1\u0dca\u0db1",
        "btn_helpful_yes":          "\U0001f44d \u0d94\u0dc5\u0dca",
        "btn_helpful_no":           "\U0001f44e \u0db1\u0dd0\u0dc4\u0dd0",
        "report_heading":           "\U0001f33e \u0d9a\u0dd8\u0dc2\u0dd2\u0d9a\u0dcf\u0dbb\u0dca\u0db8\u0dd2\u0d9a \u0d8b\u0db4\u0daf\u0dda\u0dc1 \u0dc5\u0dcf\u0dbb\u0dca\u0dad\u0dcf\u0dc0",
        "report_followup": (
            "\U0001f4ac **\u0dad\u0dc0\u0dad\u0dca \u0db4\u0dca\u200d\u0dbb\u0dc1\u0dca\u0db1\u0dba\u0d9a\u0dca \u0dad\u0dd2\u0db6\u0dda\u0daf?** \u0d89\u0dc4\u0dad \u0d9a\u0ddc\u0da7\u0dd4\u0dc0\u0dda \u0d94\u0db6\u0dda \u0db4\u0dc3\u0dd4 \u0dc5\u0dd2\u0db8\u0dc3\u0dd3\u0db8 \u0da7\u0dba\u0dd2\u0db4\u0dca \u0d9a\u0dbb "
            "**\u0d9a\u0dd8\u0dc2\u0dd2-\u0d8b\u0db4\u0daf\u0dda\u0dc1\u0d9a\u0dba\u0dd9\u0db1\u0dca \u0d85\u0dc3\u0db1\u0dca\u0db1** \u0d9a\u0dca\u0dbd\u0dd2\u0d9a\u0dca \u0d9a\u0dbb\u0db1\u0dca\u0db1 \u2014 \u0d94\u0db6\u0dda \u0dc3\u0d82\u0dc5\u0dcf\u0daf \u0dc3\u0db1\u0dca\u0daf\u0dbb\u0dca\u0db7\u0dba \u0db8\u0dad\u0d9a\u0dba\u0dda \u0dad\u0db6\u0dcf \u0d9c\u0dd0\u0db1\u0dda."
        ),
        "report_feedback":          "**\u0db8\u0dd9\u0db8 \u0d8b\u0db4\u0daf\u0dd9\u0dc3 \u0db4\u0dca\u200d\u0dbb\u0dba\u0ddd\u0da2\u0db1\u0dc0\u0dad\u0daf?**",
        "blk_diagnosis":            "\u0d9a\u0ddc\u0da7\u0dc3 1 \u2014 \u0dbb\u0ddd\u0d9c \u0dc4\u0dda\u0daf\u0dd4\u0db1\u0dcf\u0d9c\u0dd0\u0db1\u0dd3\u0db8",
        "blk_treatment":            "\u0d9a\u0ddc\u0da7\u0dc3 2 \u2014 \u0d9a\u0dca\u0dc2\u0dab\u0dd2\u0d9a \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0d9a\u0dcf\u0dbb\u0dba",
        "blk_prevention":           "\u0d9a\u0ddc\u0da7\u0dc3 3 \u2014 \u0dc5\u0dd0\u0dbd\u0dd0\u0d9a\u0dca\u0dc5\u0dd3\u0db8",
        "blk_weather":              "\u0d9a\u0ddc\u0da7\u0dc3 4 \u2014 \u0d9a\u0dcf\u0dbd\u0d9c\u0dd4\u0dab \u0d8b\u0db4\u0daf\u0dda\u0dc1\u0dba",
        "blk_sources":              "\u0d9a\u0ddc\u0da7\u0dc3 5 \u2014 \u0db4\u0dca\u200d\u0dbb\u0db7\u0dc5\u0dba\u0db1\u0dca",
        "blk_disclaimer":           "\u0d9a\u0ddc\u0da7\u0dc3 6 \u2014 \u0dc5\u0d9c\u0d9a\u0dd3\u0db8\u0dca \u0d85\u0dc3\u0dca\u0dc5\u0dd3\u0db8",
        "blk_why":                  "\u0d9a\u0ddc\u0da7\u0dc3 7 \u2014 \u0d87\u0dba\u0dd2? \u0db4\u0dd0\u0dc4\u0dd0\u0daf\u0dd2\u0dbd\u0dd3 \u0d9a\u0dd2\u0dbb\u0dd3\u0db8",
        "blk_raw_answer":           "\u0d8b\u0db4\u0daf\u0dda\u0dc1\u0dba",
        "lbl_severity":             "\u0db6\u0dbb\u0db4\u0dad\u0dbd\u0d9a\u0db8:",
        "lbl_confidence":           "\u0dc5\u0dd2\u0dc1\u0dca\u0dc5\u0dcf\u0dc3\u0dba:",
        "lbl_symptoms":             "\u0dad\u0dc4\u0dc5\u0dd4\u0dbb\u0dd4 \u0dbb\u0ddd\u0d9c \u0dbd\u0d9a\u0dca\u0dc2\u0dab:",
        "lbl_differentials":        "\u0d85\u0db1\u0dda\u0d9a\u0dd4\u0dad\u0dca \u0d91 \u0dc4\u0dcf \u0dc3\u0db8\u0dcf\u0db1 \u0dbb\u0ddd\u0d9c:",
        "lbl_urgency":              "\u0dc4\u0daf\u0dd2\u0dc3\u0dd2\u0d9a\u0db8:",
        "lbl_application":          "\u0dba\u0dd9\u0daf\u0dd3\u0db8:",
        "lbl_dosage":               "\u0db4\u0dca\u200d\u0dbb\u0db8\u0dcf\u0dab\u0dba:",
        "lbl_frequency":            "\u0db1\u0dd2\u0dad\u0dd2\u0dad\u0dcf\u0dc5:",
        "lbl_action_window":        "\u0d9a\u0dca\u200d\u0dbb\u0dd2\u0dba\u0dcf \u0d9a\u0dcf\u0dbd\u0dba:",
        "lbl_risk":                 "\u0d85\u0dc5\u0daf\u0dcf\u0db1\u0db8\u0dca \u0db8\u0da7\u0dca\u0da7\u0db8:",
        "lbl_source_type":          "\u0dc5\u0dbb\u0dca\u0d9c\u0dba:",
        "lbl_systems":              "\u0db4\u0daf\u0dca\u0daa\u0dad\u0dd2:",
        "lbl_intent":               "\u0d85\u0db7\u0dd2\u0db4\u0dca\u200d\u0dbb\u0dcf\u0dba:",
        "lbl_response_time":        "\u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0da0\u0dcf\u0dbb \u0d9a\u0dcf\u0dbd\u0dba:",
        "sidebar_heading":          "\u2699\ufe0f \u0dc3\u0dd0\u0dc3\u0dd2 \u0dad\u0ddc\u0dbb\u0dad\u0dd4\u0dbb\u0dd4",
        "lbl_user_id":              "**\u0db4\u0dbb\u0dd2\u0dc1\u0dd3\u0dbd\u0d9a \u0dc4\u0dd0\u0daf\u0dd4\u0db1\u0dd4\u0db8:**",
        "lbl_session_id":           "**\u0dc3\u0dd0\u0dc3\u0dd2 \u0dc4\u0dd0\u0daf\u0dd4\u0db1\u0dd4\u0db8:**",
        "lbl_language_code":        "**\u0db7\u0dcf\u0dc2\u0dcf\u0dc0:**",
        "lbl_turns":                "**\u0dc4\u0dd0\u0dbb\u0dc5\u0dd3\u0db8\u0dca:**",
        "demo_mode_warning": (
            "\u26a0\ufe0f **Demo Mode** \u2014 Agri-Advisor \u0dc3\u0dda\u0dc5\u0dcf\u0daf\u0dcf\u0dba\u0d9a\u0dba \u0d9a\u0dca\u200d\u0dbb\u0dd2\u0dba\u0dcf\u0dad\u0dca\u0db8\u0d9a \u0db1\u0ddc\u0dc0\u0dda. "
            "\u0db1\u0dd2\u0dbb\u0dd6\u0db4\u0dab \u0d8b\u0db4\u0daf\u0dda\u0dc1 \u0daf\u0dad\u0dca \u0db4\u0dd9\u0db1\u0dca\u0dc5\u0db1\u0dd4 \u0dbd\u0dd0\u0db6\u0dda."
        ),
        "err_empty_query":          "\u274c \u0d89\u0daf\u0dd2\u0dbb\u0dd2\u0db4\u0dad\u0dca \u0d9a\u0dd2\u0dbb\u0dd3\u0db8\u0da7 \u0db4\u0dd9\u0dbb \u0d94\u0db6\u0dda \u0db6\u0ddd\u0d9c \u0d9a\u0dd0\u0da7\u0dbd\u0dd4\u0dc0 \u0dc5\u0dd2\u0dc3\u0dca\u0dad\u0dbb \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
        "err_api_unavailable":      "\U0001f534 \u0d8b\u0db4\u0daf\u0dda\u0dc1 \u0dc3\u0dda\u0dc5\u0dcf\u0dc0 \u0daf\u0dd0\u0db1\u0da7 \u0dbd\u0d9f\u0dcf \u0dc5\u0dd2\u0dba \u0db1\u0ddc\u0dc4\u0dd0\u0d9a.",
        "err_unknown":              "\u26a0\ufe0f \u0d85\u0db1\u0db4\u0dda\u0d9a\u0dca\u0dc2\u0dd2\u0dad \u0daf\u0ddd\u0dc2\u0dba\u0d9a\u0dca \u0dc3\u0dd2\u0daf\u0dd4 \u0dc5\u0dd2\u0dba. \u0db1\u0dd0\u0dc5\u0dad \u0d8b\u0dad\u0dca\u0dc3\u0dcf\u0dc4 \u0d9a\u0dbb\u0db1\u0dca\u0db1.",
        "err_char_limit":           "\u0d85\u0d9a\u0dca\u0dc2\u0dbb \u0dc3\u0dd3\u0db8\u0dcf\u0dc0\u0da7 \u0dbd\u0d9f\u0dcf \u0dc5\u0dd2\u0dba (\u0d8b\u0db4\u0dbb\u0dd2\u0db8 1\u202f000).",
        "info_translation_warn":    "\u26a0\ufe0f \u0db4\u0dbb\u0dd2\u0dc5\u0dbb\u0dca\u0dad\u0db1 \u0dc3\u0dda\u0dc5\u0dcf\u0dc0 \u0dbd\u0db6\u0dcf \u0d9c\u0dad \u0db1\u0ddc\u0dc4\u0dd0\u0d9a\u0dd2\u0dba\u0dcf \u2014 \u0db8\u0dd6\u0dbd \u0d89\u0d82\u0d9c\u0dca\u200d\u0dbb\u0dd3\u0dc3\u0dd2 \u0d8b\u0db4\u0daf\u0dda\u0dc1\u0dba \u0db4\u0dd9\u0db1\u0dca\u0dc5\u0db1\u0dd4 \u0dbd\u0dd0\u0db6\u0dda.",
        "info_translation_partial": "\u2139\ufe0f \u0dc3\u0db8\u0dc4\u0dbb \u0d9a\u0ddc\u0da7\u0dc3\u0dca \u0db4\u0dbb\u0dd2\u0dc5\u0dbb\u0dca\u0dad\u0db1\u0dba \u0d9a\u0dbd \u0db1\u0ddc\u0dc4\u0dd0\u0d9a\u0dd2 \u0d85\u0dad\u0dbb \u0d89\u0d82\u0d9c\u0dca\u200d\u0dbb\u0dd3\u0dc3\u0dd2\u0dba\u0dd9\u0db1\u0dca \u0db4\u0dd9\u0db1\u0dca\u0dc5\u0db1\u0dd4 \u0dbd\u0dd0\u0db6\u0dda.",
        "lbl_details_expander":     "\U0001f50d \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0da0\u0dcf\u0dbb \u0dc5\u0dd2\u0dc3\u0dca\u0dad\u0dbb",
        "lbl_why_expander":         "\U0001f4a1 \u0d9a\u0dd8\u0dc2\u0dd2-\u0d8b\u0db4\u0daf\u0dda\u0dc1\u0d9a\u0dba\u0dcf \u0db8\u0dd9\u0dba \u0dba\u0ddd\u0da2\u0db1\u0dcf \u0d9a\u0dbd\u0dda \u0d87\u0dba\u0dd2?",
        "lbl_helpful_toast_yes":    "\u0d94\u0db6\u0dda \u0db4\u0dca\u200d\u0dbb\u0dad\u0dd2\u0db4\u0ddd\u0dc2\u0dab\u0dba\u0da7 \u0dc3\u0dca\u0dad\u0dd6\u0dad\u0dd2\u0dba\u0dd2!",
        "lbl_helpful_toast_no":     "\u0d91 \u0d9c\u0dd0\u0db1 \u0d9a\u0dab\u0d9c\u0dcf\u0da7\u0dd4\u0dba\u0dd2. \u0d85\u0db4\u0dd2 \u0daf\u0dd2\u0d9c\u0da7\u0db8 \u0dc5\u0dd0\u0daf\u0dd2\u0daf\u0dd2\u0dba\u0dd4\u0dab\u0dd4 \u0d9a\u0dbb\u0db1\u0dca\u0db1\u0dda\u0db8\u0dd4!",
        "lbl_no_sources":           "\u0db8\u0dd9\u0db8 \u0d8b\u0db4\u0daf\u0dda\u0dc1\u0dba \u0dc3\u0daf\u0dc4\u0dcf \u0dc3\u0db8 \u0d9a\u0dbb\u0db1 \u0dbd\u0daf \u0db4\u0dca\u200d\u0dbb\u0db7\u0dc5\u0dba\u0db1\u0dca \u0d8b\u0db4\u0dd4\u0da7\u0dcf \u0db1\u0ddc\u0daf\u0d9a\u0dca\u0dc5\u0dcf \u0d87\u0dad.",
    },

    # ========================================================================
    # TAMIL  (ta)
    # ========================================================================
    "ta": {
        "app_title":                "\u0bb5\u0bc7\u0bb3\u0bbe\u0ba3\u0bcd-\u0b86\u0bb2\u0bcb\u0b9a\u0b95\u0bb0\u0bcd",
        "app_subtitle":             "\u0bb8\u0bcd\u0bae\u0bbe\u0bb0\u0bcd\u0b9f\u0bcd \u0bb5\u0bbf\u0bb5\u0b9a\u0bbe\u0baf \u0b89\u0ba4\u0bb5\u0bbf\u0baf\u0bbe\u0bb3\u0bb0\u0bcd",
        "app_tagline":              "\u0b87\u0bb2\u0b99\u0bcd\u0b95\u0bc8 \u0bb5\u0bbf\u0bb5\u0b9a\u0bbe\u0baf\u0bbf\u0b95\u0bb3\u0bcd \u0b9a\u0bbf\u0bb1\u0ba8\u0bcd\u0ba4 \u0baa\u0baf\u0bbf\u0bb0\u0bcd\u0b95\u0bb3\u0bc8 \u0bb5\u0bb3\u0bb0\u0bcd\u0b95\u0bcd\u0b95 \u0b89\u0ba4\u0bb5\u0bc1\u0b95\u0bbf\u0bb1\u0ba4\u0bc1",
        "lbl_language":             "\U0001f310 \u0bae\u0bca\u0bb4\u0bbf",
        "lbl_district":             "\U0001f4cd \u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0bae\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0bae\u0bcd",
        "lbl_crop":                 "\U0001f33e \u0baa\u0baf\u0bbf\u0bb0\u0bcd \u0bb5\u0b95\u0bc8 (\u0bb5\u0bbf\u0bb0\u0bc1\u0bae\u0bcd\u0baa\u0bbf\u0ba9\u0bbe\u0bb2\u0bcd)",
        "lbl_query":                "\u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0baa\u0baf\u0bbf\u0bb0\u0bcd \u0baa\u0bbf\u0bb0\u0b9a\u0bcd\u0b9a\u0ba9\u0bc8\u0baf\u0bc8 \u0bb5\u0bbf\u0bb5\u0bb0\u0bbf\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd",
        "lbl_char_counter":         "{count} / 1\u202f000 \u0b8e\u0bb4\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1\u0b95\u0bb3\u0bcd",
        "ph_query": (
            "\u0b8e.\u0b95\u0bbe. \u0b8e\u0ba9\u0bcd \u0ba8\u0bc6\u0bb2\u0bcd \u0b87\u0bb2\u0bc8\u0b95\u0bb3\u0bcd \u0bae\u0b9e\u0bcd\u0b9a\u0bb3\u0bbe\u0b95\u0bbf \u0b9a\u0bbf\u0bb1\u0bbf\u0baf \u0baa\u0bb4\u0bc1\u0baa\u0bcd\u0baa\u0bc1 \u0baa\u0bc1\u0bb3\u0bcd\u0bb3\u0bbf\u0b95\u0bb3\u0bcd \u0b89\u0bb3\u0bcd\u0bb3\u0ba9. "
            "\u0b87\u0ba4\u0bc1 \u0b8e\u0ba9\u0bcd\u0ba9 \u0ba8\u0bcb\u0baf\u0bcd, \u0b8e\u0bb5\u0bcd\u0bb5\u0bbe\u0bb1\u0bc1 \u0b9a\u0bbf\u0b95\u0bbf\u0b9a\u0bcd\u0b9a\u0bc8\u0baf\u0bb3\u0bbf\u0b95\u0bcd\u0b95 \u0bb5\u0bc7\u0ba3\u0bcd\u0b9f\u0bc1\u0bae\u0bcd?"
        ),
        "btn_submit":               "\U0001f50d \u0bb5\u0bc7\u0bb3\u0bbe\u0ba3\u0bcd-\u0b86\u0bb2\u0bcb\u0b9a\u0b95\u0bb0\u0bbf\u0b9f\u0bae\u0bcd \u0b95\u0bc7\u0bb3\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd",
        "btn_clear":                "\U0001f5d1 \u0b89\u0bb0\u0bc8\u0baf\u0bbe\u0b9f\u0bb2\u0bc8 \u0b85\u0bb4\u0bbf\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd",
        "btn_helpful_yes":          "\U0001f44d \u0b86\u0bae\u0bcd",
        "btn_helpful_no":           "\U0001f44e \u0b87\u0bb2\u0bcd\u0bb2\u0bc8",
        "report_heading":           "\U0001f33e \u0bb5\u0bc7\u0bb3\u0bbe\u0ba3\u0bcd \u0b86\u0bb2\u0bcb\u0b9a\u0ba9\u0bc8 \u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8",
        "report_followup": (
            "\U0001f4ac **\u0bae\u0bc7\u0bb2\u0bc1\u0bae\u0bcd \u0b95\u0bc7\u0bb3\u0bcd\u0bb5\u0bbf \u0b89\u0bb3\u0bcd\u0bb3\u0ba4\u0bbe?** \u0bae\u0bc7\u0bb2\u0bc7 \u0b89\u0bb3\u0bcd\u0bb3 \u0baa\u0bc6\u0b9f\u0bcd\u0b9f\u0bbf\u0baf\u0bbf\u0bb2\u0bcd \u0ba4\u0b9f\u0bcd\u0b9f\u0b9a\u0bcd\u0b9a\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0ba4\u0bc1 "
            "**\u0bb5\u0bc7\u0bb3\u0bbe\u0ba3\u0bcd-\u0b86\u0bb2\u0bcb\u0b9a\u0b95\u0bb0\u0bbf\u0b9f\u0bae\u0bcd \u0b95\u0bc7\u0bb3\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd** \u0b95\u0bbf\u0bb3\u0bbf\u0b95\u0bcd \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u2014 "
            "\u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0b89\u0bb0\u0bc8\u0baf\u0bbe\u0b9f\u0bb2\u0bcd \u0b9a\u0bc2\u0bb4\u0bb2\u0bcd \u0ba8\u0bbf\u0ba9\u0bc8\u0bb5\u0bbf\u0bb2\u0bcd \u0bb5\u0bc8\u0b95\u0bcd\u0b95\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0bae\u0bcd."
        ),
        "report_feedback":          "**\u0b87\u0ba8\u0bcd\u0ba4 \u0b86\u0bb2\u0bcb\u0b9a\u0ba9\u0bc8 \u0b89\u0ba4\u0bb5\u0bbf\u0baf\u0ba4\u0bbe?**",
        "blk_diagnosis":            "\u0baa\u0b95\u0bc1\u0ba4\u0bbf 1 \u2014 \u0ba8\u0bcb\u0baf\u0bcd \u0b95\u0ba3\u0bcd\u0b9f\u0bb1\u0bbf\u0ba4\u0bb2\u0bcd",
        "blk_treatment":            "\u0baa\u0b95\u0bc1\u0ba4\u0bbf 2 \u2014 \u0b89\u0b9f\u0ba9\u0b9f\u0bbf \u0b9a\u0bbf\u0b95\u0bbf\u0b9a\u0bcd\u0b9a\u0bc8",
        "blk_prevention":           "\u0baa\u0b95\u0bc1\u0ba4\u0bbf 3 \u2014 \u0ba4\u0b9f\u0bc1\u0baa\u0bcd\u0baa\u0bc1 \u0ba8\u0b9f\u0bb5\u0b9f\u0bbf\u0b95\u0bcd\u0b95\u0bc8\u0b95\u0bb3\u0bcd",
        "blk_weather":              "\u0baa\u0b95\u0bc1\u0ba4\u0bbf 4 \u2014 \u0bb5\u0bbe\u0ba9\u0bbf\u0bb2\u0bc8 \u0b86\u0bb2\u0bcb\u0b9a\u0ba9\u0bc8",
        "blk_sources":              "\u0baa\u0b95\u0bc1\u0ba4\u0bbf 5 \u2014 \u0b86\u0ba4\u0bbe\u0bb0\u0b99\u0bcd\u0b95\u0bb3\u0bcd",
        "blk_disclaimer":           "\u0baa\u0b95\u0bc1\u0ba4\u0bbf 6 \u2014 \u0bae\u0bb1\u0bc1\u0baa\u0bcd\u0baa\u0bc1",
        "blk_why":                  "\u0baa\u0b95\u0bc1\u0ba4\u0bbf 7 \u2014 \u0b8f\u0ba9\u0bcd? \u0bb5\u0bbf\u0bb3\u0b95\u0bcd\u0b95\u0bae\u0bcd",
        "blk_raw_answer":           "\u0b86\u0bb2\u0bcb\u0b9a\u0ba9\u0bc8",
        "lbl_severity":             "\u0ba4\u0bc0\u0bb5\u0bbf\u0bb0\u0bae\u0bcd:",
        "lbl_confidence":           "\u0ba8\u0bae\u0bcd\u0baa\u0b95\u0ba4\u0bcd\u0ba4\u0ba9\u0bcd\u0bae\u0bc8:",
        "lbl_symptoms":             "\u0b89\u0bb1\u0bc1\u0ba4\u0bbf\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0ba4\u0bcd\u0ba4\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f \u0b85\u0bb1\u0bbf\u0b95\u0bc1\u0bb1\u0bbf\u0b95\u0bb3\u0bcd:",
        "lbl_differentials":        "\u0bb5\u0bc7\u0bb1\u0bc1\u0baa\u0b9f\u0bcd\u0b9f \u0ba8\u0bcb\u0baf\u0bcd \u0b95\u0ba3\u0bcd\u0b9f\u0bb1\u0bbf\u0ba4\u0bb2\u0bcd\u0b95\u0bb3\u0bcd:",
        "lbl_urgency":              "\u0b85\u0bb5\u0b9a\u0bb0\u0bae\u0bcd:",
        "lbl_application":          "\u0baa\u0baf\u0ba9\u0bcd\u0baa\u0bbe\u0b9f\u0bc1:",
        "lbl_dosage":               "\u0b85\u0bb3\u0bb5\u0bc1:",
        "lbl_frequency":            "\u0b85\u0ba4\u0bbf\u0bb0\u0bcd\u0bb5\u0bc6\u0ba3\u0bcd:",
        "lbl_action_window":        "\u0b9a\u0bc6\u0baf\u0bb2\u0bcd \u0b95\u0bbe\u0bb2\u0bae\u0bcd:",
        "lbl_risk":                 "\u0b85\u0baa\u0bbe\u0baf \u0ba8\u0bbf\u0bb2\u0bc8:",
        "lbl_source_type":          "\u0bb5\u0b95\u0bc8:",
        "lbl_systems":              "\u0b85\u0bae\u0bc8\u0baa\u0bcd\u0baa\u0bc1\u0b95\u0bb3\u0bcd:",
        "lbl_intent":               "\u0ba8\u0bcb\u0b95\u0bcd\u0b95\u0bae\u0bcd:",
        "lbl_response_time":        "\u0bae\u0bb1\u0bc1\u0bae\u0bca\u0bb4\u0bbf \u0ba8\u0bc7\u0bb0\u0bae\u0bcd:",
        "sidebar_heading":          "\u2699\ufe0f \u0b85\u0bae\u0bb0\u0bcd\u0bb5\u0bc1 \u0ba4\u0b95\u0bb5\u0bb2\u0bcd",
        "lbl_user_id":              "**\u0baa\u0baf\u0ba9\u0bb0\u0bcd ID:**",
        "lbl_session_id":           "**\u0b85\u0bae\u0bb0\u0bcd\u0bb5\u0bc1 ID:**",
        "lbl_language_code":        "**\u0bae\u0bca\u0bb4\u0bbf:**",
        "lbl_turns":                "**\u0b9a\u0bc1\u0bb1\u0bcd\u0bb1\u0bc1\u0b95\u0bb3\u0bcd:**",
        "demo_mode_warning": (
            "\u26a0\ufe0f **Demo Mode** \u2014 Agri-Advisor \u0b9a\u0bc7\u0bb5\u0bc8\u0baf\u0b95\u0bae\u0bcd \u0b87\u0baf\u0b99\u0bcd\u0b95\u0bb5\u0bbf\u0bb2\u0bcd\u0bb2\u0bc8. "
            "\u0bae\u0bbe\u0ba4\u0bbf\u0bb0\u0bbf \u0b86\u0bb2\u0bcb\u0b9a\u0ba9\u0bc8 \u0ba4\u0bb0\u0bb5\u0bc1 \u0b95\u0bbe\u0b9f\u0bcd\u0b9f\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0b95\u0bbf\u0bb1\u0ba4\u0bc1."
        ),
        "err_empty_query":          "\u274c \u0b9a\u0bae\u0bb0\u0bcd\u0baa\u0bcd\u0baa\u0bbf\u0b95\u0bcd\u0b95\u0bc1\u0bae\u0bcd \u0bae\u0bc1\u0ba9\u0bcd \u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0baa\u0baf\u0bbf\u0bb0\u0bcd \u0baa\u0bbf\u0bb0\u0b9a\u0bcd\u0b9a\u0ba9\u0bc8\u0baf\u0bc8 \u0bb5\u0bbf\u0bb5\u0bb0\u0bbf\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd.",
        "err_api_unavailable":      "\U0001f534 \u0b86\u0bb2\u0bcb\u0b9a\u0ba9\u0bc8 \u0b9a\u0bc7\u0bb5\u0bc8 \u0ba4\u0bb1\u0bcd\u0baa\u0bcb\u0ba4\u0bc1 \u0b85\u0ba3\u0bc1\u0b95 \u0b87\u0baf\u0bb2\u0bb5\u0bbf\u0bb2\u0bcd\u0bb2\u0bc8.",
        "err_unknown":              "\u26a0\ufe0f \u0b8e\u0ba4\u0bbf\u0bb0\u0bcd\u0baa\u0bbe\u0bb0\u0bbe\u0ba4 \u0baa\u0bbf\u0bb4\u0bc8 \u0b8f\u0bb1\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0ba4\u0bc1. \u0bae\u0bc0\u0ba3\u0bcd\u0b9f\u0bc1\u0bae\u0bcd \u0bae\u0bc1\u0baf\u0bb1\u0bcd\u0b9a\u0bbf\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd.",
        "err_char_limit":           "\u0b8e\u0bb4\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1 \u0bb5\u0bb0\u0bae\u0bcd\u0baa\u0bc8 \u0b8e\u0b9f\u0bcd\u0b9f\u0bbf\u0baf\u0ba4\u0bc1 (\u0b85\u0ba4\u0bbf\u0b95\u0baa\u0b9f\u0bcd\u0b9a\u0bae\u0bcd 1\u202f000).",
        "info_translation_warn":    "\u26a0\ufe0f \u0bae\u0bca\u0bb4\u0bbf\u0baa\u0bc6\u0baf\u0bb0\u0bcd\u0baa\u0bcd\u0baa\u0bc1 \u0b9a\u0bc7\u0bb5\u0bc8 \u0b95\u0bbf\u0b9f\u0bc8\u0b95\u0bcd\u0b95\u0bb5\u0bbf\u0bb2\u0bcd\u0bb2\u0bc8 \u2014 \u0b86\u0b99\u0bcd\u0b95\u0bbf\u0bb2 \u0b86\u0bb2\u0bcb\u0b9a\u0ba9\u0bc8 \u0b95\u0bbe\u0b9f\u0bcd\u0b9f\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0b95\u0bbf\u0bb1\u0ba4\u0bc1.",
        "info_translation_partial": "\u2139\ufe0f \u0b9a\u0bbf\u0bb2 \u0baa\u0b95\u0bc1\u0ba4\u0bbf\u0b95\u0bb3\u0bc8 \u0bae\u0bca\u0bb4\u0bbf\u0baa\u0bc6\u0baf\u0bb0\u0bcd\u0b95\u0bcd\u0b95 \u0bae\u0bc1\u0b9f\u0bbf\u0baf\u0bb5\u0bbf\u0bb2\u0bcd\u0bb2\u0bc8, \u0b86\u0b99\u0bcd\u0b95\u0bbf\u0bb2\u0ba4\u0bcd\u0ba4\u0bbf\u0bb2\u0bcd \u0b95\u0bbe\u0b9f\u0bcd\u0b9f\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0b95\u0bbf\u0bb1\u0ba4\u0bc1.",
        "lbl_details_expander":     "\U0001f50d \u0bae\u0bb1\u0bc1\u0bae\u0bca\u0bb4\u0bbf \u0bb5\u0bbf\u0bb5\u0bb0\u0b99\u0bcd\u0b95\u0bb3\u0bcd",
        "lbl_why_expander":         "\U0001f4a1 \u0bb5\u0bc7\u0bb3\u0bbe\u0ba3\u0bcd-\u0b86\u0bb2\u0bcb\u0b9a\u0b95\u0bb0\u0bcd \u0b8f\u0ba9\u0bcd \u0b87\u0ba4\u0bc8 \u0baa\u0bb0\u0bbf\u0ba8\u0bcd\u0ba4\u0bc1\u0bb0\u0bc8\u0ba4\u0bcd\u0ba4\u0bbe\u0bb0\u0bcd?",
        "lbl_helpful_toast_yes":    "\u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0b95\u0bb0\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1\u0b95\u0bcd\u0b95\u0bc1 \u0ba8\u0ba9\u0bcd\u0bb1\u0bbf!",
        "lbl_helpful_toast_no":     "\u0bae\u0ba9\u0bcd\u0ba9\u0bbf\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd. \u0ba8\u0bbe\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0ba4\u0bca\u0b9f\u0bb0\u0bcd\u0ba8\u0bcd\u0ba4\u0bc1 \u0bae\u0bc7\u0bae\u0bcd\u0baa\u0b9f\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1\u0bb5\u0bcb\u0bae\u0bcd!",
        "lbl_no_sources":           "\u0b87\u0ba8\u0bcd\u0ba4 \u0b86\u0bb2\u0bcb\u0b9a\u0ba9\u0bc8\u0b95\u0bcd\u0b95\u0bc1 \u0b9a\u0b95 \u0bae\u0ba4\u0bbf\u0baa\u0bcd\u0baa\u0bbe\u0baf\u0bcd\u0bb5\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f \u0b86\u0ba4\u0bbe\u0bb0\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0b8e\u0ba4\u0bc1\u0bb5\u0bc1\u0bae\u0bcd \u0bae\u0bc7\u0bb1\u0bcd\u0b95\u0bcb\u0bb3\u0bcd \u0b95\u0bbe\u0b9f\u0bcd\u0b9f\u0baa\u0bcd\u0baa\u0b9f\u0bb5\u0bbf\u0bb2\u0bcd\u0bb2\u0bc8.",
    },
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_string(key: str, lang_code: str = "en") -> str:
    """
    Return the localised string for *key* in *lang_code*.

    Fallback order:
        1. Requested locale (lang_code)
        2. English ("en")
        3. Raw key string  -- safety net, should never happen in production

    Args:
        key:       The string key, e.g. "btn_submit".
        lang_code: ISO 639-1 locale code; one of "en", "si", "ta".

    Returns:
        The localised string, guaranteed to be non-empty.
    """
    # 1 -- Primary locale
    value = UI_STRINGS.get(lang_code, {}).get(key)
    if value is not None:
        return value
    # 2 -- English fallback
    value = UI_STRINGS.get("en", {}).get(key)
    if value is not None:
        return value
    # 3 -- Absolute last resort
    return key


def get_all_strings(lang_code: str = "en") -> dict[str, str]:
    """
    Return the full string table for *lang_code* merged on top of English
    so every possible key is always present.

    Useful when a renderer needs many strings without per-key calls.

    Args:
        lang_code: One of "en", "si", "ta".

    Returns:
        dict mapping every key to the best available translated string.
    """
    base = dict(UI_STRINGS.get("en", {}))
    if lang_code != "en":
        base.update(UI_STRINGS.get(lang_code, {}))
    return base
