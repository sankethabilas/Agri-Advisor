# -*- coding: utf-8 -*-
"""
utils/i18n.py
Agri-Advisor -- Task T-17.1 & T-17.2: Static UI String Table.
All user-visible UI copy (labels, placeholders, buttons, block headings,
error messages) lives here. Dynamic advisory *content* is translated at
render-time by utils.translator; this module covers only static shell strings.

Usage
-----
    from utils.i18n import get_string, get_all_strings, SUPPORTED_LANGUAGES
    submit_label = get_string("btn_submit", lang_code)
    all_strings  = get_all_strings(lang_code)   # full dict, en-backed

Key naming convention
---------------------
    lbl_*     form labels / section headings
    ph_*      placeholder text for inputs
    btn_*     button labels
    blk_*     eight-block advisory section headings
    err_*     error / warning messages
    info_*    informational / toast strings
"""
from __future__ import annotations
import re
from typing import Final

# ---------------------------------------------------------------------------
# Supported locales
# ---------------------------------------------------------------------------
SUPPORTED_LANGUAGES: Final[dict[str, str]] = {
    "English": "en",
    "Sinhala": "si",
    "Tamil":   "ta",
}

# Reverse map: code -> display label
LANGUAGE_LABELS: Final[dict[str, str]] = {
    v: k for k, v in SUPPORTED_LANGUAGES.items()}

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
        "lbl_language":             "🌐 Language",
        # -- Input form labels -----------------------------------------------
        "lbl_district":             "📍 Your District",
        "lbl_crop":                 "🌾 Crop Type (optional)",
        "lbl_query":                "Describe your crop problem",
        "lbl_char_counter":         "{count} / 1000 characters",
        # -- Input placeholders ---------------------------------------------
        "ph_query": (
            "e.g. My paddy has yellowing leaves with small brown spots. "
            "What disease is this and how should I treat it?"
        ),
        # -- Buttons --------------------------------------------------------
        "btn_submit":               "🔍 Ask Agri-Advisor",
        "btn_clear":                "🗑️ Clear conversation",
        "btn_helpful_yes":          "👍 Yes",
        "btn_helpful_no":           "👎 No",
        # -- Advisory report headings ---------------------------------------
        "report_heading":           "🌾 Agricultural Advisory Report",
        "report_followup": (
            "💬 **Have another question?** Type your follow-up in the "
            "box above and click **Ask Agri-Advisor** — your conversation "
            "context will be remembered."
        ),
        "report_feedback":          "**Was this advice helpful?**",
        # -- Eight-block section headings (T-17.2) --------------------------
        "blk_diagnosis":            "Block 1 — Disease Diagnosis",
        "blk_treatment":            "Block 2 — Immediate Treatment",
        "blk_prevention":           "Block 3 — Prevention",
        "blk_weather":              "Block 4 — Weather Advisory",
        "blk_sources":              "Block 5 — Sources",
        "blk_disclaimer":           "Block 6 — Disclaimer",
        "blk_why":                  "Block 7 — Why? Explanation",
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
        "sidebar_heading":          "⚙️ Session Info",
        "lbl_user_id":              "**User ID:**",
        "lbl_session_id":           "**Session ID:**",
        "lbl_language_code":        "**Language:**",
        "lbl_turns":                "**Turns:**",
        # -- Demo / fallback banners ----------------------------------------
        "demo_mode_warning": (
            "⚠️ **Demo Mode** — The Agri-Advisor server is not running. "
            "Displaying sample advisory data so you can explore the interface."
        ),
        # -- Error messages -------------------------------------------------
        "err_empty_query":          "❌ Please describe your crop problem before submitting.",
        "err_api_unavailable":      "🔴 The advisory service is currently unreachable.",
        "err_unknown":              "⚠️ An unexpected error occurred. Please try again.",
        "err_char_limit":           "Character limit reached (1000 max).",
        # -- Translation / i18n notices (T-17.7) ----------------------------
        "info_translation_warn": (
            "⚠️ Translation service unavailable — "
            "showing original English advisory."
        ),
        "info_translation_partial": (
            "ℹ️️ Some sections could not be translated and are shown in English."
        ),
        # -- Misc -----------------------------------------------------------
        "lbl_details_expander":     "🔍 Response Details",
        "lbl_why_expander":         "💡 Why did Agri-Advisor suggest this?",
        "lbl_helpful_toast_yes":    "Thank you for your feedback!",
        "lbl_helpful_toast_no":     "Sorry to hear that. We'll keep improving!",
        "lbl_no_sources":           "No peer-reviewed sources were cited for this advisory.",
        "sub_prevention":           "Long-term measures to prevent recurrence",
        "sub_why":                  "AI reasoning & confidence breakdown",
        "lbl_view_sources":         "View Sources",
        "lbl_risk_score":           "Disease Risk Score",
        "lbl_alert_valid":          "Alert Valid Until",
        "lbl_model_reasoning":      "Model Reasoning:",
        "lbl_confidence_by_agent":  "Confidence by Agent:",
        "lbl_systems_consulted":    "Systems consulted:",
        "lbl_partial_warning":      "Some specialist agents did not return details. The available advisory information is shown below; ask a follow-up question for more detail.",
        # -- T-20: Authentication strings -----------------------------------
        "auth_login_title":         "Welcome Back",
        "auth_login_subtitle":      "Sign in to your Agri-Advisor account",
        "auth_register_title":      "Create Your Account",
        "auth_register_subtitle":   "Join thousands of Sri Lankan farmers",
        "lbl_username":             "👤 Username",
        "lbl_password":             "🔑 Password",
        "lbl_confirm_password":     "🔑 Confirm Password",
        "lbl_full_name":            "Full Name",
        "lbl_phone_email":          "Phone Number or Email",
        "lbl_preferred_language":   "🌐 Preferred Language",
        "ph_username":              "e.g. saman_farmer",
        "ph_password":              "Min. 12 characters",
        "ph_confirm_password":      "Repeat your password",
        "ph_full_name":             "e.g. Saman Perera",
        "ph_phone_email":           "e.g. 0771234567 or saman@example.com",
        "btn_login":                "🔓 Sign In",
        "btn_register":             "🌱 Create Account",
        "btn_go_register":          "✏️ Create an account",
        "btn_go_login":             "🔓 Sign In",
        "btn_logout":               "🚪 Sign Out",
        "auth_switch_have_account": "Already have an account?",
        "auth_switch_new":          "New to Agri-Advisor?",
        "err_auth_invalid":         "❌ **Incorrect username or password.** Please check and try again.",
        "err_auth_expired":         "⏰ **Your session has expired.** Please sign in again to continue.",
        "err_auth_duplicate":       "❌ **An account with that username already exists.** Please choose a different username or sign in.",
        "err_auth_server":          "❌ **Something went wrong on our end.** Please try again shortly.",
        "err_auth_network":         "❌ **Connection problem.** Please check your network and try again.",
        "err_auth_rate_limit":      "❌ **Too many attempts.** Please wait a moment before trying again.",
        "info_register_username":   "Username: 3–254 characters, letters, digits, '.', '_', '@', '+', '-' only.",
        "info_register_password":   "Password: Minimum 12 characters.",
        "lbl_personal_info":        "👤 Personal Information",
        "lbl_account_creds":        "🔑 Account Credentials",
        "lbl_farming_context":      "🌾 Farming Context",
    },
    # ========================================================================
    # SINHALA  (si)
    # ========================================================================
    "si": {
        "app_title":                "කෘෂි-උපදේශක",
        "app_subtitle":             "ස්මාර්ට් ගොවිතැන් සහායකයා",
        "app_tagline":              "ශ්‍රී ලාංකික ගොවීන්ට වඩා හොඳ අස්වැන්නක් ලබා ගැනීමට සහාය වේ",
        "lbl_language":             "🌐 භාෂාව",
        "lbl_district":             "📍 ඔබේ දිස්ත්‍රික්කය",
        "lbl_crop":                 "🌾 බෝග වර්ගය (අත්‍යවශ්‍ය නොවේ)",
        "lbl_query":                "ඔබේ බෝග ගැටලුව විස්තර කරන්න",
        "lbl_char_counter":         "{count} / 1000 අක්ෂර",
        "ph_query": (
            "උදා: මගේ වී වගාවේ කොළ කහ පැහැ වී කුඩා දුඹුරු ලප ඇති වී තිබේ. "
            "මෙය කුමන රෝගයක්ද? ඊට ප්‍රතිකාර කරන්නේ කෙසේද?"
        ),
        "btn_submit":               "🔍 කෘෂි-උපදේශකගෙන් අසන්න",
        "btn_clear":                "🗑️ සංවාදය මකන්න",
        "btn_helpful_yes":          "👍 ඔවු",
        "btn_helpful_no":           "👎 නැත",
        "report_heading":           "🌾 කෘෂිකාර්මික උපදේශන වාර්තාව",
        "report_followup": (
            "💬 **තවත් ප්‍රශ්නයක් තිබේද?** ඉහත කොටුවේ ඔබේ පසු විමසීම ටයිප් කර "
            "**කෘෂි-උපදේශකගෙන් අසන්න** ක්ලික් කරන්න — ඔබේ සංවාද සන්දර්භය මතකයේ තබා ගනී."
        ),
        "report_feedback":          "**මෙම උපදෙස ප්‍රයෝජනවත්ද?**",
        "blk_diagnosis":            "කොටස 1 — රෝග විනිශ්චය",
        "blk_treatment":            "කොටස 2 — ක්ෂණික ප්‍රතිකාර",
        "blk_prevention":           "කොටස 3 — පූර්ව ආරක්ෂණ පියවර",
        "blk_weather":              "කොටස 4 — කාලගුණ උපදේශය",
        "blk_sources":              "කොටස 5 — තොරතුරු මූලාශ්‍ර",
        "blk_disclaimer":           "කොටස 6 — වගකීම් ලිහිල් කිරීම",
        "blk_why":                  "කොටස 7 — හේතු පැහැදිලි කිරීම",
        "blk_raw_answer":           "උපදේශය",
        "lbl_severity":             "බරපතලකම:",
        "lbl_confidence":           "විශ්වාසනීයත්වය:",
        "lbl_symptoms":             "තහවුරු වූ රෝග ලක්ෂණ:",
        "lbl_differentials":        "වෙනත් සමාන රෝග නිශ්චයන්:",
        "lbl_urgency":              "හදිසිභාවය:",
        "lbl_application":          "යෙදීම:",
        "lbl_dosage":               "ප්‍රමාණය:",
        "lbl_frequency":            "වාර ගණන:",
        "lbl_action_window":        "ක්‍රියාත්මක විය යුතු කාලය:",
        "lbl_risk":                 "අවදානම් මට්ටම:",
        "lbl_source_type":          "වර්ගය:",
        "lbl_systems":              "පද්ධති:",
        "lbl_intent":               "අභිප්‍රාය:",
        "lbl_response_time":        "ප්‍රතිචාර කාලය:",
        "sidebar_heading":          "⚙️ සැසි තොරතුරු",
        "lbl_user_id":              "**පරිශීලක ID:**",
        "lbl_session_id":           "**සැසි ID:**",
        "lbl_language_code":        "**භාෂාව:**",
        "lbl_turns":                "**වාර ගණන:**",
        "demo_mode_warning": (
            "⚠️ **Demo Mode** — කෘෂි-උපදේශක සේවාදායකය සක්‍රිය නැත. "
            "ආදර්ශ උපදේශන දත්ත පෙන්වනු ලැබේ."
        ),
        "err_empty_query":          "❌ ඉදිරිපත් කිරීමට පෙර ඔබේ බෝග ගැටලුව විස්තර කරන්න.",
        "err_api_unavailable":      "🔴 උපදේශන සේවාව දැනට ලබා ගත නොහැක.",
        "err_unknown":              "⚠️ අනපේක්ෂිත දෝෂයක් සිදු විය. නැවත උත්සාහ කරන්න.",
        "err_char_limit":           "අක්ෂර සීමාවට ළඟා විය (උපරිම 1000).",
        "info_translation_warn":    "⚠️ පරිවර්තන සේවාව ලබා ගත නොහැක — මුල් ඉංග්‍රීසි උපදේශය පෙන්වනු ලැබේ.",
        "info_translation_partial": "ℹ️ සමහර කොටස් පරිවර්තනය කළ නොහැකි වූ අතර ඒවා ඉංග්‍රීසියෙන් පෙන්වයි.",
        "lbl_details_expander":     "🔍 ප්‍රතිචාර විස්තර",
        "lbl_why_expander":         "💡 කෘෂි-උපදේශක මෙය යෝජනා කළේ ඇයි?",
        "lbl_helpful_toast_yes":    "ඔබේ ප්‍රතිපෝෂණයට ස්තූතියි!",
        "lbl_helpful_toast_no":     "කනගාටුයි. අපි තවදුරටත් වැඩිදියුණු කරන්නෙමු!",
        "lbl_no_sources":           "මෙම උපදේශය සඳහා මූලාශ්‍ර උපුටා දක්වා නැත.",
        "sub_prevention":           "නැවත ඇතිවීම වැළැක්වීම සඳහා දීර්ඝකාලීන පියවර",
        "sub_why":                  "AI තර්කනය සහ විශ්වාසනීයත්ව විග්‍රහය",
        "lbl_view_sources":         "මූලාශ්‍ර බලන්න",
        "lbl_risk_score":           "රෝග අවදානම් ලකුණු",
        "lbl_alert_valid":          "අනතුරු ඇඟවීම වලංගු කාලය",
        "lbl_model_reasoning":      "මාදිලි තර්කනය:",
        "lbl_confidence_by_agent":  "නියෝජිතයා අනුව විශ්වාසනීයත්වය:",
        "lbl_systems_consulted":    "විමසූ පද්ධති:",
        "lbl_partial_warning":      "සමහර විශේෂඥ නියෝජිතයින් තොරතුරු ලබා දී නැත. පවතින තොරතුරු පහත දැක්වේ; වැඩි විස්තර සඳහා පසු විමසුම් ප්‍රශ්නයක් අසන්න.",
        # -- T-20: Authentication (Sinhala) ---------------------------------
        "auth_login_title":         "සාදරයෙන් පිළිගනිමු",
        "auth_login_subtitle":      "ඔබේ කෘෂි-උපදේශක ගිණුමට ඇතුළු වන්න",
        "auth_register_title":      "නව ගිණුමක් තනන්න",
        "auth_register_subtitle":   "දහස් ගණනක් වූ ශ්‍රී ලාංකික ගොවි ප්‍රජාව හා එක්වන්න",
        "lbl_username":             "👤 පරිශීලක නාමය",
        "lbl_password":             "🔑 මුරපදය",
        "lbl_confirm_password":     "🔑 මුරපදය තහවුරු කරන්න",
        "lbl_full_name":            "සම්පූර්ණ නම",
        "lbl_phone_email":          "දුරකථන අංකය හෝ විද්‍යුත් තපෑල",
        "lbl_preferred_language":   "🌐 කැමති භාෂාව",
        "ph_username":              "උදා: saman_farmer",
        "ph_password":              "අවම අක්ෂර 12ක්",
        "ph_confirm_password":      "මුරපදය නැවත ටයිප් කරන්න",
        "ph_full_name":             "උදා: සමන් පෙරේරා",
        "ph_phone_email":           "උදා: 0771234567 හෝ saman@example.com",
        "btn_login":                "🔓 ඇතුළු වන්න",
        "btn_register":             "🌱 ගිණුම සාදන්න",
        "btn_go_register":          "✏️ ගිණුමක් සාදන්න",
        "btn_go_login":             "🔓 ඇතුළු වන්න",
        "btn_logout":               "🚪 නික්මෙන්න",
        "auth_switch_have_account": "දැනටමත් ගිණුමක් තිබේද?",
        "auth_switch_new":          "කෘෂි-උපදේශක වෙත නවකයෙක්ද?",
        "err_auth_invalid":         "❌ **පරිශීලක නාමය හෝ මුරපදය වැරදියි.** පරීක්ෂා කර නැවත උත්සාහ කරන්න.",
        "err_auth_expired":         "⏰ **ඔබේ සැසියේ කාලය ඉකුත් වී ඇත.** ඉදිරියට යාමට නැවත ඇතුළු වන්න.",
        "err_auth_duplicate":       "❌ **මෙම පරිශීලක නාමයෙන් ගිණුමක් දැනටමත් පවතී.** වෙනත් නමක් තෝරන්න හෝ ඇතුළු වන්න.",
        "err_auth_server":          "❌ **පද්ධතියේ අභ්‍යන්තර දෝෂයක් සිදු විය.** මොහොතකින් නැවත උත්සාහ කරන්න.",
        "err_auth_network":         "❌ **සබැඳි දෝෂයක්.** ඔබේ ජාල සබඳතාව පරීක්ෂා කර නැවත උත්සාහ කරන්න.",
        "err_auth_rate_limit":      "❌ **වැඩි වාර ගණනක් උත්සාහ කර ඇත.** මොහොතක් රැඳී සිට නැවත උත්සාහ කරන්න.",
        "info_register_username":   "පරිශීලක නාමය: අක්ෂර 3–254, ඉංග්‍රීසි අකුරු, ඉලක්කම්, '.', '_', '@', '+', '-' පමණි.",
        "info_register_password":   "මුරපදය: අවම වශයෙන් අක්ෂර 12ක් තිබිය යුතුය.",
        "lbl_personal_info":        "👤 පෞද්ගලික තොරතුරු",
        "lbl_account_creds":        "🔑 ගිණුම් විස්තර",
        "lbl_farming_context":      "🌾 ගොවිතැන් සන්දර්භය",
    },
    # ========================================================================
    # TAMIL  (ta)
    # ========================================================================
    "ta": {
        "app_title":                "வேளாண்-ஆலோசகர்",
        "app_subtitle":             "ஸ்மார்ட் விவசாய உதவியாளர்",
        "app_tagline":              "இலங்கை விவசாயிகள் சிறந்த பயிர்களை வளர்க்க உதவுகிறது",
        "lbl_language":             "🌐 மொழி",
        "lbl_district":             "📍 உங்கள் மாவட்டம்",
        "lbl_crop":                 "🌾 பயிர் வகை (விருப்பத்திற்குரியது)",
        "lbl_query":                "உங்கள் பயிர் பிரச்சினையை விவரிக்கவும்",
        "lbl_char_counter":         "{count} / 1000 எழுத்துக்கள்",
        "ph_query": (
            "எ.கா. என் நெல் இலைகள் மஞ்சளாகி சிறிய பழுப்பு புள்ளிகள் உள்ளன. "
            "இது என்ன நோய், எவ்வாறு சிகிச்சையளிக்க வேண்டும்?"
        ),
        "btn_submit":               "🔍 வேளாண்-ஆலோசகரிடம் கேட்கவும்",
        "btn_clear":                "🗑️ உரையாடலை அழிக்கவும்",
        "btn_helpful_yes":          "👍 ஆம்",
        "btn_helpful_no":           "👎 இல்லை",
        "report_heading":           "🌾 வேளாண் ஆலோசனை அறிக்கை",
        "report_followup": (
            "💬 **மேலும் கேள்வி உள்ளதா?** மேலே உள்ள பெட்டியில் தட்டச்சு செய்து "
            "**வேளாண்-ஆலோசகரிடம் கேட்கவும்** கிளிக் செய்யவும் — "
            "உங்கள் உரையாடல் சூழல் நினைவில் வைக்கப்படும்."
        ),
        "report_feedback":          "**இந்த ஆலோசனை உதவியதா?**",
        "blk_diagnosis":            "பகுதி 1 — நோய் கண்டறிதல்",
        "blk_treatment":            "பகுதி 2 — உடனடி சிகிச்சை",
        "blk_prevention":           "பகுதி 3 — தடுப்பு நடவடிக்கைகள்",
        "blk_weather":              "பகுதி 4 — வானிலை ஆலோசனை",
        "blk_sources":              "பகுதி 5 — ஆதாரங்கள்",
        "blk_disclaimer":           "பகுதி 6 — பொறுப்புத் துறப்பு",
        "blk_why":                  "பகுதி 7 — ஏன்? விளக்கம்",
        "blk_raw_answer":           "ஆலோசனை",
        "lbl_severity":             "தீவிரம்:",
        "lbl_confidence":           "நம்பகத்தன்மை:",
        "lbl_symptoms":             "உறுதிப்படுத்தப்பட்ட அறிகுறிகள்:",
        "lbl_differentials":        "வேறுபட்ட நோய் கண்டறிதல்கள்:",
        "lbl_urgency":              "அவசியம்:",
        "lbl_application":          "பயன்பாடு:",
        "lbl_dosage":               "அளவு:",
        "lbl_frequency":            "அதிர்வெண்:",
        "lbl_action_window":        "செயல் காலம்:",
        "lbl_risk":                 "அபாய நிலை:",
        "lbl_source_type":          "வகை:",
        "lbl_systems":              "அமைப்புகள்:",
        "lbl_intent":               "நோக்கம்:",
        "lbl_response_time":        "மறுமொழி நேரம்:",
        "sidebar_heading":          "⚙️ அமர்வு தகவல்",
        "lbl_user_id":              "**பயனர் ID:**",
        "lbl_session_id":           "**அமர்வு ID:**",
        "lbl_language_code":        "**மொழி:**",
        "lbl_turns":                "**சுற்றுகள்:**",
        "demo_mode_warning": (
            "⚠️ **Demo Mode** — வேளாண்-ஆலோசகர் சேவையகம் இயங்கவில்லை. "
            "மாதிரி ஆலோசனை தரவு காட்டப்படுகிறது."
        ),
        "err_empty_query":          "❌ சமர்ப்பிக்கும் முன் உங்கள் பயிர் பிரச்சினையை விவரிக்கவும்.",
        "err_api_unavailable":      "🔴 ஆலோசனை சேவை தற்போது அணுக இயலவில்லை.",
        "err_unknown":              "⚠️️ எதிர்பார்க்காத பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.",
        "err_char_limit":           "எழுத்து வரம்பை எட்டியது (அதிகபட்சம் 1000).",
        "info_translation_warn":    "⚠️ மொழிபெயர்ப்பு சேவை கிடைக்கவில்லை — ஆங்கில ஆலோசனை காட்டப்படுகிறது.",
        "info_translation_partial": "ℹ️ சில பகுதிகளை மொழிபெயர்க்க முடியவில்லை, ஆங்கிலத்தில் காட்டப்படுகிறது.",
        "lbl_details_expander":     "🔍 மறுமொழி விவரங்கள்",
        "lbl_why_expander":         "💡 வேளாண்-ஆலோசகர் ஏன் இதை பரிந்துரைத்தார்?",
        "lbl_helpful_toast_yes":    "உங்கள் கருத்துக்களுக்கு நன்றி!",
        "lbl_helpful_toast_no":     "மன்னிக்கவும். நாங்கள் தொடர்ந்து மேம்படுத்துவோம்!",
        "lbl_no_sources":           "இந்த ஆலோசனைக்கு ஆதாரங்கள் எதுவும் மேற்கோள் காட்டப்படவில்லை.",
        "sub_prevention":           "மீண்டும் ஏற்படுவதைத் தடுப்பதற்கான நீண்டகால நடவடிக்கைகள்",
        "sub_why":                  "AI பகுத்தறிவு மற்றும் நம்பகத்தன்மை முறிவு",
        "lbl_view_sources":         "ஆதாரங்களைக் காண்க",
        "lbl_risk_score":           "நோய் அபாய மதிப்பபெண்",
        "lbl_alert_valid":          "எச்சரிக்கை செல்லுபடியாகும் வரை",
        "lbl_model_reasoning":      "மாதிரி பகுத்தறிவு:",
        "lbl_confidence_by_agent":  "முகவர் வாரியான நம்பகத்தன்மை:",
        "lbl_systems_consulted":    "ஆலோசிக்கப்பட்ட அமைப்புகள்:",
        "lbl_partial_warning":      "சில நிபுணர் முகவர்கள் விவரங்களை வழங்கவில்லை. கிடைக்கக்கூடிய ஆலோசனைகள் கீழே காட்டப்பட்டுள்ளன; கூடுதல் விவரங்களுக்கு பின்தொடர் கேள்வியைக் கேட்கவும்.",
        # -- T-20: Authentication (Tamil) -----------------------------------
        "auth_login_title":         "மீண்டும் வருக!",
        "auth_login_subtitle":      "உங்கள் வேளாண்-ஆலோசகர் கணக்கில் உள்நுழையவும்",
        "auth_register_title":      "உங்கள் கணக்கை உருவாக்கவும்",
        "auth_register_subtitle":   "ஆயிரக்கணக்கான இலங்கை விவசாயிகளுடன் இணையுங்கள்",
        "lbl_username":             "👤 பயனர் பெயர்",
        "lbl_password":             "🔑 கடவுச்சொல்",
        "lbl_confirm_password":     "🔑 கடவுச்சொல்லை உறுதிப்படுத்தவும்",
        "lbl_full_name":            "முழு பெயர்",
        "lbl_phone_email":          "தொலைபேசி அல்லது மின்னஞ்சல்",
        "lbl_preferred_language":   "🌐 விரும்பிய மொழி",
        "ph_username":              "எ.கா. saman_farmer",
        "ph_password":              "குறைந்தது 12 எழுத்துக்கள்",
        "ph_confirm_password":      "கடவுச்சொல்லை மீண்டும் தட்டச்சு செய்யவும்",
        "ph_full_name":             "எ.கா. சமன் பெரேரா",
        "ph_phone_email":           "எ.கா. 0771234567 அல்லது saman@example.com",
        "btn_login":                "🔓 உள்நுழையவும்",
        "btn_register":             "🌱 கணக்கை உருவாக்கவும்",
        "btn_go_register":          "✏️ கணக்கை உருவாக்கவும்",
        "btn_go_login":             "🔓 உள்நுழையவும்",
        "btn_logout":               "🚪 வெளியேறு",
        "auth_switch_have_account": "ஏற்கனவே கணக்கு உள்ளதா?",
        "auth_switch_new":          "வேளாண்-ஆலோசகருக்கு புதியவரா?",
        "err_auth_invalid":         "❌ **தவறான பயனர் பெயர் அல்லது கடவுச்சொல்.** சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
        "err_auth_expired":         "⏰ **உங்கள் அமர்வு காலாவதியானது.** தொடர மீண்டும் உள்நுழையவும்.",
        "err_auth_duplicate":       "❌ **இந்த பயனர் பெயருடன் ஏற்கனவே ஒரு கணக்கு உள்ளது.** வேறு பெயரைத் தேர்ந்தெடுக்கவும்.",
        "err_auth_server":          "❌ **எங்கள் பக்கத்தில் பிழை ஏற்பட்டது.** சிறிது நேரத்தில் மீண்டும் முயற்சிக்கவும்.",
        "err_auth_network":         "❌ **இணைப்பு பிரச்சினை.** நெட்வொர்க்கை சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
        "err_auth_rate_limit":      "❌ **மிகுதி முயற்சிகள்.** சிறிது நேரம் காத்திருந்து மீண்டும் முயற்சிக்கவும்.",
        "info_register_username":   "பயனர் பெயர்: 3–254 எழுத்துக்கள், ஆங்கில எழுத்துக்கள், எண்கள், '.', '_', '@', '+', '-' மட்டும்.",
        "info_register_password":   "கடவுச்சொல்: குறைந்தபட்சம் 12 எழுத்துக்கள் இருக்க வேண்டும்.",
        "lbl_personal_info":        "👤 தனிப்பட்ட தகவல்",
        "lbl_account_creds":        "🔑 கணக்கு விவரங்கள்",
        "lbl_farming_context":      "🌾 விவசாய சூழல்",
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
    """
    english_value = UI_STRINGS.get("en", {}).get(key)
    localized_fallback = UI_STRINGS.get(lang_code, {}).get(key)

    if lang_code == "en":
        return english_value if english_value is not None else key

    if english_value is not None:
        try:
            from utils.translator import translate_static_text

            format_tokens = re.findall(r"\{[^{}]+\}", english_value)
            result = translate_static_text(
                english_value,
                lang_code,
                technical_terms=format_tokens,
            )
            if result.success:
                return result.text
        except Exception:  # noqa: BLE001
            pass

    if localized_fallback is not None:
        return localized_fallback
    return english_value if english_value is not None else key


def get_all_strings(lang_code: str = "en") -> dict[str, str]:
    """
    Return the full string table for *lang_code* merged on top of English
    so every possible key is always present.
    """
    base = dict(UI_STRINGS.get("en", {}))
    if lang_code != "en":
        base.update(UI_STRINGS.get(lang_code, {}))
    return base
