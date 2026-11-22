"""
conversation.py — Smart Q&A flow manager for YojanaSetu AI

This module decides:
  1. Which question to ask next (minimum questions strategy)
  2. Whether an answer contradicts a previous answer
  3. When we have enough info to run the eligibility check

The selector ranks unanswered fields by how many unresolved schemes need them.
"""

from typing import Any

from services.input_parsing import normalize_profile, parse_numeric_answer


def _answer(value: Any, label_en: str, label_hi: str, *aliases: str) -> dict[str, Any]:
    return {
        "value": value,
        "labels": {"en": label_en, "hi": label_hi},
        "aliases": list(aliases),
    }


def _yes_no_answers() -> list[dict[str, Any]]:
    return [
        _answer(True, "yes", "हाँ", "yes", "y", "true", "ha", "haan", "हां", "जी हाँ", "जी हां"),
        _answer(False, "no", "नहीं", "no", "n", "false", "nahi", "nahin", "नही", "न"),
    ]


# ── Question definitions ─────────────────────────────────────────────────────
# answer_options and numeric metadata define the authoritative validation contract.

QUESTIONS = {
    "language": {
        "id": "language",
        "text_en": "What language would you prefer? (English / Hindi)",
        "text_hi": "आप किस भाषा में बात करना चाहते हैं? (English / Hindi)",
        "type": "choice",
        "answer_options": [
            _answer("English", "English", "अंग्रेज़ी", "en", "अंग्रेजी"),
            _answer("Hindi", "Hindi", "हिंदी", "हिन्दी", "hi"),
        ],
    },
    "occupation": {
        "id": "occupation",
        "text_en": "What work do you do?",
        "text_hi": "आप क्या काम करते हैं?",
        "type": "choice",
        "selection_priority": 10,
        "answer_options": [
            _answer("farmer", "farmer", "किसान", "खेती", "कृषि"),
            _answer("student", "student", "छात्र", "छात्रा", "विद्यार्थी"),
            _answer("daily_wage", "daily wage worker", "दिहाड़ी मजदूर", "daily wage", "दैनिक मजदूर", "मजदूर"),
            _answer("housewife", "homemaker", "गृहिणी", "housewife", "गृहणी"),
            _answer("other", "other", "अन्य", "unemployed", "not working", "बेरोज़गार", "बेरोजगार"),
        ],
    },
    "age": {
        "id": "age",
        "text_en": "How old are you?",
        "text_hi": "आपकी उम्र क्या है?",
        "type": "number",
        "selection_priority": 8,
        "numeric": {
            "unit": "years",
            "unit_labels": {"en": "years", "hi": "वर्ष"},
            "minimum": 0,
            "minimum_inclusive": False,
            "allow_unitless": True,
            "unit_factors": {
                "": 1,
                "year": 1,
                "years": 1,
                "yr": 1,
                "yrs": 1,
                "वर्ष": 1,
                "साल": 1,
            },
        },
    },
    "gender": {
        "id": "gender",
        "text_en": "What is your gender?",
        "text_hi": "आपका लिंग क्या है?",
        "type": "choice",
        "selection_priority": 7,
        "answer_options": [
            _answer("male", "male", "पुरुष", "man"),
            _answer("female", "female", "महिला", "स्त्री", "lady"),
            _answer("other", "other", "अन्य"),
        ],
    },
    "income_level": {
        "id": "income_level",
        "text_en": "What is your family's income level? (BPL / low / middle / high)",
        "text_hi": "आपके परिवार की आय का स्तर क्या है? (BPL / कम / मध्यम / अधिक)",
        "type": "choice",
        "selection_priority": 9,
        "answer_options": [
            _answer("bpl", "BPL", "BPL", "below poverty line", "बीपीएल", "गरीब", "गरीबी रेखा से नीचे"),
            _answer("low_income", "low", "कम", "low income", "कम आय"),
            _answer("middle_income", "middle", "मध्यम", "middle income", "middle class", "मध्यम आय", "मध्यम वर्ग", "medium"),
            _answer("high_income", "high", "अधिक", "high income", "अधिक आय"),
        ],
    },
    "residence_type": {
        "id": "residence_type",
        "text_en": "Do you live in a village or a city?",
        "text_hi": "आप गाँव में रहते हैं या शहर में?",
        "type": "choice",
        "selection_priority": 7,
        "answer_options": [
            _answer("rural", "rural", "ग्रामीण", "village", "गाँव", "गांव"),
            _answer("urban", "urban", "शहरी", "city", "शहर"),
        ],
    },
    "marital_status": {
        "id": "marital_status",
        "text_en": "What is your marital status?",
        "text_hi": "आपकी वैवाहिक स्थिति क्या है?",
        "type": "choice",
        "selection_priority": 7,
        "answer_options": [
            _answer("married", "married", "विवाहित"),
            _answer("unmarried", "unmarried", "अविवाहित", "single"),
            _answer("widow", "widow", "विधवा"),
            _answer("widower", "widower", "विधुर"),
            _answer("divorced", "divorced", "तलाकशुदा"),
        ],
    },
    "owns_land": {
        "id": "owns_land",
        "text_en": "Do you own farm land?",
        "text_hi": "क्या आपके पास खेती की जमीन है?",
        "type": "boolean",
        "selection_priority": 8,
        "answer_options": _yes_no_answers(),
    },
    "land_size_hectares": {
        "id": "land_size_hectares",
        "text_en": "How much farm land do you own, in hectares?",
        "text_hi": "आपके पास कितनी खेती की जमीन है (हेक्टेयर में)?",
        "type": "number",
        "selection_priority": 5,
        "numeric": {
            "unit": "hectares",
            "unit_labels": {"en": "hectares", "hi": "हेक्टेयर"},
            "minimum": 0,
            "minimum_inclusive": True,
            "allow_unitless": True,
            "unit_factors": {
                "": 1,
                "ha": 1,
                "hectare": 1,
                "hectares": 1,
                "hector": 1,
                "hectors": 1,
                "hecter": 1,
                "hecters": 1,
                "hectar": 1,
                "hectars": 1,
                "हेक्टेयर": 1,
                "हेक्टेअर": 1,
                "हेक्टर": 1,
                "acre": 0.40468564224,
                "acres": 0.40468564224,
                "ac": 0.40468564224,
                "एकड़": 0.40468564224,
                "एकड़": 0.40468564224,
                "एकर": 0.40468564224,
            },
        },
    },
    "is_govt_employee": {
        "id": "is_govt_employee",
        "text_en": "Does anyone in your family work for the government?",
        "text_hi": "क्या आपके परिवार में कोई सरकारी नौकरी करता है?",
        "type": "boolean",
        "selection_priority": 4,
        "answer_options": _yes_no_answers(),
    },
    "pays_income_tax": {
        "id": "pays_income_tax",
        "text_en": "Does anyone in your family pay income tax?",
        "text_hi": "क्या आपके परिवार में कोई आयकर भरता है?",
        "type": "boolean",
        "selection_priority": 4,
        "answer_options": _yes_no_answers(),
    },
    "institutional_land_holder": {
        "id": "institutional_land_holder",
        "text_en": "Is the land in a company's or institution's name?",
        "text_hi": "क्या जमीन किसी कंपनी या संस्था के नाम पर है?",
        "type": "boolean",
        "selection_priority": 3,
        "answer_options": _yes_no_answers(),
    },
    "housing_condition": {
        "id": "housing_condition",
        "text_en": "What type of house do you live in? (homeless / kutcha / pucca)",
        "text_hi": "आप किस तरह के घर में रहते हैं? (बेघर / कच्चा / पक्का)",
        "type": "choice",
        "selection_priority": 6,
        "answer_options": [
            _answer("homeless", "homeless", "बेघर", "no home", "घर नहीं"),
            _answer("kutcha_house", "kutcha house", "कच्चा मकान", "kutcha", "kachcha house", "kuccha house", "कच्चा"),
            _answer("pucca_house", "pucca house", "पक्का मकान", "pucca", "pukka house", "पक्का"),
        ],
    },
    "received_housing_scheme_before": {
        "id": "received_housing_scheme_before",
        "text_en": "Have you received help from a housing scheme before?",
        "text_hi": "क्या आपको पहले किसी आवास योजना से मदद मिली है?",
        "type": "boolean",
        "selection_priority": 5,
        "answer_options": _yes_no_answers(),
    },
    "is_student": {
        "id": "is_student",
        "text_en": "Are you studying now?",
        "text_hi": "क्या आप अभी पढ़ाई कर रहे हैं?",
        "type": "boolean",
        "selection_priority": 9,
        "answer_options": _yes_no_answers(),
    },
    "enrolled_in_recognized_institution": {
        "id": "enrolled_in_recognized_institution",
        "text_en": "Is your school or college recognized?",
        "text_hi": "क्या आपका स्कूल या कॉलेज मान्यता प्राप्त है?",
        "type": "boolean",
        "selection_priority": 4,
        "answer_options": _yes_no_answers(),
    },
    "category": {
        "id": "category",
        "text_en": "Which category do you belong to?",
        "text_hi": "आप किस श्रेणी में आते हैं?",
        "type": "choice",
        "selection_priority": 5,
        "answer_options": [
            _answer("sc", "SC", "SC", "scheduled caste", "अनुसूचित जाति"),
            _answer("st", "ST", "ST", "scheduled tribe", "अनुसूचित जनजाति"),
            _answer("obc", "OBC", "OBC", "other backward class", "अन्य पिछड़ा वर्ग"),
            _answer("minority", "minority", "अल्पसंख्यक"),
            _answer("ews", "EWS", "EWS", "economically weaker section", "आर्थिक रूप से कमजोर वर्ग"),
            _answer("general", "General", "सामान्य"),
        ],
    },
    "family_income_lpa": {
        "id": "family_income_lpa",
        "text_en": "What is your family's yearly income in lakhs?",
        "text_hi": "आपके परिवार की सालाना आय कितने लाख है?",
        "type": "number",
        "selection_priority": 5,
        "numeric": {
            "unit": "lakh_rupees_per_year",
            "unit_labels": {"en": "lakhs per year", "hi": "लाख रुपये प्रति वर्ष"},
            "minimum": 0,
            "minimum_inclusive": True,
            "allow_unitless": True,
            "unit_factors": {
                "": 1,
                "lpa": 1,
                "lakh": 1,
                "lakhs": 1,
                "lac": 1,
                "lacs": 1,
                "लाख": 1,
                "lakh per year": 1,
                "lakh per annum": 1,
                "lakh/year": 1,
                "lakh/yr": 1,
                "lakhs per year": 1,
                "lakhs per annum": 1,
                "lakhs/year": 1,
                "lakhs/yr": 1,
                "lac per year": 1,
                "lac per annum": 1,
                "lac/year": 1,
                "lac/yr": 1,
                "lacs per year": 1,
                "lacs per annum": 1,
                "lacs/year": 1,
                "lacs/yr": 1,
                "लाख प्रति वर्ष": 1,
                "लाख वर्ष": 1,
                "लाख प्रति साल": 1,
                "लाख साल": 1,
                "rupee": 0.00001,
                "rupees": 0.00001,
                "rupees per year": 0.00001,
                "rupees per annum": 0.00001,
                "rupees/year": 0.00001,
                "रुपया": 0.00001,
                "रुपये": 0.00001,
                "रुपए": 0.00001,
                "रुपये प्रति वर्ष": 0.00001,
                "₹": 0.00001,
                "₹ rupee": 0.00001,
                "₹ rupees": 0.00001,
                "₹ रुपया": 0.00001,
                "₹ रुपये": 0.00001,
                "₹ रुपए": 0.00001,
                "₹ rupees per year": 0.00001,
                "₹ rupees per annum": 0.00001,
                "₹ रुपये प्रति वर्ष": 0.00001,
                "₹ रुपये प्रति साल": 0.00001,
                "₹ रुपए प्रति वर्ष": 0.00001,
                "₹ रुपए प्रति साल": 0.00001,
                "₹ per year": 0.00001,
                "₹ per annum": 0.00001,
                "₹/year": 0.00001,
                "₹/yr": 0.00001,
                "₹ प्रति वर्ष": 0.00001,
                "₹ प्रति साल": 0.00001,
                "₹ वर्ष": 0.00001,
                "₹ साल": 0.00001,
                "₹ lakh": 1,
                "₹ lakhs": 1,
                "₹ lac": 1,
                "₹ lacs": 1,
                "₹ lakh per year": 1,
                "₹ lakh per annum": 1,
                "₹ lakh/year": 1,
                "₹ lakh/yr": 1,
                "₹ lakhs per year": 1,
                "₹ lakhs per annum": 1,
                "₹ lakhs/year": 1,
                "₹ lakhs/yr": 1,
                "₹ lac per year": 1,
                "₹ lac per annum": 1,
                "₹ lac/year": 1,
                "₹ lac/yr": 1,
                "₹ lacs per year": 1,
                "₹ lacs per annum": 1,
                "₹ lacs/year": 1,
                "₹ lacs/yr": 1,
                "₹ लाख": 1,
                "₹ लाख प्रति वर्ष": 1,
                "₹ लाख प्रति साल": 1,
            },
        },
    },
    "ration_card_type": {
        "id": "ration_card_type",
        "text_en": "What color is your ration card?",
        "text_hi": "आपके राशन कार्ड का रंग क्या है?",
        "type": "choice",
        "selection_priority": 5,
        "answer_options": [
            _answer("yellow", "yellow", "पीला"),
            _answer("white", "white", "सफेद"),
            _answer("orange", "orange", "नारंगी"),
            _answer("no_card", "no card", "कार्ड नहीं", "कोई कार्ड नहीं", "no card"),
        ],
    },
}

