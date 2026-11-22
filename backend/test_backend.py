"""Quick tests for the YojanaSetu AI backend logic."""
import math
import sys
sys.path.insert(0, '.')

from services.eligibility import check_eligibility, get_remaining_question_candidates
from services.conversation import QUESTIONS, detect_contradictions, get_next_question
from services.input_parsing import normalize_profile, parse_numeric_answer

PASS = "[PASS]"
FAIL = "[FAIL]"


def parse_number(field, value):
    return parse_numeric_answer(QUESTIONS[field], value)


# ── Test 1: Farmer profile ────────────────────────────────────────────────────
print("=== TEST 1: Farmer, 1.5ha, BPL, rural, kutcha house ===")
p1 = {
    "occupation": "farmer", "owns_land": True, "land_size_hectares": 1.5,
    "is_govt_employee": False, "pays_income_tax": False,
    "institutional_land_holder": False,
    "income_level": "bpl", "residence_type": "rural",
    "housing_condition": "kutcha_house", "received_housing_scheme_before": False,
    "gender": "male", "age": 45
}
results1 = check_eligibility(p1, "en")
for r in results1:
    status = "ELIGIBLE" if r["eligible"] else ("NOT" if r["eligible"] is False else "UNCLEAR")
    print(f"  {status:10}  {r['name']}")

pm_kisan = next(r for r in results1 if r["scheme_id"] == "pm_kisan")
pm_awas  = next(r for r in results1 if r["scheme_id"] == "pm_awas_gramin")
assert pm_kisan["eligible"] is True,  "PM Kisan should be eligible for small farmer"
assert pm_awas["eligible"] is True,   "PM Awas should be eligible for rural BPL kutcha house"
print(PASS, "Farmer profile correct")

# ── Test 2: Widow profile ─────────────────────────────────────────────────────
print("\n=== TEST 2: Widow, 55yo, BPL ===")
p2 = {
    "gender": "female", "marital_status": "widow", "age": 55,
    "income_level": "bpl", "ration_card_type": "yellow", "residence_type": "urban"
}
results2 = check_eligibility(p2, "en")
for r in results2:
    status = "ELIGIBLE" if r["eligible"] else ("NOT" if r["eligible"] is False else "UNCLEAR")
    print(f"  {status:10}  {r['name']}")

widow = next(r for r in results2 if r["scheme_id"] == "widow_pension_ignwps")
assert widow["eligible"] is True, "Widow pension should be eligible"
print(PASS, "Widow profile correct")

# ── Test 3: Student profile ───────────────────────────────────────────────────
print("\n=== TEST 3: Student, SC, age 20, income 1.5L ===")
p3 = {
    "occupation": "student", "is_student": True, "age": 20,
    "gender": "female", "category": "sc",
    "family_income_lpa": 1.5, "income_level": "low_income",
    "enrolled_in_recognized_institution": True,
}
results3 = check_eligibility(p3, "en")
for r in results3:
    status = "ELIGIBLE" if r["eligible"] else ("NOT" if r["eligible"] is False else "UNCLEAR")
    print(f"  {status:10}  {r['name']}")

scholarship = next(r for r in results3 if r["scheme_id"] == "national_scholarship")
assert scholarship["eligible"] is True, "Scholarship should be eligible for SC student"
print(PASS, "Student profile correct")

# ── Test 4: Contradiction detection ──────────────────────────────────────────
print("\n=== TEST 4: Contradiction — farmer with no land ===")
contradictions = detect_contradictions({"occupation": "farmer", "owns_land": False}, "en")
assert len(contradictions) == 1, "Should detect farmer+no-land contradiction"
print(f"  Detected: {contradictions[0][:70]}...")
print(PASS, "Contradiction detection correct")

# ── Test 5: Hindi contradiction message ──────────────────────────────────────
print("\n=== TEST 5: Hindi contradiction message ===")
c_hi = detect_contradictions({"occupation": "farmer", "owns_land": False}, "hi")
assert len(c_hi) == 1
print(f"  Hindi: {c_hi[0][:60]}...")
print(PASS, "Hindi contradiction message works")

# ── Test 6: Question flow ─────────────────────────────────────────────────────
print("\n=== TEST 6: Question ordering ===")
q1 = get_next_question({}, "en")
assert q1["id"] == "income_level", f"First high-value question should be income, got {q1['id']}"
print(f"  Q1 (empty): {q1['id']} - covers multiple schemes")

q2 = get_next_question({
    "income_level": "middle",
    "occupation": "daily_wage",
    "is_student": False,
}, "en")
assert q2["id"] == "ration_card_type", f"Only unresolved scheme question should be ration card, got {q2['id']}"
assert get_next_question({
    "income_level": "middle",
    "occupation": "daily_wage",
    "is_student": False,
    "ration_card_type": "white",
}, "en") is None
print("  Ruled-out schemes are skipped; unaskable official checks stop without extra questions")

