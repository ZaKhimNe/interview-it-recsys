"""
Scoring Engine — tinh diem cau tra loi theo tung loai cau hoi.

Fixes:
  - _match_key_points: yeu cau majority keywords khop (>=50%), khong phai bat ky 1 keyword
  - grade_theory fallback: neu khong co eval_points, dung keyword Jaccard vs answers.detailed
  - update_skill_vector: doi scale 0-5 -> 0-1 de dong bo voi competency_engine
  - _fuzzy_match: them strip punctuation + substring fallback
"""

import re
from datetime import datetime, timezone
from typing import Optional


# ── Public graders ─────────────────────────────────────────────────────────────

def grade_theory(question: dict, user_answer: str) -> dict:
    answers = question.get("answers", {})
    evaluation_points = answers.get("evaluation_points", [])

    if evaluation_points:
        matched = _match_key_points(user_answer, evaluation_points)
        total = len(evaluation_points)
    else:
        # Fallback: keyword Jaccard vs answers.detailed
        expected = answers.get("detailed", "")
        if expected:
            candidate_tok = _tokenize(user_answer)
            expected_tok  = _tokenize(expected)
            if expected_tok:
                ratio = len(candidate_tok & expected_tok) / len(expected_tok)
            else:
                ratio = 0.0
            # Map ratio -> matched/total (virtual 5 points)
            total   = 5
            matched = round(ratio * total)
        else:
            total, matched = 1, 0

    score = round(matched / total, 2) if total > 0 else 0.0
    return {
        "matched_points": matched,
        "total_points": total,
        "score": score,
        "is_correct": score >= 0.6,
        "feedback": _build_feedback(matched, total, evaluation_points),
    }


def grade_practice(question: dict, user_answer: str) -> dict:
    return grade_theory(question, user_answer)


def grade_mc_single(question: dict, selected_option_id: str) -> dict:
    correct = question.get("answers", {}).get("correct_option_id", "")
    is_correct = str(selected_option_id).strip() == str(correct).strip()
    return {
        "matched_points": 1.0 if is_correct else 0.0,
        "total_points": 1.0,
        "score": 1.0 if is_correct else 0.0,
        "is_correct": is_correct,
        "feedback": "Chinh xac!" if is_correct
                    else question.get("answers", {}).get("explanation", "Sai dap an."),
    }


def grade_true_false(question: dict, user_answer: bool) -> dict:
    correct = question.get("answers", {}).get("correct_answer")
    is_correct = bool(user_answer) == bool(correct)
    return {
        "matched_points": 1.0 if is_correct else 0.0,
        "total_points": 1.0,
        "score": 1.0 if is_correct else 0.0,
        "is_correct": is_correct,
        "feedback": "Chinh xac!" if is_correct
                    else question.get("answers", {}).get("explanation", "Sai dap an."),
    }


def grade_fill_blank(question: dict, blank_answers: list[str]) -> dict:
    accepted = question.get("answers", {}).get("accepted_answers", [])
    total = len(accepted)
    if total == 0:
        return {
            "matched_points": 0.0,
            "total_points": 1.0,
            "score": 0.0,
            "is_correct": False,
            "feedback": "Khong co dap an tham khao.",
        }

    matched = sum(
        1 for i, user_val in enumerate(blank_answers)
        if i < total and _fuzzy_match(user_val, accepted[i])
    )
    score = round(matched / total, 2)
    return {
        "matched_points": float(matched),
        "total_points": float(total),
        "score": score,
        "is_correct": score >= 0.6,
        "feedback": _fill_blank_feedback(accepted, blank_answers, matched, total),
    }


def grade_coding(question: dict, user_answer: str) -> dict:
    return grade_theory(question, user_answer)


def grade_coding_exercise(question: dict, user_code: str) -> dict:
    test_cases = question.get("test_cases", [])
    if not test_cases:
        return grade_theory(question, user_code)

    passed, failed_details = 0, []
    for tc in test_cases:
        if _run_test_case(user_code, tc):
            passed += 1
        else:
            failed_details.append(
                f"Input: {tc.get('input')} -> Expected: {tc.get('expected_output')}"
            )

    total = len(test_cases)
    score = round(passed / total, 2) if total > 0 else 0.0
    feedback = f"Passed {passed}/{total} test cases."
    if failed_details:
        feedback += "\nFailed:\n" + "\n".join(f"  - {d}" for d in failed_details[:3])
    return {
        "matched_points": float(passed),
        "total_points": float(total),
        "score": score,
        "is_correct": score >= 0.75,
        "feedback": feedback,
    }


def grade(question: dict, response: dict) -> dict:
    """Dispatcher chinh theo question_type. Tra ve score trong [0, 1]."""
    qtype = question.get("question_type", "THEORY")
    if qtype in ("THEORY", "PRACTICE"):
        return grade_theory(question, response.get("free_text", ""))
    elif qtype == "MC_SINGLE":
        return grade_mc_single(question, response.get("selected_option_id", ""))
    elif qtype == "TRUE_FALSE":
        return grade_true_false(question, response.get("bool_answer", False))
    elif qtype == "FILL_BLANK":
        return grade_fill_blank(question, response.get("blank_answers", []))
    elif qtype == "CODING_EXERCISE":
        return grade_coding_exercise(question, response.get("code_submitted", ""))
    elif qtype == "CODING":
        return grade_coding(question, response.get("free_text", ""))
    else:
        return grade_theory(question, response.get("free_text", ""))


