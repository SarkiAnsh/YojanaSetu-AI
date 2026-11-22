"""Question-contract-driven parsing for answers used by the rule engine."""

import math
import re
import unicodedata
from typing import Any

NUMBER_AND_UNIT_PATTERN = re.compile(
    r"^(?P<prefix>₹)?\s*"
    r"(?P<amount>(?:\d+(?:\.\d+)?|\.\d+|one|a|an|एक))"
    r"\s*(?P<unit>.*?)$",
    re.IGNORECASE,
)
NUMBER_WORDS = {"one": 1.0, "a": 1.0, "an": 1.0, "एक": 1.0}
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def parse_answer(question: dict[str, Any], value: Any) -> Any | None:
    """Return a canonical answer, or None when it does not match the question."""
    question_type = question.get("type")
    if question_type == "choice":
        return parse_choice_answer(value, question)
    if question_type == "boolean":
        return parse_boolean_answer(value, question)
    if question_type == "number":
        return parse_numeric_answer(question, value)
    return None


def parse_choice_answer(value: Any, question: dict[str, Any]) -> str | None:
    if not isinstance(value, str):
        return None
    return _match_option(value, question.get("answer_options", []))


def parse_boolean_answer(value: Any, question: dict[str, Any]) -> bool | None:
    answer_options = question.get("answer_options", [])
    if isinstance(value, bool):
        return value if any(option.get("value") is value for option in answer_options) else None
    if not isinstance(value, str):
        return None
    return _match_option(value, answer_options)


def parse_numeric_answer(question: dict[str, Any], value: Any) -> float | None:
    """Parse a numeric answer using only units declared by its question."""
    numeric = question.get("numeric")
    if question.get("type") != "number" or not isinstance(numeric, dict):
        return None
    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        amount = float(value)
        unit = ""
    elif isinstance(value, str):
        answer = _normalize_text(value)
        match = NUMBER_AND_UNIT_PATTERN.fullmatch(answer)
        if not match:
            return None
        amount_text = match.group("amount")
        amount = _parse_amount(amount_text)
        unit = match.group("unit").strip()
        prefix = match.group("prefix")
        if amount is None or (amount_text in NUMBER_WORDS and not unit):
            return None
        if prefix:
            unit = f"₹{unit}" if unit.startswith("/") else f"₹ {unit}".strip()
    else:
        return None

    if not math.isfinite(amount):
        return None

    unit_factors = numeric.get("unit_factors", {})
    if not unit and not numeric.get("allow_unitless", False):
        return None
    factor = unit_factors.get(unit)
    if factor is None:
        return None

    result = amount * factor
    minimum = numeric.get("minimum", 0)
    minimum_inclusive = numeric.get("minimum_inclusive", True)
    if not math.isfinite(result):
        return None
    if result < minimum or (result == minimum and not minimum_inclusive):
        return None
    return result


def validation_error(question: dict[str, Any], lang: str = "en") -> str:
    """Build an invalid-answer message from the same contract as validation."""
    question_type = question.get("type")
    if question_type in ("choice", "boolean"):
        labels = [
            option.get("labels", {}).get(lang) or option.get("labels", {}).get("en")
            for option in question.get("answer_options", [])
        ]
        labels = [label for label in labels if label]
        if lang == "hi":
            return f"कृपया इनमें से एक विकल्प चुनें: {', '.join(labels)}।"
        return f"Please choose one of the listed options: {', '.join(labels)}."

    unit_labels = question.get("numeric", {}).get("unit_labels", {})
    unit = unit_labels.get(lang) or unit_labels.get("en")
    if lang == "hi":
        return f"कृपया {unit or 'संख्या'} में एक मान्य संख्या दर्ज करें।"
    return f"Please enter a valid number in {unit or 'the requested unit'}."


def normalize_profile(
    profile: dict[str, Any],
    questions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Normalize supplied profile values against each question's contract."""
    normalized = dict(profile)
    if questions is None:
        return normalized

    for field, value in normalized.items():
        question = questions.get(field)
        if question is not None:
            normalized[field] = parse_answer(question, value)
    return normalized


def _match_option(value: str, answer_options: list[dict[str, Any]]) -> Any | None:
    answer = _normalize_text(value)
    for option in answer_options:
        labels = option.get("labels", {}).values()
        candidates = [option.get("value"), *labels, *option.get("aliases", [])]
        if any(isinstance(candidate, str) and _normalize_text(candidate) == answer for candidate in candidates):
            return option.get("value")
    return None


def _parse_amount(value: str) -> float | None:
    number = NUMBER_WORDS.get(value)
    if number is None:
        try:
            number = float(value)
        except ValueError:
            return None
    return number if math.isfinite(number) and number >= 0 else None


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).translate(DEVANAGARI_DIGITS).casefold()
    normalized = normalized.replace("\u200c", "").replace("\u200d", "").replace("\u00a0", " ")
    return " ".join(normalized.split())
