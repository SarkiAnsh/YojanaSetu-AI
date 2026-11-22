"""
eligibility.py — Core eligibility rule engine for YojanaSetu AI

This module checks a user's answers against each scheme's rules
and returns a list of matched / unmatched schemes with reasons.

[DEMO DATA] — Rules here are illustrative. Verify at official portals.
"""

import json
from pathlib import Path
from typing import Any

from services.conversation import QUESTIONS
from services.input_parsing import normalize_profile, parse_numeric_answer

# ── Load scheme data once at startup ────────────────────────────────────────
DATA_PATH = Path(__file__).parent.parent / "data" / "schemes_demo.json"
with open(DATA_PATH, encoding="utf-8") as f:
    SCHEMES = json.load(f)["schemes"]

UNKNOWN_ANSWERS = {
    "", "unknown", "not sure", "unsure", "maybe", "n/a", "na",
    "not applicable", "don't know", "dont know", "idk",
    "पता नहीं", "नहीं पता", "pata nahi", "nahi pata",
}


def check_eligibility(user_profile: dict[str, Any], lang: str = "en") -> list[dict]:
    """
    Given a user profile dict, check all 5 demo schemes.

    Args:
        user_profile: Collected answers, e.g.
            {
              "occupation": "farmer",
              "owns_land": True,
              "land_size_hectares": 1.5,
              "is_govt_employee": False,
              "pays_income_tax": False,
              "gender": "female",
              "marital_status": "widow",
              "age": 55,
              "income_level": "bpl",
              ...
            }
        lang: "en" or "hi" — controls language of reason strings

    Returns:
        List of result dicts, one per scheme:
        {
          "scheme_id": "...",
          "name": "...",
          "eligible": True/False/None,   # None = not enough info yet
          "reasons": ["...", "..."],      # why eligible or not
          "benefit": "...",
          "apply_at": "..."
        }
    """
    user_profile = normalize_profile(user_profile, QUESTIONS)
    results = []
    for scheme in SCHEMES:
        result = _check_single_scheme(scheme, user_profile, lang)
        results.append(result)
    return results


def get_remaining_question_candidates(profile: dict[str, Any]) -> dict[str, set[str]]:
    """Map unanswered question IDs to unresolved schemes that require them."""
    normalized = normalize_profile(profile, QUESTIONS)
    results = {
        result["scheme_id"]: result
        for result in check_eligibility(normalized)
    }
    candidates: dict[str, set[str]] = {}
    for scheme in SCHEMES:
        if results[scheme["id"]]["eligible"] is not None:
            continue
        for field in _missing_required_fields(scheme, normalized):
            if field in QUESTIONS:
                candidates.setdefault(field, set()).add(scheme["id"])
    return candidates


