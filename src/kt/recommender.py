"""
Adaptive recommender for interview questions.

Sử dụng KC taxonomy UPPERCASE khớp với competency_engine.py.
Scoring: 65% weak-skill priority + 30% difficulty fit (khi focus_weak=True).
"""

from __future__ import annotations
import random
import numpy as np

from src.kt.competency_engine import (
    ROLE_COMPETENCIES,
    SKILL_GROUP_TO_KC,
    _BEGINNER_THRESH,
    _ADVANCED_THRESH,
)

DIFFICULTY_LABEL_TO_SCORE: dict[str, float] = {
    "EASY":   2.5,
    "MEDIUM": 5.0,
    "HARD":   7.5,
}

_NORM_DIFFICULTY: dict[str, float] = {
    **DIFFICULTY_LABEL_TO_SCORE,
    "easy": 2.5, "medium": 5.0, "hard": 7.5, "expert": 9.0,
}

TAG_COMPETENCY_HINTS: dict[str, list[str]] = {
    "SQL_DATABASE":               ["SQL_", "DATABASE", "DB_", "DAX_"],
    "BI_VISUALIZATION":           ["BI_", "VISUALIZATION", "POWER_BI", "TABLEAU", "DATA_MODELING"],
    "STATISTICS_EXPERIMENTATION": ["STAT_", "AB_TESTING", "HYPOTHESIS", "CONFIDENCE_INTERVAL"],
    "ANALYTICS_BUSINESS":         ["ANALYTICS_", "BUSINESS", "COHORT", "RFM", "FUNNEL"],
    "PYTHON_ANALYTICS":           ["PYTHON_", "PANDAS", "LANG_PYTHON"],
    "ALGORITHM_THEORY":           ["ML_SUPERVISED", "ML_UNSUPERVISED", "ML_ENSEMBLE",
                                   "ML_CLUSTERING", "ML_RECOMMENDER", "ALGORITHM_"],
    "EVALUATION_METRICS":         ["EVALUATION_", "EVAL_", "METRIC_", "ROC_AUC", "F1_SCORE",
                                   "CROSS_VALIDATION"],
    "DATA_PREPROCESSING":         ["DATA_PREPROCESSING", "DATA_CLEANING", "FEATURE_ENGINEERING"],
    "DEEP_LEARNING":              ["DL_", "DEEP_LEARNING"],
    "NLP":                        ["NLP_", "NLP"],
    "TIME_SERIES":                ["TIME_SERIES", "ML_TIME_SERIES"],
    "MLOPS":                      ["MLOPS", "ML_MLOPS", "ML_MONITORING", "MONITORING_"],
    "DATA_PIPELINE":              ["PIPE_", "PIPELINE", "ETL", "ELT", "CDC", "ORCHESTRATION"],
    "DATA_ARCHITECTURE_MODELING": ["DATA_ARCHITECTURE", "ARCH_DATA", "DATA_WAREHOUSE", "DATA_LAKE"],
    "BIG_DATA_CLOUD_TOOLS":       ["BIG_DATA", "SPARK", "KAFKA", "CLOUD_", "TOOL_SPARK",
                                   "TOOL_KAFKA", "TOOL_AIRFLOW"],
    "DATABASE_INTERNALS":         ["DATABASE_INDEXING", "DATABASE_SCALING", "DATABASE_INTERNALS"],
    "SYSTEM_ARCHITECTURE":        ["ARCH_SYSTEM", "SYSTEM_ARCHITECTURE", "SYSTEM_DESIGN"],
}

ROLE_DEFAULT_KC: dict[str, str] = {
    "DA": "SQL_DATABASE",
    "DS": "ALGORITHM_THEORY",
    "DE": "DATA_PIPELINE",
}


# ── Internal helpers ───────────────────────────────────────────────────────────

def _question_kc(question: dict) -> str | None:
    for sg in question.get("skill_groups", []):
        kc = SKILL_GROUP_TO_KC.get(str(sg).upper())
        if kc:
            return kc
    tags = [str(t).upper() for t in question.get("skill_tags", [])]
    tag_text = " ".join(tags)
    for kc, hints in TAG_COMPETENCY_HINTS.items():
        if any(h in tag_text for h in hints):
            return kc
    primary = str(question.get("roles", {}).get("primary", "")).upper()
    return ROLE_DEFAULT_KC.get(primary)


def _difficulty_score(question: dict) -> float:
    ds = question.get("difficulty_score")
    if ds is not None:
        return float(np.clip(float(ds), 1.0, 10.0))
    label = str(question.get("difficulty_label", "MEDIUM")).upper()
    return _NORM_DIFFICULTY.get(label, 5.0)


def adaptive_difficulty(skill_value: float, streak: int = 0) -> str:
    """
    Chọn độ khó tiếp theo từ skill hiện tại (0–1).
    Returns: "EASY" / "MEDIUM" / "HARD"
    """
    score = float(np.clip(skill_value * 10.0, 0.0, 10.0))
    if streak >= 3:
        score += 1.0
    elif streak <= -2:
        score -= 1.0
    if score < 4.0:
        return "EASY"
    if score < 7.0:
        return "MEDIUM"
    return "HARD"


# ── Public API ─────────────────────────────────────────────────────────────────

def recommend_questions(
    skill_vector: dict[str, float],
    question_bank: list[dict],
    num_recommendations: int = 5,
    focus_weak: bool = True,
    exclude_ids: set[str] | None = None,
) -> list[dict]:
    """
    Recommend câu hỏi từ skill_vector (dict KC → [0,1]).

    Scoring (focus_weak=True):
        65% weak-skill priority + 30% difficulty fit + 5% coverage bonus
    Scoring (focus_weak=False):
        45% readiness + 45% difficulty fit + 10% coverage bonus

    Returns: list câu hỏi đã được sắp xếp theo score giảm dần.
    """
    exclude_ids = exclude_ids or set()
    candidates = [
        q for q in question_bank
        if q.get("question_id") not in exclude_ids
    ]
    if not candidates:
        return []

    scored: list[tuple[float, dict]] = []
    weak_kcs = {kc for kc, v in skill_vector.items() if v < _BEGINNER_THRESH}
    strong_kcs = {kc for kc, v in skill_vector.items() if v > _ADVANCED_THRESH}

    for q in candidates:
        kc = _question_kc(q)
        skill_val = skill_vector.get(kc, 0.5) if kc else 0.5
        diff_score = _difficulty_score(q)

        # Target difficulty dựa trên skill
        target_diff = skill_val * 10.0
        # Difficulty fit: gần target → điểm cao
        diff_fit = 1.0 - abs(diff_score - target_diff) / 10.0

        if focus_weak:
            # Weak-skill priority: KC yếu → điểm cao
            weakness = max(0.0, _BEGINNER_THRESH - skill_val) / _BEGINNER_THRESH if kc else 0.0
            coverage = 1.0 if (kc and kc not in strong_kcs) else 0.3
            score = weakness * 0.65 + diff_fit * 0.30 + coverage * 0.05
        else:
            # Readiness: skill gần 0.5 → phù hợp nhất
            readiness = 1.0 - abs(skill_val - 0.5) * 2.0
            coverage = 1.0 if kc else 0.5
            score = readiness * 0.45 + diff_fit * 0.45 + coverage * 0.10

        scored.append((score, q))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [q for _, q in scored[:num_recommendations]]


def get_recommended_difficulty(skill_vector: dict[str, float], kc: str) -> str:
    """Trả về difficulty khuyến nghị cho KC cụ thể."""
    skill = skill_vector.get(kc, 0.5)
    return adaptive_difficulty(skill)
