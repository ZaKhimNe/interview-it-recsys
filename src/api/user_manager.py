"""
User Manager — load/save profile, cập nhật skill vector sau mỗi câu trả lời.

Skill update pipeline:
    1. EMA update (update_skill_after_answer) — luôn chạy
    2. KT prediction (kt_predictor.predict_skill) — chạy nếu model sẵn sàng + đủ history
    3. Blend: KT(70%) + EMA(30%) → ghi vào skill_vector
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.kt.competency_engine import (
    init_skill_vector,
    update_skill_after_answer,
    classify_level,
    identify_weak_kcs,
    identify_strong_kcs,
    overall_score,
    question_to_kc,
)

_BASE_DIR     = Path(__file__).resolve().parents[2]
_PROFILES_DIR = _BASE_DIR / "data" / "users"
_cache: dict[str, dict] = {}

# Số lượng history tối thiểu để kích hoạt KT update
_KT_MIN_HISTORY = 3


def _profile_path(user_id: str) -> Path:
    return _PROFILES_DIR / f"{user_id}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    _PROFILES_DIR.mkdir(parents=True, exist_ok=True)


def _save_profile(profile: dict) -> None:
    _ensure_dir()
    with _profile_path(profile["user_id"]).open("w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


# ── KT skill update (lazy import) ─────────────────────────────────────────────

def _kt_update_skill(
    skill_vector: dict[str, float],
    history: list[dict],
    role: str,
) -> dict[str, float]:
    """
    Gọi KT predictor để blend skill_vector.
    Trả về skill_vector gốc nếu KT không khả dụng hoặc history quá ngắn.
    Blend: KT(70%) + EMA(30%).
    """
    if len(history) < _KT_MIN_HISTORY:
        return skill_vector
    try:
        from src.kt.kt_predictor import predict_skill
        kt_sv = predict_skill(history, role)
        if not kt_sv:
            return skill_vector
        blended = dict(skill_vector)
        for kc, kt_val in kt_sv.items():
            ema_val = float(skill_vector.get(kc, kt_val))
            blended[kc] = round(kt_val * 0.7 + ema_val * 0.3, 4)
        return blended
    except Exception:
        return skill_vector


# ── CRUD ───────────────────────────────────────────────────────────────────────

def create_user_profile(user_id: str, role: str) -> dict:
    _ensure_dir()
    if _profile_path(user_id).exists():
        return load_user_profile(user_id)
    role = role.upper()
    now = _now_iso()
    profile = {
        "user_id"              : user_id,
        "role"                 : role,
        "level"                : "beginner",
        "skill_vector"         : init_skill_vector(role),
        "history"              : [],
        "assessment_completed" : False,
        "total_answered"       : 0,
        "created_at"           : now,
        "updated_at"           : now,
    }
    _cache[user_id] = profile
    _save_profile(profile)
    return profile


def load_user_profile(user_id: str) -> Optional[dict]:
    if user_id in _cache:
        return _cache[user_id]
    path = _profile_path(user_id)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            profile = json.load(f)
        _cache[user_id] = profile
        return profile
    except (json.JSONDecodeError, OSError):
        return None


def get_user_profile(user_id: str) -> Optional[dict]:
    return load_user_profile(user_id)


# ── Skill update ───────────────────────────────────────────────────────────────

def update_after_answer(user_id: str, question: dict, grade_result: dict) -> dict:
    """
    Cập nhật skill_vector sau mỗi câu trả lời.

    Pipeline:
        1. EMA update (update_skill_after_answer)
        2. Ghi history entry
        3. KT blend nếu đủ history
    """
    profile = load_user_profile(user_id)
    if profile is None:
        raise ValueError(f"User '{user_id}' không tồn tại.")

    role  = profile["role"]
    kc    = question_to_kc(question, role)
    score = float(grade_result.get("score", 0.0))
    is_correct = bool(grade_result.get("is_correct", score >= 6.0))

    # 1. EMA update
    sv = update_skill_after_answer(profile["skill_vector"], kc, score)

    # 2. Ghi history
    history_entry = {
        "question_id" : question.get("question_id", ""),
        "kc"          : kc,
        "score"       : round(score, 2),
        "is_correct"  : is_correct,
        "timestamp"   : _now_iso(),
    }
    profile["history"].append(history_entry)
    profile["total_answered"] = profile.get("total_answered", 0) + 1

    # 3. KT blend (chạy sau khi đã append history)
    sv = _kt_update_skill(sv, profile["history"], role)

    profile["skill_vector"] = sv
    profile["updated_at"]   = _now_iso()
    _cache[user_id]         = profile
    _save_profile(profile)
    return profile


def update_from_assessment(
    user_id: str,
    role: str,
    stage1_score: float,
    stage2_score: float,
    stage2_is_hard: bool,
    new_skill_vector: dict[str, float],
) -> dict:
    profile = load_user_profile(user_id) or create_user_profile(user_id, role)

    # KT blend trên skill_vector từ assessment
    sv = _kt_update_skill(new_skill_vector, profile.get("history", []), role)

    profile["level"]                 = classify_level(stage1_score, stage2_score, stage2_is_hard)
    profile["skill_vector"]          = sv
    profile["assessment_completed"]  = True
    profile["updated_at"]            = _now_iso()
    _cache[user_id]  = profile
    _save_profile(profile)
    return profile


# ── Read helpers ───────────────────────────────────────────────────────────────

def get_answered_question_ids(user_id: str) -> set[str]:
    profile = load_user_profile(user_id)
    if not profile:
        return set()
    return {e["question_id"] for e in profile.get("history", [])}


def get_user_summary(user_id: str) -> dict:
    profile = load_user_profile(user_id)
    if not profile:
        return {"error": f"User '{user_id}' không tồn tại."}
    sv = profile.get("skill_vector", {})
    return {
        "user_id"              : user_id,
        "role"                 : profile.get("role"),
        "level"                : profile.get("level"),
        "overall_score"        : overall_score(sv),
        "weak_kcs"             : identify_weak_kcs(sv, top_n=3),
        "strong_kcs"           : identify_strong_kcs(sv, top_n=3),
        "total_answered"       : profile.get("total_answered", 0),
        "assessment_completed" : profile.get("assessment_completed", False),
    }


def list_users() -> list[str]:
    _ensure_dir()
    return [p.stem for p in _PROFILES_DIR.glob("*.json")]