def _check_single_scheme(scheme: dict, profile: dict, lang: str) -> dict:
    """Check one scheme against the user profile. Returns a result dict."""
    sid = scheme["id"]
    name = scheme[f"name_{lang}"]
    reasons_pass = []
    reasons_fail = []
    reasons_unclear = []

    # ── PM Kisan ────────────────────────────────────────────────────────────
    if sid == "pm_kisan":
        occ = profile.get("occupation", "")
        if _has_known_answer(profile, "occupation") and occ != "farmer":
            reasons_fail.append(_t(lang,
                "You mentioned your occupation is not farming.",
                "आपने बताया कि आपका व्यवसाय खेती नहीं है।"))
        elif occ == "farmer":
            reasons_pass.append(_t(lang, "You are a farmer. ✓", "आप किसान हैं। ✓"))

        if profile.get("owns_land") is False:
            reasons_fail.append(_t(lang,
                "PM Kisan requires you to own cultivable land.",
                "पीएम किसान के लिए आपके पास कृषि योग्य भूमि होनी चाहिए।"))
        elif profile.get("owns_land") is True:
            land = _number(profile, "land_size_hectares")
            if land == 0:
                reasons_unclear.append(_t(lang,
                    "You said you own land but entered zero hectares; confirm the land area.",
                    "आपने जमीन होने की बात कही, लेकिन क्षेत्रफल शून्य बताया; कृपया क्षेत्रफल की पुष्टि करें।"))
            elif land is not None and land > 2:
                reasons_fail.append(_t(lang,
                    f"Land holding ({land} ha) exceeds the 2-hectare limit for small/marginal farmers.",
                    f"भूमि ({land} हेक्टेयर) छोटे/सीमांत किसान की 2 हेक्टेयर सीमा से अधिक है।"))
            elif land is not None:
                reasons_pass.append(_t(lang,
                    f"Land holding ({land} ha) is within the 2-hectare limit. ✓",
                    f"भूमि ({land} हेक्टेयर) 2 हेक्टेयर सीमा के अंदर है। ✓"))

        if profile.get("is_govt_employee") is True:
            reasons_fail.append(_t(lang,
                "Government employees are not eligible for PM Kisan.",
                "सरकारी कर्मचारी पीएम किसान के लिए पात्र नहीं हैं।"))
        elif profile.get("is_govt_employee") is False:
            reasons_pass.append(_t(lang,
                "You are not a government employee. ✓",
                "आप सरकारी कर्मचारी नहीं हैं। ✓"))

        if profile.get("pays_income_tax") is True:
            reasons_fail.append(_t(lang,
                "Income tax payers are not eligible for PM Kisan.",
                "आयकर दाता पीएम किसान के लिए पात्र नहीं हैं।"))
        elif profile.get("pays_income_tax") is False:
            reasons_pass.append(_t(lang,
                "No family member pays income tax. ✓",
                "परिवार का कोई सदस्य आयकर नहीं भरता। ✓"))

        if profile.get("institutional_land_holder") is True:
            reasons_fail.append(_t(lang,
                "Institutional landholders are excluded under the demo rules.",
                "डेमो नियमों के अनुसार संस्थागत भूमिधारक पात्र नहीं हैं।"))
        elif profile.get("institutional_land_holder") is False:
            reasons_pass.append(_t(lang,
                "The land is not held by an institution. ✓",
                "भूमि किसी संस्था के नाम पर नहीं है। ✓"))

    # ── Ayushman Bharat ─────────────────────────────────────────────────────
    elif sid == "ayushman_bharat":
        income = profile.get("income_level", "")
        ration = profile.get("ration_card_type", "")
        secc_listed = profile.get("secc_listed")
        conflicting_indicators = (
            income == "high_income"
            and (ration in ("yellow", "orange", "apl_poor") or secc_listed is True)
        )
        if conflicting_indicators:
            reasons_unclear.append(_t(lang,
                "The reported income and ration-card category conflict; confirm them with official records.",
                "बताई गई आय और राशन कार्ड की श्रेणी में अंतर है; आधिकारिक रिकॉर्ड से पुष्टि करें।"))
        elif income in ("bpl", "low_income") or ration in ("yellow", "orange", "apl_poor"):
            reasons_pass.append(_t(lang,
                "Your income / ration card category suggests possible SECC eligibility. ✓",
                "आपकी आय / राशन कार्ड श्रेणी SECC पात्रता का संकेत देती है। ✓"))
        elif income == "high_income":
            reasons_unclear.append(_t(lang,
                "A high-income answer alone cannot establish eligibility; check the official SECC records.",
                "केवल उच्च आय का उत्तर पात्रता तय नहीं करता; आधिकारिक SECC रिकॉर्ड जाँचें।"))

        if secc_listed is True:
            reasons_pass.append(_t(lang,
                "SECC listing is confirmed in the provided profile. ✓",
                "दी गई जानकारी के अनुसार SECC सूची में नाम की पुष्टि हुई। ✓"))
        elif secc_listed is False:
            reasons_fail.append(_t(lang,
                "The profile indicates no matching SECC listing.",
                "दी गई जानकारी में SECC सूची से मेल नहीं मिला।"))
        else:
            reasons_unclear.append(_t(lang,
                "Final eligibility must be verified against the SECC 2011 records.",
                "अंतिम पात्रता की पुष्टि SECC 2011 रिकॉर्ड से करनी होगी।"))

    # ── PM Awas Gramin ───────────────────────────────────────────────────────
    elif sid == "pm_awas_gramin":
        if profile.get("residence_type") == "urban":
            reasons_fail.append(_t(lang,
                "PM Awas Yojana Gramin is only for rural residents. (PMAY-U covers urban areas.)",
                "पीएम आवास योजना ग्रामीण केवल ग्रामीण निवासियों के लिए है। (शहरी क्षेत्रों के लिए PMAY-U है।)"))
        elif profile.get("residence_type") == "rural":
            reasons_pass.append(_t(lang, "You live in a rural area. ✓", "आप ग्रामीण क्षेत्र में रहते हैं। ✓"))

        housing = profile.get("housing_condition", "")
        if housing in ("homeless", "kutcha_house"):
            reasons_pass.append(_t(lang,
                "Your housing condition (kutcha/no house) meets the requirement. ✓",
                "आपकी आवास स्थिति (कच्चा/बेघर) आवश्यकता पूरी करती है। ✓"))
        elif housing == "pucca_house":
            reasons_fail.append(_t(lang,
                "You already have a pucca house, so this scheme may not apply.",
                "आपके पास पहले से पक्का मकान है, इसलिए यह योजना लागू नहीं हो सकती।"))

        if profile.get("received_housing_scheme_before") is True:
            reasons_fail.append(_t(lang,
                "Previous beneficiaries of housing schemes are not eligible again.",
                "पहले से आवास योजना का लाभ उठाने वाले पुनः पात्र नहीं हैं।"))

        income = profile.get("income_level", "")
        if income in ("bpl", "low_income"):
            reasons_pass.append(_t(lang, "Income category qualifies. ✓", "आय श्रेणी पात्र है। ✓"))
        elif income in ("middle_income", "high_income"):
            reasons_fail.append(_t(lang,
                "The reported income category is outside the demo rules for this scheme.",
                "बताई गई आय श्रेणी इस योजना के डेमो नियमों में शामिल नहीं है।"))

    # ── National Scholarship ─────────────────────────────────────────────────
    elif sid == "national_scholarship":
        if profile.get("is_student") is False:
            reasons_fail.append(_t(lang,
                "This scholarship is for currently enrolled students.",
                "यह छात्रवृत्ति वर्तमान में नामांकित छात्रों के लिए है।"))
        elif profile.get("is_student") is True:
            reasons_pass.append(_t(lang, "You are a student. ✓", "आप छात्र/छात्रा हैं। ✓"))

        age = _number(profile, "age")
        if age is not None and age > 35:
            reasons_fail.append(_t(lang,
                "Most NSP scholarships have an upper age limit of 35.",
                "अधिकांश NSP छात्रवृत्तियों के लिए अधिकतम आयु 35 वर्ष है।"))

        category = profile.get("category", "")
        if category in ("sc", "st", "obc", "minority", "ews"):
            reasons_pass.append(_t(lang,
                f"Your category ({category.upper()}) is covered under NSP. ✓",
                f"आपकी श्रेणी ({category.upper()}) NSP के अंतर्गत शामिल है। ✓"))
        elif category == "general":
            reasons_fail.append(_t(lang,
                "General category students may not qualify for most NSP scholarships.",
                "सामान्य श्रेणी के छात्र अधिकांश NSP छात्रवृत्तियों के लिए पात्र नहीं हो सकते।"))

        income = _number(profile, "family_income_lpa")
        if income is not None and income > 2.5:
            reasons_fail.append(_t(lang,
                f"Family income (₹{income}L/year) exceeds the ₹2.5L/year limit.",
                f"पारिवारिक आय (₹{income}L/वर्ष) ₹2.5L/वर्ष की सीमा से अधिक है।"))
        elif income is not None:
            reasons_pass.append(_t(lang,
                f"Family income (₹{income}L/year) is within limit. ✓",
                f"पारिवारिक आय (₹{income}L/वर्ष) सीमा के अंदर है। ✓"))

        if profile.get("enrolled_in_recognized_institution") is False:
            reasons_fail.append(_t(lang,
                "Enrollment in a recognized institution is required by the demo rules.",
                "डेमो नियमों के अनुसार मान्यता प्राप्त संस्थान में नामांकन आवश्यक है।"))
        elif profile.get("enrolled_in_recognized_institution") is True:
            reasons_pass.append(_t(lang,
                "Enrollment in a recognized institution is confirmed. ✓",
                "मान्यता प्राप्त संस्थान में नामांकन की पुष्टि हुई। ✓"))

    # ── Widow Pension ────────────────────────────────────────────────────────
    elif sid == "widow_pension_ignwps":
        gender = profile.get("gender", "")
        marital = profile.get("marital_status", "")
        income = profile.get("income_level", "")

        if _has_known_answer(profile, "gender") and gender != "female":
            reasons_fail.append(_t(lang,
                "IGNWPS is only for women who are widows.",
                "IGNWPS केवल विधवा महिलाओं के लिए है।"))
        elif gender == "female":
            reasons_pass.append(_t(lang, "Gender criterion met. ✓", "लिंग मानदंड पूरा हुआ। ✓"))

        if _has_known_answer(profile, "marital_status") and marital != "widow":
            reasons_fail.append(_t(lang,
                "This pension is for widows only.",
                "यह पेंशन केवल विधवाओं के लिए है।"))
        elif marital == "widow":
            reasons_pass.append(_t(lang, "Marital status (widow) qualifies. ✓",
                                   "वैवाहिक स्थिति (विधवा) पात्र है। ✓"))

        age_value = _number(profile, "age")
        if age_value is not None:
            if age_value < 40:
                reasons_fail.append(_t(lang,
                    f"Minimum age is 40 (you are {age_value:g}).",
                    f"न्यूनतम आयु 40 वर्ष है (आपकी आयु {age_value:g} है)।"))
            elif age_value > 79:
                reasons_fail.append(_t(lang,
                    f"Maximum age is 79 (you are {age_value:g}). Consider IGNOAPS (old age pension).",
                    f"अधिकतम आयु 79 वर्ष है (आपकी आयु {age_value:g} है)। IGNOAPS (वृद्धावस्था पेंशन) देखें।"))
            else:
                reasons_pass.append(_t(lang, f"Age ({age_value:g}) is within 40–79 range. ✓",
                                       f"आयु ({age_value:g}) 40–79 की सीमा में है। ✓"))

        if income == "bpl":
            reasons_pass.append(_t(lang, "BPL status qualifies. ✓", "BPL स्थिति पात्र है। ✓"))
        elif _has_known_answer(profile, "income_level") and income != "bpl":
            reasons_fail.append(_t(lang,
                "IGNWPS requires BPL (Below Poverty Line) status.",
                "IGNWPS के लिए BPL (गरीबी रेखा से नीचे) स्थिति आवश्यक है।"))

    missing_fields = _missing_required_fields(scheme, profile)
    if missing_fields:
        reasons_unclear.append(_t(lang,
            "Some required eligibility information is missing or could not be confirmed.",
            "पात्रता की पुष्टि के लिए कुछ आवश्यक जानकारी उपलब्ध नहीं है।"))

    # A failed criterion can rule a scheme out; a positive result needs complete evidence.
    if reasons_fail:
        eligible = False
    elif missing_fields or reasons_unclear:
        eligible = None
    elif reasons_pass:
        eligible = True
    else:
        eligible = None

    return {
        "scheme_id": sid,
        "name": name,
        "description": scheme[f"description_{lang}"],
        "eligible": eligible,
        "reasons": reasons_pass + reasons_fail + reasons_unclear,
        "benefit": scheme[f"benefit_{lang}"],
        "apply_at": scheme[f"apply_at_{lang}"],
        "data_note": "[DEMO DATA] Verify eligibility at official portals before applying."
    }