# After all base questions + farmer occupation, should ask farmer-specific q
p_base_farmer = {
    "occupation": "farmer", "age": 45, "gender": "male",
    "income_level": "bpl", "residence_type": "rural"
}
q3 = get_next_question(p_base_farmer, "en")
assert q3["id"] == "owns_land", f"Should ask owns_land for farmer, got {q3['id']}"
print(f"  Q3 (base done, farmer): {q3['id']} - correct")

# After owns_land=False, should NOT ask land_size
p_no_land = dict(p_base_farmer, owns_land=False)
q4 = get_next_question(p_no_land, "en")
assert q4["id"] != "land_size_hectares", "Should skip land_size when no land"
print(f"  Q4 (no land): {q4['id']} (unnecessary farmer questions skipped)")
q_unknown = get_next_question({
    "occupation": "not sure",
    "age": 45,
    "gender": "male",
    "income_level": "middle",
    "residence_type": "urban",
    "is_student": False,
}, "en")
assert q_unknown["id"] == "occupation", "Vague occupation should remain unanswered"
print("  Vague answers remain unanswered")
canonical_choices = normalize_profile({
    "income_level": "middle",
    "gender": "FEMALE",
    "occupation": "daily wage worker",
    "owns_land": "no",
}, QUESTIONS)
assert canonical_choices == {
    "income_level": "middle_income",
    "gender": "female",
    "occupation": "daily_wage",
    "owns_land": False,
}
assert normalize_profile({"income_level": "LOW"}, QUESTIONS)["income_level"] == "low_income"
assert normalize_profile({"income_level": "BPL"}, QUESTIONS)["income_level"] == "bpl"
assert normalize_profile({"income_level": "मध्यम"}, QUESTIONS)["income_level"] == "middle_income"
invalid_income_profile = {
    "occupation": "farmer", "age": 35, "gender": "male",
    "income_level": "invalid", "residence_type": "rural",
}
assert get_next_question(invalid_income_profile, "en")["id"] == "income_level"
p_farmer_exclusions = dict(
    p_base_farmer,
    owns_land=True,
    land_size_hectares=1.5,
    is_govt_employee=False,
    pays_income_tax=False,
)
q_institution = get_next_question(p_farmer_exclusions, "en")
assert "institutional_land_holder" in get_remaining_question_candidates(p_farmer_exclusions)
print("  All remaining rule-required farmer exclusions stay askable")
p_student_base = {
    "occupation": "student", "age": 20, "gender": "female",
    "income_level": "low_income", "residence_type": "urban",
    "is_student": True,
}
q_enrollment = get_next_question(p_student_base, "en")
assert q_enrollment["id"] in get_remaining_question_candidates(p_student_base)
assert {"enrolled_in_recognized_institution", "category", "family_income_lpa"}.issubset(
    get_remaining_question_candidates(p_student_base)
)
print("  Only remaining scholarship requirements are candidates")
assert not detect_contradictions({"occupation": "student", "age": "not sure"}, "en")
print("  Vague age does not crash contradiction checks")
assert "age" in get_remaining_question_candidates({"occupation": "student", "age": "2 acres"})
assert detect_contradictions({"occupation": "student", "age": "३६"}, "en")
print(PASS, "Question flow correct")

# ── Test 7: Large farmer excluded ─────────────────────────────────────────────
print("\n=== TEST 7: Large farmer (3ha) should NOT get PM Kisan ===")
p_large = dict(p1, land_size_hectares=3.0)
results_large = check_eligibility(p_large, "en")
pm_kisan_large = next(r for r in results_large if r["scheme_id"] == "pm_kisan")
assert pm_kisan_large["eligible"] is False, "Large farmer should not qualify"
print(f"  3ha farmer PM Kisan eligible: {pm_kisan_large['eligible']} (expected False)")
print(PASS, "Large farmer exclusion correct")

# ── Test 8: Missing evidence is insufficient, not eligible ───────────────────
print("\n=== TEST 8: Empty profile remains insufficient ===")
empty_results = check_eligibility({}, "en")
for scheme_id in ("pm_kisan", "ayushman_bharat", "national_scholarship"):
    result = next(r for r in empty_results if r["scheme_id"] == scheme_id)
    assert result["eligible"] is None, f"{scheme_id} needs evidence before a positive result"
ayushman_empty = next(r for r in empty_results if r["scheme_id"] == "ayushman_bharat")
assert not any("Final eligibility verified via SECC" in reason for reason in ayushman_empty["reasons"])
print(PASS, "Missing evidence is not treated as eligibility")

# ── Test 9: Missing student status is not interpreted as not-a-student ───────
print("\n=== TEST 9: Partial scholarship profile is insufficient ===")
partial_student = {
    "age": 20, "category": "sc", "family_income_lpa": 1.5,
    "enrolled_in_recognized_institution": True,
}
scholarship_partial = next(
    r for r in check_eligibility(partial_student, "en")
    if r["scheme_id"] == "national_scholarship"
)
assert scholarship_partial["eligible"] is None
print(PASS, "Missing student status remains insufficient")

