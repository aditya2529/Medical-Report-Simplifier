"""UI translations for ClarityMed. Add more languages by adding a dict here."""

T = {
    "english": {
        # Hero
        "app_title":      "🩺 ClarityMed",
        "app_tagline":    "Understand your lab report in plain language — in under 15 seconds.",

        # Settings
        "language":       "Language",
        "age":            "Age (optional)",
        "gender":         "Gender (optional)",
        "gender_options": ["Not specified", "Male", "Female", "Other"],

        # Upload
        "photo_tips_title": "📸 Tips for uploading a photo of a printed report",
        "photo_tips": [
            "📄 Lay the report flat — no folds or curves",
            "💡 Use good lighting — avoid shadows",
            "📐 Keep the full page in frame",
            "🔍 Hold steady — blur ruins extraction",
        ],
        "uploader_label":   "Upload your lab report (PDF, JPG, PNG, HEIC — up to 10 MB)",
        "analyse_btn":      "🔍 Analyse Report",

        # Manual entry
        "manual_title":     "✏️ Or enter values manually (for handwritten or unclear reports)",
        "manual_caption":   "Add one row per test. Press + to add more.",
        "ph_test_name":     "e.g. HbA1c",
        "ph_value":         "e.g. 7.8",
        "ph_unit":          "e.g. %",
        "ph_ref_low":       "4.0",
        "ph_ref_high":      "6.0",
        "col_test":         "Test name",
        "col_value":        "Value",
        "col_unit":         "Unit",
        "col_ref_low":      "Ref low",
        "col_ref_high":     "Ref high",
        "add_row":          "+ Add row",
        "analyse_manual":   "Analyse Manual Entry",
        "manual_warn":      "Please enter at least one test name and value.",
        "manual_report_type": "Manual Entry",

        # Progress
        "p_reading":        "📖 Reading your report…",
        "p_extracting":     "🔍 Extracting test parameters…",
        "p_analysing":      "📊 Analysing values against reference ranges…",
        "p_explaining":     "✍️ Generating plain-language explanations…",
        "p_done":           "✅ Done!",

        # Results
        "detected":         "Detected",
        "params_found":     "parameters found",
        "see_doctor":       "See Doctor",
        "monitor":          "Monitor",
        "normal":           "Normal",
        "urgent_banner":    "⚠️ Several values need attention — please consult your doctor before making any health decisions.",
        "low_conf_warn":    "values could not be read clearly. Please verify against your original report.",
        "verify_badge":     "⚠ Verify",
        "what_it_measures": "What it measures:",
        "reference":        "Reference",

        # Buttons
        "share_whatsapp":   "📲 Share on WhatsApp",
        "download_pdf":     "📄 Download PDF",
        "copy_summary":     "📋 Copy summary text",

        # WhatsApp text
        "wa_summary":       "Summary",
        "wa_attention":     "🔴 *Needs Attention:*",
        "wa_monitor":       "🟡 *Worth Monitoring:*",
        "wa_normal":        "🟢 *Normal: {n} values*",
        "wa_disclaimer":    "_This is not a medical diagnosis. Do not start, stop, or change any medication or treatment based on this. Always consult a qualified doctor._",

        # Errors
        "err_prefix":       "❌",
        "err_hint":         "💡 Try a clearer image, or use **manual entry** above.",

        # Disclaimer (audit #3 — top-of-results banner; "do not act on this")
        "disclaimer": (
            "**This is not a medical diagnosis.** "
            "Do not start, stop, or change any medication or treatment based on this output. "
            "Always consult a qualified doctor."
        ),
    },

    "hindi": {
        # Hero
        "app_title":      "🩺 ClarityMed",
        "app_tagline":    "अपनी लैब रिपोर्ट को सरल भाषा में समझें — सिर्फ़ 15 सेकंड में।",

        # Settings
        "language":       "भाषा",
        "age":            "उम्र (वैकल्पिक)",
        "gender":         "लिंग (वैकल्पिक)",
        "gender_options": ["नहीं बताया", "पुरुष", "महिला", "अन्य"],

        # Upload
        "photo_tips_title": "📸 छपी हुई रिपोर्ट की फ़ोटो लेने के सुझाव",
        "photo_tips": [
            "📄 रिपोर्ट को समतल जगह पर रखें — कोई मोड़ या सिलवट न हो",
            "💡 अच्छी रोशनी में फ़ोटो लें — छाया से बचें",
            "📐 पूरा पेज फ़्रेम में रखें",
            "🔍 कैमरा स्थिर रखें — धुंधली फ़ोटो से डेटा नहीं पढ़ा जा सकता",
        ],
        "uploader_label":   "अपनी लैब रिपोर्ट अपलोड करें (PDF, JPG, PNG, HEIC — 10 MB तक)",
        "analyse_btn":      "🔍 रिपोर्ट का विश्लेषण करें",

        # Manual entry
        "manual_title":     "✏️ या मानों को मैन्युअली दर्ज करें (हस्तलिखित या अस्पष्ट रिपोर्ट के लिए)",
        "manual_caption":   "हर टेस्ट के लिए एक पंक्ति जोड़ें। और जोड़ने के लिए + दबाएँ।",
        "ph_test_name":     "जैसे HbA1c",
        "ph_value":         "जैसे 7.8",
        "ph_unit":          "जैसे %",
        "ph_ref_low":       "4.0",
        "ph_ref_high":      "6.0",
        "col_test":         "टेस्ट का नाम",
        "col_value":        "मान",
        "col_unit":         "इकाई",
        "col_ref_low":      "न्यूनतम सीमा",
        "col_ref_high":     "अधिकतम सीमा",
        "add_row":          "+ पंक्ति जोड़ें",
        "analyse_manual":   "मैन्युअल प्रविष्टि का विश्लेषण करें",
        "manual_warn":      "कृपया कम से कम एक टेस्ट का नाम और मान दर्ज करें।",
        "manual_report_type": "मैन्युअल प्रविष्टि",

        # Progress
        "p_reading":        "📖 आपकी रिपोर्ट पढ़ी जा रही है…",
        "p_extracting":     "🔍 टेस्ट के पैरामीटर निकाले जा रहे हैं…",
        "p_analysing":      "📊 मानों की संदर्भ सीमा से तुलना की जा रही है…",
        "p_explaining":     "✍️ सरल भाषा में स्पष्टीकरण तैयार किया जा रहा है…",
        "p_done":           "✅ हो गया!",

        # Results
        "detected":         "पहचानी गई रिपोर्ट",
        "params_found":     "पैरामीटर मिले",
        "see_doctor":       "डॉक्टर से मिलें",
        "monitor":          "निगरानी करें",
        "normal":           "सामान्य",
        "urgent_banner":    "⚠️ कई मानों पर ध्यान देने की ज़रूरत है — कोई भी निर्णय लेने से पहले अपने डॉक्टर से सलाह लें।",
        "low_conf_warn":    "मान स्पष्ट रूप से नहीं पढ़े जा सके। कृपया अपनी मूल रिपोर्ट से मिलान करें।",
        "verify_badge":     "⚠ जाँचें",
        "what_it_measures": "यह क्या मापता है:",
        "reference":        "संदर्भ सीमा",

        # Buttons
        "share_whatsapp":   "📲 व्हाट्सऐप पर भेजें",
        "download_pdf":     "📄 PDF डाउनलोड करें",
        "copy_summary":     "📋 सारांश कॉपी करें",

        # WhatsApp text
        "wa_summary":       "सारांश",
        "wa_attention":     "🔴 *ध्यान देने योग्य:*",
        "wa_monitor":       "🟡 *निगरानी करें:*",
        "wa_normal":        "🟢 *सामान्य: {n} मान*",
        "wa_disclaimer":    "_यह कोई चिकित्सकीय निदान नहीं है। इसके आधार पर कोई भी दवा या इलाज शुरू, बंद या बदलें नहीं। हमेशा योग्य डॉक्टर से सलाह लें।_",

        # Errors
        "err_prefix":       "❌",
        "err_hint":         "💡 स्पष्ट फ़ोटो के साथ फिर कोशिश करें, या ऊपर **मैन्युअल प्रविष्टि** का उपयोग करें।",

        # Disclaimer (audit #3 — top-of-results banner; "इसके आधार पर कोई दवा बदलें नहीं")
        "disclaimer": (
            "**यह कोई चिकित्सकीय निदान नहीं है।** "
            "इस जानकारी के आधार पर कोई भी दवा या इलाज शुरू, बंद या बदलें नहीं। "
            "हमेशा योग्य डॉक्टर से सलाह लें।"
        ),
    },
}


def t(language: str, key: str):
    """Get translated string. Falls back to English if missing."""
    return T.get(language, T["english"]).get(key, T["english"].get(key, key))