for _question in QUESTIONS.values():
    if _question["type"] == "choice":
        _question["options"] = [answer["value"] for answer in _question["answer_options"]]

def get_next_question(profile: dict[str, Any], lang: str = "en") -> dict | None:
    """Choose the highest-value unanswered question for unresolved schemes."""
    profile = normalize_profile(profile, QUESTIONS)
    clarification = _next_clarification(profile, lang)
    if clarification is not None:
        question_id, text = clarification
        question = QUESTIONS[question_id].copy()
        question["text"] = text
        question["is_clarification"] = True
        return question

    from services.eligibility import get_remaining_question_candidates

    candidates = get_remaining_question_candidates(profile)
    if not candidates:
        return None

    question_id = max(
        candidates,
        key=lambda field: (
            len(candidates[field]),
            QUESTIONS[field].get("selection_priority", 0),
        ),
    )
    question = QUESTIONS[question_id].copy()
    question["text"] = question[f"text_{lang}"]
    return question


def _next_clarification(profile: dict[str, Any], lang: str) -> tuple[str, str] | None:
    clarified = profile.get("_clarified_fields", [])
    clarified = {field for field in clarified if isinstance(field, str)} if isinstance(clarified, list) else set()
    age = parse_numeric_answer(QUESTIONS["age"], profile.get("age"))
    land_size = parse_numeric_answer(
        QUESTIONS["land_size_hectares"], profile.get("land_size_hectares")
    )
    pending = []

    if profile.get("owns_land") is False and land_size is not None and land_size > 0:
        pending.append(("owns_land", "Do you own the land you listed?", "क्या बताई गई जमीन आपकी है?"))
    if profile.get("owns_land") is True and land_size == 0:
        pending.append(("land_size_hectares", "What is the correct land area?", "जमीन का सही क्षेत्रफल कितना है?"))
    if profile.get("income_level") == "high_income" and profile.get("ration_card_type") == "yellow":
        pending.append(("income_level", "Please confirm your family's income level.", "कृपया अपने परिवार की आय की पुष्टि करें।"))
    if profile.get("occupation") == "student" and age is not None and age > 35:
        pending.append(("age", "Please confirm your age.", "कृपया अपनी उम्र की पुष्टि करें।"))

    for field, english, hindi in pending:
        if field not in clarified:
            return field, hindi if lang == "hi" else english
    return None


