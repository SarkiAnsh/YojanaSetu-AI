"""Contract and API-flow regression tests for answer validation."""

from fastapi.testclient import TestClient

from main import app
from services.conversation import QUESTIONS
from services.input_parsing import parse_answer

client = TestClient(app)


def validate(question_id, answer, lang="en"):
    response = client.post(
        "/api/validate-answer",
        json={"question_id": question_id, "answer": answer, "lang": lang},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_question_contract_accepts_every_canonical_option_and_alias():
    for question_id, question in QUESTIONS.items():
        assert question["id"] == question_id
        assert question["type"] in {"choice", "boolean", "number"}
        assert question["text_en"] and question["text_hi"]

        if question["type"] in {"choice", "boolean"}:
            answer_options = question["answer_options"]
            assert answer_options
            if question["type"] == "choice":
                assert question["options"] == [option["value"] for option in answer_options]
            for option in answer_options:
                assert option["labels"]["en"] and option["labels"]["hi"]
                candidates = [option["labels"]["en"], option["labels"]["hi"], *option["aliases"]]
                if isinstance(option["value"], str):
                    candidates.append(option["value"])
                else:
                    assert parse_answer(question, option["value"]) is option["value"]
                for candidate in candidates:
                    result = validate(question_id, candidate)
                    assert result == {
                        "valid": True,
                        "value": option["value"],
                        "error": None,
                    }, (question_id, candidate, result)
                    if candidate.isascii() and any(character.isalpha() for character in candidate):
                        assert validate(question_id, candidate.upper())["value"] == option["value"]
            invalid = validate(question_id, "__invalid__")
            assert invalid["valid"] is False
            assert invalid["value"] is None
            assert invalid["error"]
            assert "number" not in invalid["error"].lower()
        else:
            numeric = question["numeric"]
            assert numeric["unit"] and numeric["unit_labels"]["en"] and numeric["unit_labels"]["hi"]
            assert numeric["unit_factors"]
            for unit, factor in numeric["unit_factors"].items():
                if unit.startswith("₹"):
                    raw_answer = f"₹1 {unit[1:].strip()}".strip()
                else:
                    raw_answer = f"1 {unit}".strip()
                result = validate(question_id, raw_answer)
                assert result["valid"] is True, (question_id, unit, result)
                assert abs(result["value"] - factor) < 1e-12

            invalid = validate(question_id, "__invalid__")
            assert invalid["valid"] is False
            assert invalid["value"] is None
            assert invalid["error"]


def test_invalid_choices_are_question_scoped_and_localized():
    assert validate("housing_condition", "maybe") == {
        "valid": False,
        "value": None,
        "error": "Please choose one of the listed options: homeless, kutcha house, pucca house.",
    }
    assert validate("income_level", "kutcha house")["valid"] is False
    assert validate("housing_condition", "middle")["valid"] is False
    assert validate("housing_condition", "maybe", "hi")["error"].startswith("कृपया")


def test_housing_answers_and_middle_advance_through_the_api():
    profile = {
        "occupation": "other",
        "age": 25,
        "gender": "male",
        "income_level": "low_income",
        "residence_type": "rural",
        "is_student": False,
        "ration_card_type": "white",
    }
    next_response = client.post("/api/next-question", json={"profile": profile, "lang": "en"})
    assert next_response.status_code == 200
    assert next_response.json()["next_question"]["id"] == "housing_condition"
    assert validate("income_level", "middle")["value"] == "middle_income"

    invalid = validate("housing_condition", "unknown house")
    assert invalid["valid"] is False
    unchanged = client.post("/api/next-question", json={"profile": profile, "lang": "en"})
    assert unchanged.json()["next_question"]["id"] == "housing_condition"

    for raw_answer, canonical in (
        ("kutcha house", "kutcha_house"),
        ("pucca house", "pucca_house"),
        ("homeless", "homeless"),
    ):
        validated = validate("housing_condition", raw_answer)
        assert validated["valid"] is True
        assert validated["value"] == canonical
        advanced = client.post(
            "/api/next-question",
            json={"profile": {**profile, "housing_condition": validated["value"]}, "lang": "en"},
        )
        assert advanced.status_code == 200
        next_question = advanced.json()["next_question"]
        if canonical == "pucca_house":
            assert next_question is None
        else:
            assert next_question["id"] == "received_housing_scheme_before"


def test_numeric_contracts_and_rule_engine_remain_authoritative():
    assert validate("land_size_hectares", "1 hectare")["value"] == 1
    assert validate("land_size_hectares", "1 hectors")["value"] == 1
    assert abs(validate("land_size_hectares", "2 acres")["value"] - 0.80937128448) < 1e-12
    assert validate("age", "25 years")["value"] == 25
    assert validate("age", "2 acres")["valid"] is False

    result = client.post(
        "/api/check-eligibility",
        json={
            "lang": "en",
            "profile": {
                "residence_type": "rural",
                "housing_condition": "kutcha house",
                "income_level": "low",
                "received_housing_scheme_before": "no",
            },
        },
    )
    assert result.status_code == 200
    pm_awas = next(item for item in result.json()["results"] if item["scheme_id"] == "pm_awas_gramin")
    assert pm_awas["eligible"] is True


def test_contradictory_answers_receive_a_single_short_clarification():
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
    response = client.post("/api/next-question", json={"profile": profile, "lang": "en"})
    assert response.status_code == 200
    question = response.json()["next_question"]
    assert question["id"] == "land_size_hectares"
    assert question["is_clarification"] is True
    assert question["text"] == "What is the correct land area?"

    profile["_clarified_fields"] = ["land_size_hectares"]
    completed = client.post("/api/next-question", json={"profile": profile, "lang": "en"})
    assert completed.status_code == 200
    assert completed.json()["done"] is True


def test_completed_rule_matches_are_returned_while_other_questions_remain():
    profile = {
        "occupation": "farmer",
        "age": 45,
        "gender": "male",
        "income_level": "bpl",
        "residence_type": "rural",
        "owns_land": True,
        "land_size_hectares": 1,
        "is_govt_employee": False,
        "pays_income_tax": False,
        "institutional_land_holder": False,
        "housing_condition": "kutcha",
        "received_housing_scheme_before": False,
        "is_student": False,
    }
    response = client.post("/api/next-question", json={"profile": profile, "lang": "en"})
    assert response.status_code == 200
    data = response.json()
    assert data["done"] is False
    assert data["next_question"]["id"] == "ration_card_type"
    assert {match["scheme_id"] for match in data["early_matches"]} == {
        "pm_kisan",
        "pm_awas_gramin",
    }


if __name__ == "__main__":
    test_question_contract_accepts_every_canonical_option_and_alias()
    test_invalid_choices_are_question_scoped_and_localized()
    test_housing_answers_and_middle_advance_through_the_api()
    test_numeric_contracts_and_rule_engine_remain_authoritative()
    test_contradictory_answers_receive_a_single_short_clarification()
    test_completed_rule_matches_are_returned_while_other_questions_remain()
    print("All answer-validation API tests passed.")
