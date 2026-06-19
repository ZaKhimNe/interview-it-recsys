"""
Question Manager — 2-Stage Branching Assessment (GRE/SAT-style CAT).

Luồng:
  Stage 1  → MEDIUM, 1 câu/KC → ~10 câu (DA:5, DS:7, DE:5 KC)
  score_stage1() → routing:
      < 50% đúng → Stage 2A (EASY, tập trung KC yếu)
      ≥ 50% đúng → Stage 2B (HARD, tập trung KC stage1)
  Stage 2A → EASY, 5 câu, ưu tiên KC yếu
  Stage 2B → HARD, 5 câu, ưu tiên KC đã test stage1
  classify_level() → beginner / intermediate / advanced
"""

from __future__ import annotations

import random
from typing import Optional

from src.data.data_loader import get_questions, load_question_bank
from src.kt.competency_engine import (
    ROLE_COMPETENCIES,
    SKILL_GROUP_TO_KC,
    question_to_kc,
    classify_level,
)

# ── Config ─────────────────────────────────────────────────────────────────────

_STAGE1_DIFFICULTY = "MEDIUM"
_STAGE2A_DIFFICULTY = "EASY"
_STAGE2B_DIFFICULTY = "HARD"

_STAGE2_N = 5          # số câu mỗi stage 2 track
_STAGE1_PASS_THRESH = 0.5   # tỉ lệ đúng để chuyển sang HARD track


# ── Internal helpers ───────────────────────────────────────────────────────────

def _get_pool(role: str, difficulty: str) -> list[dict]:
    """Load câu hỏi theo role + difficulty."""
    return get_questions(role=role, difficulty_label=difficulty)


def _pool_by_kc(pool: list[dict], role: str) -> dict[str, list[dict]]:
    """Phân loại pool theo KC."""
    buckets: dict[str, list[dict]] = {}
    for q in pool:
        kc = question_to_kc(q, role)
        buckets.setdefault(kc, []).append(q)
    return buckets


def _pick_one(pool: list[dict], exclude_ids: set[str]) -> Optional[dict]:
    """Chọn ngẫu nhiên 1 câu không nằm trong exclude_ids."""
    available = [q for q in pool if q.get("question_id") not in exclude_ids]
    return random.choice(available) if available else None


def _pick_n(
    pool: list[dict],
    n: int,
    exclude_ids: set[str],
    priority_kcs: list[str] | None = None,
    kc_buckets: dict[str, list[dict]] | None = None,
) -> list[dict]:
    """
    Chọn n câu từ pool, không trùng exclude_ids.
    Nếu có priority_kcs + kc_buckets: ưu tiên lấy từ KC yếu trước.
    """
    selected: list[dict] = []
    used_ids: set[str] = set(exclude_ids)

    # Ưu tiên KC yếu
    if priority_kcs and kc_buckets:
        for kc in priority_kcs:
            if len(selected) >= n:
                break
            candidates = [q for q in kc_buckets.get(kc, []) if q.get("question_id") not in used_ids]
            if candidates:
                q = random.choice(candidates)
                selected.append(q)
                used_ids.add(q["question_id"])

    # Điền phần còn lại ngẫu nhiên
    remaining = [q for q in pool if q.get("question_id") not in used_ids]
    random.shuffle(remaining)
    for q in remaining:
        if len(selected) >= n:
            break
        selected.append(q)
        used_ids.add(q["question_id"])

    return selected


# ── Stage 1 ────────────────────────────────────────────────────────────────────

def generate_stage1(role: str, exclude_ids: set[str] | None = None) -> list[dict]:
    """
    Sinh bộ câu hỏi Stage 1: MEDIUM, 1 câu/KC.

    Returns list câu hỏi đã được thêm field 'stage' và 'kc'.
    """
    exclude_ids = exclude_ids or set()
    role = role.upper()
    kcs = ROLE_COMPETENCIES.get(role, [])
    pool = _get_pool(role, _STAGE1_DIFFICULTY)
    kc_buckets = _pool_by_kc(pool, role)

    questions: list[dict] = []
    used_ids = set(exclude_ids)

    for kc in kcs:
        q = _pick_one(kc_buckets.get(kc, []), used_ids)
        if q is None:
            # fallback: bất kỳ câu MEDIUM chưa dùng
            q = _pick_one(pool, used_ids)
        if q:
            enriched = dict(q)
            enriched["stage"] = 1
            enriched["kc"] = kc
            questions.append(enriched)
            used_ids.add(q["question_id"])

    return questions


