"""
Test Generator — sinh bộ câu hỏi Mock Interview và Entry Test.

Mock Interview blueprint (~15 câu):
  EASY   : 2 câu (MC_SINGLE, TRUE_FALSE) — warm-up
  MEDIUM : 8 câu (MC_SINGLE, THEORY, PRACTICE) — core skills
  HARD   : 5 câu (THEORY, PRACTICE, CODING) — challenge
"""

from __future__ import annotations

import random
from typing import Optional

from src.data.data_loader import get_questions
from src.kt.competency_engine import ROLE_COMPETENCIES, question_to_kc

# ── Config ─────────────────────────────────────────────────────────────────────

DEFAULT_BLUEPRINT: dict[str, dict] = {
    "EASY":   {"n": 2, "types": ["MC_SINGLE", "TRUE_FALSE"]},
    "MEDIUM": {"n": 8, "types": ["MC_SINGLE", "THEORY", "PRACTICE"]},
    "HARD":   {"n": 5, "types": ["THEORY", "PRACTICE", "CODING"]},
}

# Điều chỉnh theo level người dùng
_LEVEL_ADJUSTMENTS: dict[str, dict] = {
    "beginner":     {"EASY": 4, "MEDIUM": 8, "HARD": 2},
    "intermediate": {"EASY": 2, "MEDIUM": 8, "HARD": 5},
    "advanced":     {"EASY": 1, "MEDIUM": 7, "HARD": 7},
}


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_mock_interview(
    role: str,
    user_level: str = "intermediate",
    blueprint: Optional[dict] = None,
    exclude_ids: Optional[set[str]] = None,
    seed: Optional[int] = None,
) -> list[dict]:
    """
    Sinh bộ câu hỏi mock interview ~15 câu theo blueprint.

    Args:
        role       : DA / DS / DE
        user_level : beginner / intermediate / advanced
        blueprint  : override DEFAULT_BLUEPRINT nếu cần
        exclude_ids: set question_id đã làm trước đó
        seed       : random seed để reproduce

    Returns:
        List câu hỏi đã được thêm field 'stage' và 'session_order'.
    """
    if seed is not None:
        random.seed(seed)

    role = role.upper()
    exclude_ids = exclude_ids or set()
    bp = _adjust_blueprint(blueprint or DEFAULT_BLUEPRINT, user_level)

    all_questions = get_questions(role=role)
    result: list[dict] = []
    used_ids = set(exclude_ids)
    order = 1

    for difficulty in ["EASY", "MEDIUM", "HARD"]:
        cfg = bp.get(difficulty, {})
        n = cfg.get("n", 0)
        allowed_types = cfg.get("types", [])

        pool = [
            q for q in all_questions
            if q.get("question_id") not in used_ids
            and str(q.get("difficulty_label", "")).upper() == difficulty
            and (not allowed_types or q.get("question_type") in allowed_types)
        ]
        random.shuffle(pool)

        for q in pool[:n]:
            enriched = dict(q)
            enriched["session_difficulty"] = difficulty
            enriched["session_order"] = order
            result.append(enriched)
            used_ids.add(q["question_id"])
            order += 1

    return result


def generate_entry_test(
    role: str,
    n: int = 10,
    exclude_ids: Optional[set[str]] = None,
    seed: Optional[int] = None,
) -> list[dict]:
    """
    Sinh bài test đầu vào nhanh — toàn MEDIUM, phủ đủ KC.

    Returns list câu hỏi đã thêm 'session_order'.
    """
    if seed is not None:
        random.seed(seed)

    role = role.upper()
    exclude_ids = exclude_ids or set()
    kcs = ROLE_COMPETENCIES.get(role, [])
    all_questions = get_questions(role=role)

    pool_medium = [
        q for q in all_questions
        if str(q.get("difficulty_label", "")).upper() == "MEDIUM"
        and q.get("question_id") not in exclude_ids
    ]

    # Ưu tiên lấy 1 câu mỗi KC
    result: list[dict] = []
    used_ids = set(exclude_ids)
    kc_buckets: dict[str, list[dict]] = {kc: [] for kc in kcs}
    for q in pool_medium:
        kc = question_to_kc(q, role)
        if kc in kc_buckets:
            kc_buckets[kc].append(q)

    for kc in kcs:
        if len(result) >= n:
            break
        bucket = [q for q in kc_buckets[kc] if q["question_id"] not in used_ids]
        if bucket:
            q = random.choice(bucket)
            result.append(q)
            used_ids.add(q["question_id"])

    # Điền thêm nếu chưa đủ n
    remaining = [q for q in pool_medium if q["question_id"] not in used_ids]
    random.shuffle(remaining)
    for q in remaining:
        if len(result) >= n:
            break
        result.append(q)
        used_ids.add(q["question_id"])

    return [dict(q, session_order=i + 1) for i, q in enumerate(result)]


# ── Internal helpers ───────────────────────────────────────────────────────────

def _adjust_blueprint(blueprint: dict, user_level: str) -> dict:
    """
    Điều chỉnh số lượng câu theo level.
    Giữ types của blueprint gốc, chỉ override n.
    """
    level_counts = _LEVEL_ADJUSTMENTS.get(user_level.lower(), _LEVEL_ADJUSTMENTS["intermediate"])
    adjusted = {}
    for diff, cfg in blueprint.items():
        adjusted[diff] = {
            "n": level_counts.get(diff, cfg.get("n", 0)),
            "types": cfg.get("types", []),
        }
    return adjusted
