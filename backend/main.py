"""
main.py — YojanaSetu AI FastAPI Backend

This is the entry point for the backend server.
Run with: uvicorn main:app --reload

Endpoints:
  POST /api/validate-answer    → Validate one raw answer against its question
  POST /api/check-eligibility  → Check schemes for a user profile
  POST /api/next-question      → Get the next question to ask
  GET  /api/schemes            → List all demo schemes
  GET  /api/health             → Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional
import json
from pathlib import Path

from services.eligibility import check_eligibility
from services.conversation import QUESTIONS, get_next_question, detect_contradictions
from services.assistant import AssistantServiceError, generate_clarification
from services.input_parsing import parse_answer, validation_error

# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="YojanaSetu AI API",
    description="[DEMO] Bilingual welfare scheme eligibility checker",
    version="0.1.0"
)

# Allow the React frontend (running on localhost:5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response models ─────────────────────────────────────────────────

class ProfileRequest(BaseModel):
    """User's collected answers so far."""
    profile: dict[str, Any]
    lang: Optional[str] = "en"  # "en" or "hi"


class NextQuestionRequest(BaseModel):
    """Ask the server: given what we know, what should we ask next?"""
    profile: dict[str, Any]
    lang: Optional[str] = "en"


class AnswerValidationRequest(BaseModel):
    """Validate one raw answer using the current question's contract."""
    question_id: str
    answer: str = Field(max_length=500)
    lang: Literal["en", "hi"] = "en"


class ClarificationRequest(BaseModel):
    """Ask the optional AI assistant to clarify the current rule-based question."""
    question_id: str
    message: str = Field(min_length=1, max_length=500)
    lang: Literal["en", "hi"] = "en"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    """Simple check to confirm the server is running."""
    return {"status": "ok", "message": "YojanaSetu AI backend is running!"}


@app.get("/api/schemes")
def list_schemes(lang: str = "en"):
    """
    Returns the list of all 5 demo schemes with names and descriptions.
    No personal data needed.
    """
    data_path = Path(__file__).parent / "data" / "schemes_demo.json"
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    schemes = []
    for s in data["schemes"]:
        schemes.append({
            "id": s["id"],
            "name": s[f"name_{lang}"],
            "description": s[f"description_{lang}"],
            "benefit": s[f"benefit_{lang}"],
            "apply_at": s[f"apply_at_{lang}"],
        })
    return {
        "schemes": schemes,
        "note": data["_note"]
    }


@app.post("/api/next-question")
def next_question(req: NextQuestionRequest):
    """
    Given the current user profile (answered questions so far),
    return the next question to ask — or null if we have enough info.

    Also returns any contradiction warnings.
    """
    contradictions = detect_contradictions(req.profile, req.lang)
    next_q = get_next_question(req.profile, req.lang)
    early_matches = []
    if not contradictions and next_q is not None:
        early_matches = [
            {"scheme_id": result["scheme_id"], "name": result["name"]}
            for result in check_eligibility(req.profile, req.lang)
            if result["eligible"] is True
        ]

    return {
        "next_question": next_q,
        "contradictions": contradictions,
        "early_matches": early_matches,
        "done": next_q is None
    }


@app.post("/api/validate-answer")
def validate_answer_endpoint(req: AnswerValidationRequest):
    """Normalize one answer using the authoritative backend question contract."""
    question = QUESTIONS.get(req.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Unknown question_id")

    value = parse_answer(question, req.answer)
    if value is None:
        return {
            "valid": False,
            "value": None,
            "error": validation_error(question, req.lang),
        }
    return {"valid": True, "value": value, "error": None}


@app.post("/api/chat")
async def chat_clarification(req: ClarificationRequest):
    """Return a conversational clarification without changing the rule-based flow."""
    question = QUESTIONS.get(req.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Unknown question_id")

    prompt_context = {
        "text": question[f"text_{req.lang}"],
        "type": question["type"],
        "options": [
            answer["labels"][req.lang]
            for answer in question.get("answer_options", [])
        ] or question.get("options", []),
    }
    try:
        reply = await generate_clarification(req.message, prompt_context, req.lang)
    except AssistantServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"reply": reply}


@app.post("/api/check-eligibility")
def check_eligibility_endpoint(req: ProfileRequest):
    """
    Given a completed user profile, return eligibility results for all 5 schemes.

    Each result includes:
    - eligible: True / False / None (not enough info)
    - reasons: list of plain-language explanations
    - benefit: what you get
    - apply_at: where to apply
    """
    if not req.profile:
        raise HTTPException(status_code=400, detail="Profile cannot be empty")

    # Check for contradictions before running eligibility
    contradictions = detect_contradictions(req.profile, req.lang)

    results = check_eligibility(req.profile, req.lang)

    # Separate into eligible, not eligible, insufficient info
    eligible = [r for r in results if r["eligible"] is True]
    not_eligible = [r for r in results if r["eligible"] is False]
    unclear = [r for r in results if r["eligible"] is None]

    return {
        "results": results,
        "summary": {
            "eligible_count": len(eligible),
            "not_eligible_count": len(not_eligible),
            "unclear_count": len(unclear),
            "eligible_schemes": [r["name"] for r in eligible],
        },
        "contradictions": contradictions,
        "disclaimer": "[DEMO DATA] This tool provides educational guidance only. "
                      "Always verify eligibility at official government portals. "
                      "This system does not connect to or represent any government database."
    }
