"""
Answer grading for interview practice.

The module prefers Gemini when GOOGLE_API_KEY is configured. Without an API key
it falls back to a deterministic rubric matcher so local tests and demos still
produce useful scores.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from config import GOOGLE_API_KEY, LLM_MODEL_NAME, LLM_TEMPERATURE
from src.prompts import FOLLOW_UP_PROMPT, GRADING_PROMPT


def _normalize(text: str) -> set[str]:
    tokens = re.findall(r"[\w+#.]+", text.lower(), flags=re.UNICODE)
    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "cua",
        "co",
        "de",
        "for",
        "in",
        "is",
        "la",
        "mot",
        "of",
        "or",
        "the",
        "thi",
        "to",
        "trong",
        "va",
        "voi",
    }
    return {token for token in tokens if len(token) > 2 and token not in stopwords}


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("LLM response did not contain JSON")
    return json.loads(match.group(0))


def _coerce_grade(payload: dict) -> dict:
    score = float(payload.get("score", 0.0))
    return {
        "score": round(max(0.0, min(10.0, score)), 2),
        "feedback": str(payload.get("feedback", "")).strip(),
        "strengths": list(payload.get("strengths", [])),
        "improvements": list(payload.get("improvements", [])),
    }


def _local_grade(
    expected_answer: str,
    candidate_answer: str,
    scoring_rubric: Optional[str] = None,
) -> dict:
    expected_terms = _normalize(expected_answer)
    candidate_terms = _normalize(candidate_answer)
    rubric_terms = _normalize(scoring_rubric or "")

    if not candidate_answer.strip():
        return {
            "score": 0.0,
            "feedback": "Chua co cau tra loi de cham diem.",
            "strengths": [],
            "improvements": ["Can tra loi bang cac y chinh lien quan den dap an tham khao."],
        }

    expected_overlap = len(expected_terms & candidate_terms) / max(len(expected_terms), 1)
    rubric_overlap = len(rubric_terms & candidate_terms) / max(len(rubric_terms), 1) if rubric_terms else 0.0
    length_ratio = min(len(candidate_answer.split()) / max(len(expected_answer.split()), 1), 1.0)

    score = (0.70 * expected_overlap + 0.20 * rubric_overlap + 0.10 * length_ratio) * 10.0
    strengths = []
    improvements = []

    if expected_overlap >= 0.5:
        strengths.append("Nam duoc nhieu y chinh trong dap an tham khao.")
    elif expected_overlap > 0:
        strengths.append("Co de cap mot phan noi dung lien quan.")
    else:
        improvements.append("Can bo sung cac khai niem cot loi trong dap an tham khao.")

    if rubric_terms and rubric_overlap < 0.5:
        improvements.append("Can bam sat hon cac tieu chi trong rubric.")
    if length_ratio < 0.35:
        improvements.append("Cau tra loi con ngan, can giai thich ro hon.")
    if not improvements:
        improvements.append("Co the bo sung vi du hoac edge case de cau tra loi thuyet phuc hon.")

    return {
        "score": round(float(max(0.0, min(10.0, score))), 2),
        "feedback": "Cham diem bang rubric cuc bo dua tren muc do trung khop y chinh.",
        "strengths": strengths,
        "improvements": improvements,
    }


def _gemini_model():
    import google.generativeai as genai

    genai.configure(api_key=GOOGLE_API_KEY)
    return genai.GenerativeModel(
        LLM_MODEL_NAME,
        generation_config={"temperature": LLM_TEMPERATURE, "response_mime_type": "application/json"},
    )


def grade_answer(
    question: str,
    expected_answer: str,
    candidate_answer: str,
    scoring_rubric: Optional[str] = None,
) -> dict:
    """
    Grade a candidate answer on a 0-10 scale.

    Returns:
        {
            "score": float,
            "feedback": str,
            "strengths": list[str],
            "improvements": list[str]
        }
    """
    rubric = scoring_rubric or "Cham diem theo do dung, do day du, tinh ro rang va vi du minh hoa."

    if GOOGLE_API_KEY:
        prompt = GRADING_PROMPT.format(
            question=question,
            expected_answer=expected_answer,
            candidate_answer=candidate_answer,
            scoring_rubric=rubric,
        )
        try:
            response = _gemini_model().generate_content(prompt)
            return _coerce_grade(_extract_json(response.text))
        except Exception as exc:
            fallback = _local_grade(expected_answer, candidate_answer, rubric)
            fallback["feedback"] += f" LLM grading failed, used local fallback: {exc}"
            return fallback

    return _local_grade(expected_answer, candidate_answer, rubric)


def generate_follow_up(
    question: str,
    candidate_answer: str,
    difficulty: str = "medium",
) -> str:
    """
    Generate one follow-up question based on the candidate's answer.
    """
    if GOOGLE_API_KEY:
        prompt = FOLLOW_UP_PROMPT.format(
            question=question,
            candidate_answer=candidate_answer,
            difficulty=difficulty,
        )
        try:
            response = _gemini_model().generate_content(prompt)
            return response.text.strip()
        except Exception:
            pass

    if difficulty.lower() == "hard":
        return "Neu ap dung vao he thong thuc te, ban se xu ly edge case va trade-off nao?"
    if difficulty.lower() == "easy":
        return "Ban co the giai thich lai bang mot vi du ngan gon khong?"
    return "Ban co the neu them vi du va ly do vi sao cach tiep can nay dung khong?"
