"""
Recommendation Engine — điều phối recommender + KT predictor để sinh câu hỏi tiếp theo.

Pipeline:
    1. Gọi KTPredictor.predict_skill(history) → skill estimate từ DKT
    2. Nếu KT không sẵn (history ngắn / model lỗi) → dùng skill_vector EMA
    3. recommend_questions() với skill estimate

Functions:
    get_next_questions()      → câu tiếp theo trong session luyện tập
    get_weak_kc_practice()    → ôn KC yếu
    get_challenge_questions() → thử thách KC mạnh
    get_session_summary()     → tóm tắt tiến độ
"""

from __future__ import annotations

from src.kt.recommender import recommend_questions, adaptive_difficulty
from src.kt.competency_engine import (
    identify_weak_kcs,
    identify_strong_kcs,
    overall_score,
    get_role_kcs,
)
from src.data.data_loader import get_questions


# ── KT predictor (lazy import để tránh lỗi khi torch chưa cài) ───────────────

def _kt_predict(user_profile: dict) -> dict[str, float]:
    """
    Gọi KT predictor. Trả về {} nếu không khả dụng.
    Kết quả được merge với EMA: KT(70%) + EMA(30%) nếu có đủ history.
    """
    try:
        from src.kt.kt_predictor import predict_skill
        history = user_profile.get("history", [])
        role    = user_profile.get("role", "DA")
        kt_sv   = predict_skill(history, role)
        if not kt_sv:
            return {}

        # Blend với EMA skill_vector
        ema_sv = user_profile.get("skill_vector", {})
        blended = {}
        for kc, kt_val in kt_sv.items():
            ema_val = float(ema_sv.get(kc, kt_val))
            blended[kc] = round(kt_val * 0.7 + ema_val * 0.3, 4)
        return blended

    except Exception:
        return {}


def _get_skill_vector(user_profile: dict) -> dict[str, float]:
    """
    Lấy skill vector tốt nhất: KT prediction (nếu có) hoặc EMA fallback.
    """
    kt_sv = _kt_predict(user_profile)
    if kt_sv:
        # Điền KC thiếu từ EMA (KT chỉ trả về KC thuộc role)
        ema_sv = user_profile.get("skill_vector", {})
        merged = dict(ema_sv)
        merged.update(kt_sv)
        return merged
    return user_profile.get("skill_vector", {})


# ── Public API ─────────────────────────────────────────────────────────────────

def get_next_questions(
    user_profile: dict,
    n: int = 3,
    exclude_ids: set[str] | None = None,
) -> list[dict]:
    """
    Sinh n câu hỏi tiếp theo dựa trên KT skill estimate.

    Args:
        user_profile: dict từ user_manager (skill_vector, history, role, level)
        n           : số câu
        exclude_ids : set question_id đã làm

    Returns: list câu hỏi sắp xếp theo relevance.
    """
    role        = user_profile.get("role", "DA")
    exclude_ids = exclude_ids or set()
    skill_vector = _get_skill_vector(user_profile)

    question_bank = get_questions(role=role)
    focus_weak    = overall_score(skill_vector) < 0.6

    return recommend_questions(
        skill_vector        = skill_vector,
        question_bank       = question_bank,
        num_recommendations = n,
        focus_weak          = focus_weak,
        exclude_ids         = exclude_ids,
    )


def get_weak_kc_practice(
    user_profile: dict,
    n: int = 5,
    exclude_ids: set[str] | None = None,
) -> list[dict]:
    """Câu hỏi EASY/MEDIUM cho KC yếu nhất."""
    role         = user_profile.get("role", "DA")
    exclude_ids  = exclude_ids or set()
    skill_vector = _get_skill_vector(user_profile)

    weak_kcs = identify_weak_kcs(skill_vector, top_n=3)
    if not weak_kcs:
        return get_next_questions(user_profile, n=n, exclude_ids=exclude_ids)

    pool: list[dict] = []
    for diff in ("EASY", "MEDIUM"):
        pool += get_questions(role=role, difficulty_label=diff)

    return recommend_questions(
        skill_vector        = skill_vector,
        question_bank       = pool,
        num_recommendations = n,
        focus_weak          = True,
        exclude_ids         = exclude_ids,
    )


def get_challenge_questions(
    user_profile: dict,
    n: int = 3,
    exclude_ids: set[str] | None = None,
) -> list[dict]:
    """Câu HARD để thử thách KC mạnh."""
    role         = user_profile.get("role", "DA")
    exclude_ids  = exclude_ids or set()
    skill_vector = _get_skill_vector(user_profile)

    pool = get_questions(role=role, difficulty_label="HARD")

    return recommend_questions(
        skill_vector        = skill_vector,
        question_bank       = pool,
        num_recommendations = n,
        focus_weak          = False,
        exclude_ids         = exclude_ids,
    )


def get_session_summary(
    user_profile: dict,
    session_history: list[dict],
) -> dict:
    """
    Tóm tắt tiến độ session.

    Args:
        user_profile    : dict từ user_manager
        session_history : list {question_id, kc, score, is_correct} trong session

    Returns dict với total, correct, accuracy, weak_kcs, strong_kcs, overall_score,
    recommended_focus, next_difficulty, skill_source.
    """
    skill_vector = _get_skill_vector(user_profile)
    skill_source = "kt" if _kt_predict(user_profile) else "ema"

    total   = len(session_history)
    correct = sum(1 for r in session_history if r.get("is_correct", False))
    accuracy = round(correct / total, 4) if total > 0 else 0.0

    weak_kcs   = identify_weak_kcs(skill_vector, top_n=3)
    strong_kcs = identify_strong_kcs(skill_vector, top_n=3)
    ov_score   = overall_score(skill_vector)

    if weak_kcs:
        recommended_focus = f"Ôn lại: {', '.join(weak_kcs[:2])}"
    elif strong_kcs:
        recommended_focus = f"Thử thách: {', '.join(strong_kcs[:2])}"
    else:
        recommended_focus = "Tiếp tục luyện tập đều các KC."

    weakest_kc = weak_kcs[0] if weak_kcs else None
    next_diff  = adaptive_difficulty(skill_vector.get(weakest_kc, 0.5)) if weakest_kc else "MEDIUM"

    return {
        "total_answered"    : total,
        "correct"           : correct,
        "accuracy"          : accuracy,
        "weak_kcs"          : weak_kcs,
        "strong_kcs"        : strong_kcs,
        "overall_score"     : ov_score,
        "recommended_focus" : recommended_focus,
        "next_difficulty"   : next_diff,
        "skill_source"      : skill_source,
    }