def detect_contradictions(profile: dict[str, Any], lang: str = "en") -> list[str]:
    """
    Check for contradictory answers in the profile.
    Returns a list of contradiction messages (empty list = no contradictions).
    """
    profile = normalize_profile(profile, QUESTIONS)
    contradictions = []

    # Farmer + no land
    if profile.get("occupation") == "farmer" and profile.get("owns_land") is False:
        msg = (
            "आपने बताया कि आप किसान हैं, लेकिन आपके पास कृषि भूमि नहीं है। "
            "क्या आप किसी और की जमीन पर काम करते हैं? पीएम किसान के लिए अपनी जमीन होना जरूरी है।"
            if lang == "hi" else
            "You said you're a farmer but don't own land. "
            "Do you work on someone else's land? PM Kisan requires you to own the land."
        )
        contradictions.append(msg)

    land_size = profile.get("land_size_hectares")
    if profile.get("owns_land") is False and land_size is not None and land_size > 0:
        msg = (
            f"आपने बताया कि आपके पास कृषि भूमि नहीं है, लेकिन {land_size:g} हेक्टेयर भूमि भी बताई। "
            "कृपया स्पष्ट करें कि कौन-सी जानकारी सही है।"
            if lang == "hi" else
            f"You said you do not own agricultural land but also reported {land_size:g} hectares. "
            "Please clarify which answer is correct."
        )
        contradictions.append(msg)
    elif profile.get("owns_land") is True and land_size == 0:
        msg = (
            "आपने बताया कि आपके पास कृषि भूमि है, लेकिन भूमि का क्षेत्रफल शून्य बताया। "
            "कृपया एक स्पष्ट मात्रा बताएं।"
            if lang == "hi" else
            "You said you own agricultural land but reported zero hectares. "
            "Please clarify the amount."
        )
        contradictions.append(msg)

    # Student + age > 35
    age = parse_numeric_answer(QUESTIONS["age"], profile.get("age"))
    if profile.get("occupation") == "student" and age is not None and age > 35:
        msg = (
            "आपने बताया कि आप छात्र हैं और आपकी उम्र 35 से अधिक है। "
            "कृपया पुष्टि करें — अधिकांश NSP छात्रवृत्तियों के लिए अधिकतम आयु 35 वर्ष है।"
            if lang == "hi" else
            "You mentioned being a student but your age is over 35. "
            "Please confirm — most NSP scholarships have a 35-year age limit."
        )
        contradictions.append(msg)

    # High income + BPL claim
    if profile.get("income_level") == "high_income" and profile.get("ration_card_type") in ("yellow",):
        msg = (
            "आपने उच्च आय बताई लेकिन पीला राशन कार्ड (BPL) भी बताया। "
            "कृपया स्पष्ट करें — इससे पात्रता प्रभावित होती है।"
            if lang == "hi" else
            "You mentioned high income but also a yellow (BPL) ration card. "
            "Please clarify — this affects eligibility."
        )
        contradictions.append(msg)

    return contradictions