def _missing_required_fields(scheme: dict, profile: dict) -> list[str]:
    required_fields = set(scheme.get("questions_needed", []))
    excluded_field_map = {
        "government_employee": "is_govt_employee",
        "income_taxpayer": "pays_income_tax",
        "institutional_land_holder": "institutional_land_holder",
    }
    for exclusion in scheme.get("eligibility_rules", {}).get("excluded_if", []):
        profile_field = excluded_field_map.get(exclusion)
        if profile_field:
            required_fields.add(profile_field)

    return sorted(
        field for field in required_fields
        if not _has_known_answer(profile, field)
    )


def _has_known_answer(profile: dict, field: str) -> bool:
    if field not in profile:
        return False

    value = profile[field]
    if value is None:
        return False
    question = QUESTIONS.get(field)
    if question and question["type"] == "boolean":
        return isinstance(value, bool)
    if question and question["type"] == "number":
        number = parse_numeric_answer(question, value)
        if number is None:
            return False
        return number > 0 if field == "age" else number >= 0
    if field == "secc_listed":
        return isinstance(value, bool)
    if question and question["type"] == "choice":
        return value in question.get("options", [])
    if isinstance(value, str) and value.strip().lower() in UNKNOWN_ANSWERS:
        return False
    return True


def _number(profile: dict, field: str) -> float | None:
    question = QUESTIONS.get(field)
    return parse_numeric_answer(question, profile.get(field)) if question else None


def _t(lang: str, en: str, hi: str) -> str:
    """Return English or Hindi string based on lang."""
    return hi if lang == "hi" else en