# ── Skill vector update ────────────────────────────────────────────────────────

def update_skill_vector(
    skill_vector: dict,
    question: dict,
    score: float,
    taxonomy: Optional[dict] = None,
) -> dict:
    """
    Cap nhat skill_vector (scale 0-1) sau khi tra loi.
    score: [0, 1] — tu grade() dispatcher.
    Su dung EMA giong competency_engine de nhat quan.
    """
    LEARNING_RATE   = 0.08
    FORGETTING_RATE = 0.002

    for group in question.get("skill_groups", []):
        if group not in skill_vector:
            continue
        current = float(skill_vector[group])
        if score >= 0.6:
            skill_vector[group] = round(min(0.99, current + LEARNING_RATE * (1.0 - current)), 4)
        else:
            skill_vector[group] = round(max(0.05, current - FORGETTING_RATE * current), 4)
    return skill_vector


def update_tag_stats(
    tag_stats: dict,
    question: dict,
    score: float,
    is_correct: bool,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    for tag in question.get("skill_tags", []):
        entry = tag_stats.get(tag)
        if entry is None:
            tag_stats[tag] = {
                "attempted": 1,
                "correct": 1 if is_correct else 0,
                "avg_score": round(score, 2),
                "last_updated": now,
            }
        else:
            old = entry["attempted"]
            entry["attempted"] += 1
            if is_correct:
                entry["correct"] += 1
            entry["avg_score"] = round((entry["avg_score"] * old + score) / entry["attempted"], 2)
            entry["last_updated"] = now
    return tag_stats


def map_tags_to_groups(skill_tags: list[str], taxonomy: dict) -> list[str]:
    groups = set()
    for group_code, group_data in taxonomy.items():
        if isinstance(group_data, dict):
            tags = group_data.get("tags", [])
            if any(t in tags for t in skill_tags):
                groups.add(group_code)
    return sorted(groups)


# ── Internal helpers ───────────────────────────────────────────────────────────

_STOPWORDS = {
    "a","an","and","are","as","be","by","for","in","is","of","or","the","to","with",
    "co","cua","de","la","mot","thi","trong","va","voi","that","this","it","its",
}


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[\w]+", text.lower())
    return {t for t in tokens if len(t) >= 3 and t not in _STOPWORDS}


def _match_key_points(user_answer: str, evaluation_points: list[str]) -> int:
    """
    Kiem tra tung eval_point co duoc de cap trong user_answer.
    Mot point duoc coi la 'covered' khi >= 50% keywords cua no xuat hien.
    (Tranh false positive khi chi co 1 tu chung xuyen nhu 'data', 'model')
    """
    matched = 0
    candidate_lower = user_answer.lower()
    for point in evaluation_points:
        keywords = [w for w in re.findall(r"[\w]+", point.lower())
                    if len(w) >= 4 and w not in _STOPWORDS]
        if not keywords:
            matched += 1   # point rong hoac toan stopword -> bo qua
            continue
        hits = sum(1 for kw in keywords if kw in candidate_lower)
        # Can >= 50% keywords khop moi tinh la covered
        if hits / len(keywords) >= 0.5:
            matched += 1
    return matched


def _build_feedback(matched: int, total: int, evaluation_points: list[str]) -> str:
    if total == 0:
        return "Khong co tieu chi danh gia."
    pct = matched / total
    if pct >= 0.8:
        return f"Tot! Ban dat {matched}/{total} y chinh."
    elif pct >= 0.5:
        missed = [p for p in evaluation_points[matched:matched+2]]
        hint = "; ".join(missed) if missed else ""
        return f"Kha! Ban dat {matched}/{total} y. Con thieu: {hint}"
    else:
        hint = "; ".join(evaluation_points[:3])
        return f"Can cai thien ({matched}/{total}). Goi y: {hint}"


def _fill_blank_feedback(
    accepted: list[list[str]], given: list[str], matched: int, total: int
) -> str:
    parts = []
    for i, (acc, giv) in enumerate(zip(accepted, given)):
        status = "V" if _fuzzy_match(giv, acc) else "X"
        parts.append(f"#{i+1}: {status} ban='{giv}' | dap an={acc}")
    return f"Dung {matched}/{total}.\n" + "\n".join(parts)


def _fuzzy_match(user_val: str, accepted_vals: list[str]) -> bool:
    """Exact match (lowercase, strip punct). Fallback: substring neu user_val dai >= 4."""
    if not user_val:
        return False
    cleaned = re.sub(r"[^\w\s]", "", user_val.strip().lower())
    for a in accepted_vals:
        norm = re.sub(r"[^\w\s]", "", a.strip().lower())
        if cleaned == norm:
            return True
        # Substring fallback cho truong hop user viet day du hon
        if len(cleaned) >= 4 and (cleaned in norm or norm in cleaned):
            return True
    return False


def _run_test_case(user_code: str, test_case: dict) -> bool:
    """Chay code nguoi dung voi test_case. Khong sandbox — chi dung internal."""
    input_data = test_case.get("input", "")
    expected   = test_case.get("expected_output", "")
    try:
        local_env: dict = {}
        exec(user_code, {}, local_env)  # nosec
        func_name = _find_function_name(user_code)
        if func_name and func_name in local_env:
            result = local_env[func_name](input_data)
            return str(result).strip() == str(expected).strip()
        return False
    except Exception:
        return False


def _find_function_name(code: str) -> Optional[str]:
    m = re.search(r"def\s+(\w+)\s*\(", code)
    return m.group(1) if m else None
