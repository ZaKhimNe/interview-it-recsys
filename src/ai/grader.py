"""
Answer grading for interview practice.
Supports deterministic (MC/TF/Fill) and open-ended (THEORY/PRACTICE/CODING).
"""

from __future__ import annotations
import json
import re
from typing import Optional

from config import GOOGLE_API_KEY, LLM_MODEL_NAME
from src.ai.prompts import FOLLOW_UP_PROMPT, GRADING_PROMPT
from src.kt.scoring import grade as scoring_grade

_DETERMINISTIC_TYPES = {"MC_SINGLE", "TRUE_FALSE", "FILL_BLANK", "CODING_EXERCISE"}
_PASS_THRESHOLD = 6.0
_TIEBREAK_THRESHOLD = 1.5


def grade_answer(question: dict, candidate_response: dict) -> dict:
    qtype = question.get("question_type", "THEORY")
    if qtype in _DETERMINISTIC_TYPES:
        return _grade_deterministic(question, candidate_response)
    return _grade_open_ended(question, candidate_response.get("free_text", ""))


def generate_follow_up(question: dict, candidate_answer: str,
                       grade_result: Optional[dict] = None, difficulty: str = "medium") -> str:
    weak_points = ""
    if grade_result:
        improvements = grade_result.get("improvements", [])
        weak_points = "; ".join(improvements[:2]) if improvements else ""
    if GOOGLE_API_KEY:
        prompt = FOLLOW_UP_PROMPT.format(
            question=question.get("question_text", ""),
            candidate_answer=candidate_answer,
            difficulty=difficulty,
            weak_points=weak_points or "Không có",
        )
        try:
            return _call_gemini(prompt)
        except Exception:
            pass
    if weak_points:
        first = weak_points.split(";")[0].strip()
        return f"Bạn có thể giải thích rõ hơn về: {first}?"
    if difficulty.lower() == "hard":
        return "Nếu áp dụng vào hệ thống thực tế, bạn sẽ xử lý edge case và trade-off nào?"
    if difficulty.lower() == "easy":
        return "Bạn có thể giải thích lại bằng một ví dụ ngắn gọn không?"
    return "Bạn có thể bổ sung ví dụ cụ thể và lý do vì sao cách tiếp cận này phù hợp không?"


def _grade_deterministic(question: dict, candidate_response: dict) -> dict:
    result = scoring_grade(question, candidate_response)
    score_10 = round(float(result["score"]) * 10.0, 2)
    is_correct = result.get("is_correct", score_10 >= _PASS_THRESHOLD)
    feedback = result.get("feedback", "")
    return {
        "score": score_10,
        "feedback": feedback,
        "strengths": ["Câu trả lời chính xác."] if is_correct else [],
        "improvements": [] if is_correct else [feedback or "Xem lại đáp án tham khảo."],
        "method": "deterministic",
        "is_correct": is_correct,
    }


def _grade_open_ended(question: dict, candidate_text: str) -> dict:
    if not candidate_text.strip():
        return _empty_answer_result()
    if GOOGLE_API_KEY:
        return _grade_with_gemini(question, candidate_text)
    return _local_grade(question, candidate_text)


def _grade_with_gemini(question: dict, candidate_text: str) -> dict:
    try:
        answers = question.get("answers", {})
        eval_points = answers.get("evaluation_points", [])
        ep_text = "\n".join(f"- {p}" for p in eval_points) if eval_points else "N/A"
        expected = answers.get("detailed", answers.get("brief", ""))
        prompt = GRADING_PROMPT.format(
            question=question.get("question_text", ""),
            expected_answer=expected[:600] if expected else "N/A",
            evaluation_points=ep_text,
            candidate_answer=candidate_text[:3000],
            scoring_rubric=answers.get("scoring_rubric", "Đánh giá theo mức độ hiểu biết và ví dụ cụ thể."),
        )

        def _call_one():
            try:
                return _parse_gemini_response(_call_gemini_json(prompt))
            except ValueError:
                return _local_grade(question, candidate_text)

        r1 = _call_one()
        r2 = _call_one()
        s1, s2 = r1.get("score", 0.0), r2.get("score", 0.0)
        if abs(s1 - s2) > _TIEBREAK_THRESHOLD:
            r3 = _call_one()
            s3 = r3.get("score", 0.0)
            scores = sorted([s1, s2, s3])
            final_score = scores[1]
            best = r3 if s3 == final_score else (r1 if s1 == final_score else r2)
        else:
            final_score = round((s1 + s2) / 2.0, 2)
            best = r1
        is_correct = final_score >= _PASS_THRESHOLD
        return {
            "score": round(final_score, 2),
            "feedback": best.get("feedback", ""),
            "strengths": best.get("strengths", []),
            "improvements": best.get("improvements", []),
            "method": "gemini",
            "is_correct": is_correct,
        }
    except Exception as e:
        import sys
        print(f"[grader] gemini failed: {e}", file=sys.stderr)
        result = _local_grade(question, candidate_text)
        result["gemini_error"] = str(e)
        return result