def score_stage1(stage1_results: list[dict]) -> tuple[float, list[str]]:
    """
    Tính tỉ lệ đúng Stage 1 và list KC yếu (đúng = is_correct hoặc score ≥ 6).

    Args:
        stage1_results: List {question_id, kc, score (0–10), is_correct}

    Returns:
        (pass_ratio: float, weak_kcs: list[str])
    """
    if not stage1_results:
        return 0.0, []

    correct = sum(
        1 for r in stage1_results
        if r.get("is_correct", False) or float(r.get("score", 0)) >= 6.0
    )
    pass_ratio = correct / len(stage1_results)

    weak_kcs = [
        r["kc"] for r in stage1_results
        if not (r.get("is_correct", False) or float(r.get("score", 0)) >= 6.0)
        if r.get("kc")
    ]
    return round(pass_ratio, 4), weak_kcs


def route_stage2(stage1_pass_ratio: float) -> str:
    """
    Routing sang Stage 2A (EASY) hoặc 2B (HARD).
    Returns: "2A" hoặc "2B"
    """
    return "2B" if stage1_pass_ratio >= _STAGE1_PASS_THRESH else "2A"


# ── Stage 2 ────────────────────────────────────────────────────────────────────

def generate_stage2a(
    role: str,
    weak_kcs: list[str],
    exclude_ids: set[str] | None = None,
    n: int = _STAGE2_N,
) -> list[dict]:
    """Stage 2A: EASY, ưu tiên KC yếu từ stage 1."""
    exclude_ids = exclude_ids or set()
    role = role.upper()
    pool = _get_pool(role, _STAGE2A_DIFFICULTY)
    kc_buckets = _pool_by_kc(pool, role)
    priority = weak_kcs + [kc for kc in ROLE_COMPETENCIES.get(role, []) if kc not in weak_kcs]
    selected = _pick_n(pool, n, exclude_ids, priority_kcs=priority, kc_buckets=kc_buckets)
    return [dict(q, stage=2, track="2A", kc=question_to_kc(q, role)) for q in selected]


def generate_stage2b(
    role: str,
    stage1_kcs: list[str],
    exclude_ids: set[str] | None = None,
    n: int = _STAGE2_N,
) -> list[dict]:
    """Stage 2B: HARD, tập trung KC đã test ở stage 1."""
    exclude_ids = exclude_ids or set()
    role = role.upper()
    pool = _get_pool(role, _STAGE2B_DIFFICULTY)
    kc_buckets = _pool_by_kc(pool, role)
    priority = stage1_kcs + [kc for kc in ROLE_COMPETENCIES.get(role, []) if kc not in stage1_kcs]
    selected = _pick_n(pool, n, exclude_ids, priority_kcs=priority, kc_buckets=kc_buckets)
    return [dict(q, stage=2, track="2B", kc=question_to_kc(q, role)) for q in selected]


def finalize_assessment(
    role: str,
    stage1_results: list[dict],
    stage2_results: list[dict],
    stage2_is_hard: bool,
) -> dict:
    """
    Tổng hợp kết quả 2-stage assessment.

    Returns: {level, stage1_score, stage2_score, route, weak_kcs}
    """
    pass_ratio, weak_kcs = score_stage1(stage1_results)
    route = route_stage2(pass_ratio)

    if stage2_results:
        s2_correct = sum(
            1 for r in stage2_results
            if r.get("is_correct", False) or float(r.get("score", 0)) >= 6.0
        )
        stage2_score = round(s2_correct / len(stage2_results), 4)
    else:
        stage2_score = 0.0

    level = classify_level(pass_ratio, stage2_score, stage2_is_hard)

    return {
        "level": level,
        "stage1_score": pass_ratio,
        "stage2_score": stage2_score,
        "route": route,
        "weak_kcs": weak_kcs,
    }
