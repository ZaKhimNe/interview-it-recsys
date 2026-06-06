"""
📊 Scoring Engine
==================
Phụ trách: Data Lead
Mục đích: Tính điểm cho câu trả lời dựa trên loại câu hỏi.
          Hỗ trợ: THEORY, PRACTICE, CODING, CODING_EXERCISE,
                 MC_SINGLE, FILL_BLANK, TRUE_FALSE
"""

from datetime import datetime, timezone
from typing import Any, Optional


def grade_theory(question: dict, user_answer: str) -> dict:
    evaluation_points = question.get("answers", {}).get("evaluation_points", [])
    total = len(evaluation_points) or 3
    matched = _match_key_points(user_answer, evaluation_points)
    return {
        "matched_points": matched,
        "total_points": total,
        "score": round(matched / total, 2) if total > 0 else 0.0,
        "is_correct": matched >= total * 0.6 if total > 0 else False,
        "feedback": _build_feedback(matched, total, evaluation_points),
    }


def grade_practice(question: dict, user_answer: str) -> dict:
    return grade_theory(question, user_answer)


def grade_mc_single(question: dict, selected_option_id: str) -> dict:
    correct = question.get("answers", {}).get("correct_option_id", "")
    is_correct = selected_option_id == correct
    return {
        "matched_points": 1.0 if is_correct else 0.0,
        "total_points": 1.0,
        "score": 1.0 if is_correct else 0.0,
        "is_correct": is_correct,
        "feedback": question.get("answers", {}).get("explanation", "")
        if not is_correct
        else "Chính xác!",
    }


def grade_true_false(question: dict, user_answer: bool) -> dict:
    correct = question.get("answers", {}).get("correct_answer")
    is_correct = user_answer == correct
    return {
        "matched_points": 1.0 if is_correct else 0.0,
        "total_points": 1.0,
        "score": 1.0 if is_correct else 0.0,
        "is_correct": is_correct,
        "feedback": question.get("answers", {}).get("explanation", "")
        if not is_correct
        else "Chính xác!",
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
            "feedback": "",
        }

    matched = 0
    for i, user_val in enumerate(blank_answers):
        if i < len(accepted) and _fuzzy_match(user_val, accepted[i]):
            matched += 1

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

    passed = 0
    failed_details = []
    for tc in test_cases:
        if _run_test_case(user_code, tc):
            passed += 1
        else:
            failed_details.append(
                f"Input: {tc['input']} → Expected: {tc['expected_output']}"
            )

    total = len(test_cases)
    score = round(passed / total, 2) if total > 0 else 0
    feedback = f"Passed {passed}/{total} test cases."
    if failed_details:
        feedback += "\nFailed:" + "\n".join(f"  - {d}" for d in failed_details[:3])
    return {
        "matched_points": float(passed),
        "total_points": float(total),
        "score": score,
        "is_correct": score >= 0.75 if total > 0 else False,
        "feedback": feedback,
    }


def grade(question: dict, response: dict) -> dict:
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


# ── helpers ──────────────────────────────────────────────────────────


def _match_key_points(user_answer: str, evaluation_points: list[str]) -> int:
    matched = 0
    lower = user_answer.lower()
    for point in evaluation_points:
        keywords = [w.strip() for w in point.lower().split() if len(w.strip()) > 3]
        if not keywords:
            matched += 1
            continue
        if any(kw in lower for kw in keywords):
            matched += 1
    return matched


def _build_feedback(matched: int, total: int, evaluation_points: list[str]) -> str:
    if total == 0:
        return "Không có tiêu chí đánh giá."
    pct = matched / total
    if pct >= 0.8:
        return f"Tốt! Bạn đã đạt {matched}/{total} ý chính."
    elif pct >= 0.5:
        return f"Khá! Bạn đạt {matched}/{total} ý. Tham khảo: {'; '.join(evaluation_points[:2])}"
    else:
        return f"Cần cải thiện ({matched}/{total}). Gợi ý: {'; '.join(evaluation_points[:3])}"


def _fill_blank_feedback(
    accepted: list[list[str]], given: list[str], matched: int, total: int
) -> str:
    parts = []
    for i, (acc, giv) in enumerate(zip(accepted, given)):
        status = "✓" if _fuzzy_match(giv, acc) else "✗"
        parts.append(f"#{i + 1}: {status} bạn='{giv}' | đáp án={acc}")
    return f"Đúng {matched}/{total}.\n" + "\n".join(parts)


def _fuzzy_match(user_val: str, accepted_vals: list[str]) -> bool:
    if not user_val:
        return False
    cleaned = user_val.strip().lower()
    return any(cleaned == a.strip().lower() for a in accepted_vals)


def _run_test_case(user_code: str, test_case: dict) -> bool:
    input_data = test_case.get("input", "")
    expected = test_case.get("expected_output", "")
    try:
        local_env = {}
        exec(user_code, {}, local_env)
        func_name = _find_function_name(user_code)
        if func_name and func_name in local_env:
            result = local_env[func_name](input_data)
            return str(result) == str(expected)
        return False
    except Exception:
        return False


def _find_function_name(code: str) -> Optional[str]:
    import re

    match = re.search(r"def\s+(\w+)\s*\(", code)
    return match.group(1) if match else None


def map_tags_to_groups(skill_tags: list[str], taxonomy: dict) -> list[str]:
    groups = set()
    for group_code, group_data in taxonomy.items():
        if isinstance(group_data, dict):
            tags = group_data.get("tags", [])
            if any(t in tags for t in skill_tags):
                groups.add(group_code)
    return sorted(groups)


def calculate_group_delta(score: float, difficulty_score: int) -> float:
    mapping = {
        1: (0.1, 0.3),
        2: (0.15, 0.4),
        3: (0.2, 0.5),
        4: (0.25, 0.6),
        5: (0.3, 0.7),
        6: (0.35, 0.8),
        7: (0.4, 0.9),
        8: (0.5, 1.0),
        9: (0.6, 1.2),
        10: (0.7, 1.5),
    }
    min_d, max_d = mapping.get(difficulty_score, (0.1, 0.3))
    if score >= 0.8:
        return min_d + (max_d - min_d) * (score - 0.8) / 0.2
    elif score < 0.4:
        return -(min_d + (0.4 - score) / 0.4 * min_d)
    else:
        return (score - 0.5) * min_d


def update_skill_vector(
    skill_vector: dict,
    question: dict,
    score: float,
    taxonomy: Optional[dict] = None,
) -> dict:
    delta = calculate_group_delta(score, question.get("difficulty_score", 5))
    for group in question.get("skill_groups", []):
        if group in skill_vector:
            skill_vector[group] = max(0, min(5, skill_vector[group] + delta))
    return skill_vector


def _new_tag_entry(score: float, is_correct: bool) -> dict:
    return {
        "attempted": 1,
        "correct": 1 if is_correct else 0,
        "avg_score": round(score, 2),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


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
            tag_stats[tag] = _new_tag_entry(score, is_correct)
            continue

        old_attempted = entry["attempted"]
        entry["attempted"] += 1
        if is_correct:
            entry["correct"] += 1
        entry["avg_score"] = round(
            (entry["avg_score"] * old_attempted + score) / entry["attempted"], 2
        )
        entry["last_updated"] = now
    return tag_stats
