"""Compare the rule-driven selector with the previous fixed question order."""

from services.conversation import get_next_question
from services.eligibility import (
    SCHEMES,
    check_eligibility,
    get_remaining_question_candidates,
)


PROFILES = {
    "farmer": {
        "occupation": "farmer", "age": 45, "gender": "male", "income_level": "bpl",
        "residence_type": "rural", "owns_land": True, "land_size_hectares": 1.5,
        "is_govt_employee": False, "pays_income_tax": False,
        "institutional_land_holder": False, "housing_condition": "kutcha_house",
        "received_housing_scheme_before": False, "ration_card_type": "yellow",
        "is_student": False,
    },
    "student": {
        "occupation": "student", "age": 20, "gender": "female", "income_level": "low_income",
        "residence_type": "urban", "is_student": True,
        "enrolled_in_recognized_institution": True, "category": "sc",
        "family_income_lpa": 1.5, "marital_status": "unmarried",
        "housing_condition": "pucca_house", "received_housing_scheme_before": False,
        "ration_card_type": "white", "owns_land": False,
    },
    "daily wage worker": {
        "occupation": "daily_wage", "age": 35, "gender": "male",
        "income_level": "middle_income", "residence_type": "urban",
        "is_student": False, "ration_card_type": "white",
    },
    "homemaker": {
        "occupation": "housewife", "age": 35, "gender": "female",
        "income_level": "low_income", "residence_type": "rural",
        "marital_status": "married", "is_student": False,
        "housing_condition": "kutcha_house",
        "received_housing_scheme_before": False, "ration_card_type": "yellow",
    },
    "unemployed citizen": {
        "occupation": "unemployed", "age": 40, "gender": "male",
        "income_level": "high_income", "residence_type": "urban",
        "is_student": False, "ration_card_type": "white",
    },
}

LEGACY_BASE_ORDER = ["occupation", "age", "gender", "income_level", "residence_type"]


def legacy_next_question(profile):
    for field in LEGACY_BASE_ORDER:
        if field not in profile:
            return field

    if profile.get("occupation") == "farmer":
        for field in ("owns_land", "land_size_hectares", "is_govt_employee", "pays_income_tax", "institutional_land_holder"):
            if field not in profile:
                if field in ("land_size_hectares", "institutional_land_holder") and not profile.get("owns_land"):
                    continue
                return field

    if profile.get("occupation") == "student" or profile.get("is_student"):
        for field in ("is_student", "enrolled_in_recognized_institution", "category", "family_income_lpa"):
            if field not in profile:
                if field in ("enrolled_in_recognized_institution", "category", "family_income_lpa") and profile.get("is_student") is False:
                    continue
                return field

    if profile.get("gender") == "female" and "marital_status" not in profile:
        return "marital_status"

    if profile.get("residence_type") == "rural" or profile.get("income_level") in ("bpl", "low_income"):
        for field in ("housing_condition", "received_housing_scheme_before"):
            if field not in profile:
                return field

    if profile.get("income_level") in ("bpl", "low_income") and "ration_card_type" not in profile:
        return "ration_card_type"
    return None


def collect_answers(next_question, answers):
    profile = {}
    question_ids = []
    for _ in range(30):
        question_id = next_question(profile)
        if question_id is None:
            return profile, question_ids
        assert question_id in answers, (question_id, question_ids)
        question_ids.append(question_id)
        profile[question_id] = answers[question_id]
    raise AssertionError("Question selector did not stop.")


def current_question_id(profile):
    question = get_next_question(profile)
    return question["id"] if question else None


def test_shorter_conversations_preserve_rule_results_and_required_fields():
    before_total = 0
    after_total = 0

    for name, answers in PROFILES.items():
        _, before_questions = collect_answers(legacy_next_question, answers)
        profile, after_questions = collect_answers(
            current_question_id,
            answers,
        )
        before_total += len(before_questions)
        after_total += len(after_questions)

        assert len(after_questions) == len(set(after_questions)), name
        assert get_remaining_question_candidates(profile) == {}, name
        assert {
            result["scheme_id"]: result["eligible"]
            for result in check_eligibility(profile)
        } == {
            result["scheme_id"]: result["eligible"]
            for result in check_eligibility(answers)
        }, name
        for result in check_eligibility(profile):
            if result["eligible"] is True:
                scheme = next(scheme for scheme in SCHEMES if scheme["id"] == result["scheme_id"])
                assert set(scheme["questions_needed"]).issubset(profile), name

        print(
            f"{name}: {len(before_questions)} → {len(after_questions)} questions; "
            f"repeats={len(after_questions) - len(set(after_questions))}"
        )

    assert after_total < before_total
    print(f"Total: {before_total} → {after_total} questions.")


def test_vague_values_remain_unanswered_and_ruled_out_schemes_stop_consuming_questions():
    partial_profile = {
        "occupation": "not sure",
        "age": 45,
        "gender": "male",
        "income_level": "middle",
        "residence_type": "urban",
        "is_student": False,
    }
    question = get_next_question(partial_profile)
    assert question["id"] == "occupation"

    profile = {
        "occupation": "daily wage worker",
        "age": 35,
        "gender": "male",
        "income_level": "middle",
        "residence_type": "urban",
        "is_student": False,
    }
    assert get_next_question(profile)["id"] == "ration_card_type"
    profile["ration_card_type"] = "white"
    assert get_next_question(profile) is None


def test_contradictions_get_one_clarification_and_never_confirm_conflicted_eligibility():
    profile = {
        "occupation": "farmer",
        "age": 45,
        "gender": "male",
        "income_level": "middle",
        "residence_type": "urban",
        "owns_land": True,
        "land_size_hectares": 0,
        "is_govt_employee": False,
        "pays_income_tax": False,
        "institutional_land_holder": False,
        "is_student": False,
        "ration_card_type": "white",
        "housing_condition": "pucca_house",
        "received_housing_scheme_before": False,
    }
    clarification = get_next_question(profile)
    assert clarification["id"] == "land_size_hectares"
    assert clarification["is_clarification"] is True
    profile["_clarified_fields"] = ["land_size_hectares"]
    assert get_next_question(profile) is None

    pm_kisan = next(
        result for result in check_eligibility(profile)
        if result["scheme_id"] == "pm_kisan"
    )
    assert pm_kisan["eligible"] is None


if __name__ == "__main__":
    test_shorter_conversations_preserve_rule_results_and_required_fields()
    test_vague_values_remain_unanswered_and_ruled_out_schemes_stop_consuming_questions()
    test_contradictions_get_one_clarification_and_never_confirm_conflicted_eligibility()