# ── Test 10: Institutional landholder exclusion ──────────────────────────────
print("\n=== TEST 10: Institutional landholder is excluded ===")
p_institution = dict(p1, institutional_land_holder=True)
institution_result = next(
    r for r in check_eligibility(p_institution, "en")
    if r["scheme_id"] == "pm_kisan"
)
assert institution_result["eligible"] is False
print(PASS, "Institutional landholder exclusion works")

# ── Test 11: Conflicting Ayushman indicators remain unresolved ───────────────
print("\n=== TEST 11: Conflicting indicators remain unresolved ===")
p_conflicting = {
    "income_level": "high_income",
    "ration_card_type": "yellow",
    "state": "Maharashtra",
    "secc_listed": True,
}
ayushman_conflicting = next(
    r for r in check_eligibility(p_conflicting, "en")
    if r["scheme_id"] == "ayushman_bharat"
)
assert ayushman_conflicting["eligible"] is None
assert any("conflict" in reason.lower() for reason in ayushman_conflicting["reasons"])
print(PASS, "Conflicting eligibility indicators are flagged")

# ── Test 12: Income alone does not determine Ayushman eligibility ─────────────
print("\n=== TEST 12: Ayushman income alone is insufficient ===")
p_high_income = {
    "income_level": "high_income",
    "ration_card_type": "white",
    "state": "Maharashtra",
}
ayushman_high_income = next(
    r for r in check_eligibility(p_high_income, "en")
    if r["scheme_id"] == "ayushman_bharat"
)
assert ayushman_high_income["eligible"] is None
print(PASS, "SECC verification remains authoritative")

# ── Test 13: Unit-aware land input parsing ──────────────────────────────────
print("\n=== TEST 13: Land quantities, units, and safe clarification ===")
assert parse_number("land_size_hectares", "1 hectare") == 1
assert parse_number("land_size_hectares", "1 hectors") == 1
assert parse_number("land_size_hectares", "1.5 hectares") == 1.5
assert parse_number("land_size_hectares", "एक हेक्टेयर") == 1
assert parse_number("land_size_hectares", "१ हेक्टेयर") == 1
assert math.isclose(
    parse_number("land_size_hectares", "2 acres"),
    2 * 0.40468564224,
)
assert parse_number("land_size_hectares", "-1 hectare") is None
assert parse_number("land_size_hectares", "1 hectare and 2 acres") is None
assert parse_number("land_size_hectares", "about one acre") is None
assert parse_number("age", "2 acres") is None
assert parse_number("family_income_lpa", "2 acres") is None
assert parse_number("family_income_lpa", "1.5 lakhs") == 1.5
assert parse_number("family_income_lpa", "₹1.5 lakh per year") == 1.5
assert parse_number("family_income_lpa", "१.५ लाख") == 1.5
assert parse_number("family_income_lpa", "एक लाख") == 1
assert parse_number("family_income_lpa", "₹50000") == 0.5
assert parse_number("family_income_lpa", "50000 rupees") == 0.5
assert parse_number("age", "25 years") == 25
assert parse_number("age", "२५ वर्ष") == 25
assert parse_number("age", "-25 years") is None
assert parse_number("age", "1.5 lakhs") is None
assert parse_number("land_size_hectares", "1.5 lakhs") is None
p3_lakh = dict(p3, family_income_lpa="1.5 lakhs")
scholarship_lakh = next(
    r for r in check_eligibility(p3_lakh, "en")
    if r["scheme_id"] == "national_scholarship"
)
assert scholarship_lakh["eligible"] is True

p_invalid_land = dict(p1, land_size_hectares="1 hectare and 2 acres")
pm_kisan_invalid_land = next(
    r for r in check_eligibility(p_invalid_land, "en")
    if r["scheme_id"] == "pm_kisan"
)
assert pm_kisan_invalid_land["eligible"] is None

land_conflict = detect_contradictions({
    "occupation": "farmer",
    "owns_land": False,
    "land_size_hectares": "1 hectare",
}, "en")
assert any("reported 1 hectares" in message for message in land_conflict)

q_retry_land = get_next_question({
    **p_base_farmer,
    "owns_land": True,
    "land_size_hectares": "one hectare and two acres",
    "is_govt_employee": False,
    "pays_income_tax": False,
}, "en")
assert "land_size_hectares" in get_remaining_question_candidates({
    **p_base_farmer,
    "owns_land": True,
    "land_size_hectares": "one hectare and two acres",
    "is_govt_employee": False,
    "pays_income_tax": False,
})
print(PASS, "Unit conversion, invalid values, retries, and contradictions work")

print("\n" + "="*50)
print("ALL 13 TESTS PASSED - Backend logic is working correctly!")