def _local_grade(question: dict, candidate_text: str) -> dict:
    """Fallback dùng scoring_grade từ src.kt.scoring — logic chuẩn, có eval_points."""
    candidate_response = {"free_text": candidate_text}
    result = scoring_grade(question, candidate_response)

    score_10 = round(float(result["score"]) * 10.0, 2)
    is_correct = score_10 >= _PASS_THRESHOLD

    eval_points = question.get("answers", {}).get("evaluation_points", [])
    n_matched = int(result.get("matched_points", 0))
    strengths    = eval_points[:n_matched][:2] if eval_points and n_matched > 0 else (["Đề cập nội dung cơ bản."] if score_10 >= 6 else [])
    improvements = eval_points[n_matched:][:3] if eval_points else (["Bổ sung ví dụ và chi tiết kỹ thuật."] if not is_correct else [])

    return {
        "score": score_10,
        "feedback": result.get("feedback", ""),
        "strengths": strengths,
        "improvements": improvements,
        "method": "local_rubric",
        "is_correct": is_correct,
    }


def _local_feedback(layer1: float, eval_points: list) -> str:
    if layer1 >= 0.8:
        return "Câu trả lời tốt, đủ ý chính."
    if layer1 >= 0.5:
        missed = eval_points[int(len(eval_points) * layer1):][:2]
        hint = "; ".join(missed) if missed else ""
        return ("Đủ một phần. Cần bổ sung: " + hint) if hint else "Đủ một phần, cần thêm chi tiết."
    return "Còn thiếu nhiều ý chính. Xem lại đáp án tham khảo."


def _extract_score_dict(data: dict) -> dict:
    score = float(data.get("score", 5.0))
    return {
        "score": max(0.0, min(10.0, score)),
        "feedback": str(data.get("feedback", "")),
        "strengths": list(data.get("strengths", [])),
        "improvements": list(data.get("improvements", [])),
    }


def _sanitize_json_strings(text: str) -> str:
    result = []
    in_str = False
    esc = False
    for c in text:
        if esc:
            esc = False
            result.append(c)
            continue
        if c == "\\" and in_str:
            esc = True
            result.append(c)
            continue
        if c == chr(34):  # double quote
            in_str = not in_str
            result.append(c)
            continue
        if in_str:
            if c == "\n":
                result.append("\\n")
                continue
            if c == "\r":
                result.append("\\r")
                continue
            if c == "\t":
                result.append("\\t")
                continue
        result.append(c)
    return "".join(result)


def _find_balanced_json(text: str):
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i, c in enumerate(text[start:], start):
        if esc:
            esc = False
            continue
        if c == "\\" and in_str:
            esc = True
            continue
        if c == chr(34):
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None


def _parse_gemini_response(text: str) -> dict:
    import sys
    text = text.strip()
    sanitized = _sanitize_json_strings(text)
    for candidate in (sanitized, text):
        try:
            return _extract_score_dict(json.loads(candidate))
        except (json.JSONDecodeError, ValueError):
            pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", sanitized, re.DOTALL)
    if m:
        try:
            return _extract_score_dict(json.loads(m.group(1)))
        except (json.JSONDecodeError, ValueError):
            pass
    candidate = _find_balanced_json(sanitized)
    if candidate:
        try:
            return _extract_score_dict(json.loads(candidate))
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[grader] balanced JSON parse failed: {e}", file=sys.stderr)
    print(f"[grader] JSON parse failed. text[:80]={text[:80]!r}", file=sys.stderr)
    raise ValueError("Cannot parse Gemini JSON response")


def _empty_answer_result() -> dict:
    return {
        "score": 0.0,
        "feedback": "Không có câu trả lời.",
        "strengths": [],
        "improvements": ["Hãy trả lời câu hỏi."],
        "method": "empty",
        "is_correct": False,
    }


_gemini_client = None


def _get_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
    return _gemini_client


def _call_gemini_json(prompt: str) -> str:
    if not GOOGLE_API_KEY:
        raise RuntimeError("[grader] GOOGLE_API_KEY not set")
    from google.genai import types
    resp = _get_client().models.generate_content(
        model=LLM_MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="low"),
            response_mime_type="application/json",
            max_output_tokens=1024,
        ),
    )
    return resp.text.strip()


def _call_gemini(prompt: str) -> str:
    if not GOOGLE_API_KEY:
        raise RuntimeError("[grader] GOOGLE_API_KEY not set")
    from google.genai import types
    resp = _get_client().models.generate_content(
        model=LLM_MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="low"),
            max_output_tokens=256,
        ),
    )
    return resp.text.strip()
