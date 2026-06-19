"""Competency Engine - KC taxonomy + skill vector management."""
from __future__ import annotations
import numpy as np
from typing import Optional

ROLE_COMPETENCIES: dict[str, list[str]] = {
    "DA": ["SQL_DATABASE","BI_VISUALIZATION","STATISTICS_EXPERIMENTATION","ANALYTICS_BUSINESS","PYTHON_ANALYTICS"],
    "DS": ["ALGORITHM_THEORY","EVALUATION_METRICS","DATA_PREPROCESSING","DEEP_LEARNING","NLP","TIME_SERIES","MLOPS"],
    "DE": ["DATA_PIPELINE","DATA_ARCHITECTURE_MODELING","BIG_DATA_CLOUD_TOOLS","DATABASE_INTERNALS","SYSTEM_ARCHITECTURE"],
}

SKILL_GROUP_TO_KC: dict[str, str] = {
    "SQL_DATABASE": "SQL_DATABASE",
    "SQL_FUNDAMENTALS": "SQL_DATABASE",
    "SQL_WINDOW_FUNCTION": "SQL_DATABASE",
    "SQL_JOIN": "SQL_DATABASE",
    "SQL_AGGREGATION": "SQL_DATABASE",
    "SQL_PERFORMANCE": "SQL_DATABASE",
    "SQL_CTE": "SQL_DATABASE",
    "DATABASE_DESIGN": "SQL_DATABASE",
    "BI_VISUALIZATION": "BI_VISUALIZATION",
    "TOOL_POWER_BI": "BI_VISUALIZATION",
    "TOOL_TABLEAU": "BI_VISUALIZATION",
    "DATA_VISUALIZATION": "BI_VISUALIZATION",
    "DATA_MODELING": "BI_VISUALIZATION",
    "DAX_FUNDAMENTALS": "BI_VISUALIZATION",
    "STATISTICS_EXPERIMENTATION": "STATISTICS_EXPERIMENTATION",
    "STAT_AB_TESTING": "STATISTICS_EXPERIMENTATION",
    "STAT_FUNDAMENTALS": "STATISTICS_EXPERIMENTATION",
    "STAT_HYPOTHESIS_TESTING": "STATISTICS_EXPERIMENTATION",
    "ANALYTICS_BUSINESS": "ANALYTICS_BUSINESS",
    "ANALYTICS_COHORT": "ANALYTICS_BUSINESS",
    "ANALYTICS_FUNNEL": "ANALYTICS_BUSINESS",
    "ANALYTICS_RFM": "ANALYTICS_BUSINESS",
    "PYTHON_ANALYTICS": "PYTHON_ANALYTICS",
    "PYTHON_PANDAS": "PYTHON_ANALYTICS",
    "LANG_PYTHON": "PYTHON_ANALYTICS",
    "ALGORITHM_THEORY": "ALGORITHM_THEORY",
    "ML_SUPERVISED": "ALGORITHM_THEORY",
    "ML_UNSUPERVISED": "ALGORITHM_THEORY",
    "ML_ENSEMBLE": "ALGORITHM_THEORY",
    "ML_CLUSTERING": "ALGORITHM_THEORY",
    "ML_RECOMMENDER_SYSTEM": "ALGORITHM_THEORY",
    "ML_FUNDAMENTALS": "ALGORITHM_THEORY",
    "ML_CLASSIFICATION": "ALGORITHM_THEORY",
    "ML_REGRESSION": "ALGORITHM_THEORY",
    "EVALUATION_METRICS": "EVALUATION_METRICS",
    "EVAL_CROSS_VALIDATION": "EVALUATION_METRICS",
    "METRIC_ROC_AUC": "EVALUATION_METRICS",
    "METRIC_F1_SCORE": "EVALUATION_METRICS",
    "DATA_PREPROCESSING": "DATA_PREPROCESSING",
    "DATA_CLEANING": "DATA_PREPROCESSING",
    "FEATURE_ENGINEERING": "DATA_PREPROCESSING",
    "DEEP_LEARNING": "DEEP_LEARNING",
    "DL_TRAINING": "DEEP_LEARNING",
    "DL_CNN": "DEEP_LEARNING",
    "DL_FUNDAMENTALS": "DEEP_LEARNING",
    "DL_RNN": "DEEP_LEARNING",
    "DL_TRANSFORMER": "DEEP_LEARNING",
    "NLP": "NLP",
    "NLP_PREPROCESSING": "NLP",
    "NLP_FUNDAMENTALS": "NLP",
    "NLP_CLASSIFICATION": "NLP",
    "TIME_SERIES": "TIME_SERIES",
    "ML_TIME_SERIES": "TIME_SERIES",
    "MLOPS": "MLOPS",
    "ML_MLOPS": "MLOPS",
    "ML_MONITORING": "MLOPS",
    "DATA_PIPELINE": "DATA_PIPELINE",
    "PIPE_ETL": "DATA_PIPELINE",
    "PIPE_ELT": "DATA_PIPELINE",
    "PIPE_CDC": "DATA_PIPELINE",
    "PIPE_ORCHESTRATION": "DATA_PIPELINE",
    "DATA_ARCHITECTURE_MODELING": "DATA_ARCHITECTURE_MODELING",
    "ARCH_DATA_ARCHITECTURE": "DATA_ARCHITECTURE_MODELING",
    "DATA_WAREHOUSE": "DATA_ARCHITECTURE_MODELING",
    "DATA_LAKE": "DATA_ARCHITECTURE_MODELING",
    "DWH_ARCHITECTURE": "DATA_ARCHITECTURE_MODELING",
    "BIG_DATA_CLOUD_TOOLS": "BIG_DATA_CLOUD_TOOLS",
    "TOOL_SPARK": "BIG_DATA_CLOUD_TOOLS",
    "TOOL_KAFKA": "BIG_DATA_CLOUD_TOOLS",
    "TOOL_AIRFLOW": "BIG_DATA_CLOUD_TOOLS",
    "CLOUD_AWS": "BIG_DATA_CLOUD_TOOLS",
    "CLOUD_DW": "BIG_DATA_CLOUD_TOOLS",
    "BIG_DATA": "BIG_DATA_CLOUD_TOOLS",
    "STREAMING": "BIG_DATA_CLOUD_TOOLS",
    "DISTRIBUTED_DB": "DATABASE_INTERNALS",
    "DATABASE_INTERNALS": "DATABASE_INTERNALS",
    "DATABASE_INDEXING": "DATABASE_INTERNALS",
    "DATABASE_SCALING": "DATABASE_INTERNALS",
    "NOSQL": "DATABASE_INTERNALS",
    "SYSTEM_ARCHITECTURE": "SYSTEM_ARCHITECTURE",
    "ARCH_SYSTEM_DESIGN": "SYSTEM_ARCHITECTURE",
    "SYSTEM_DESIGN": "SYSTEM_ARCHITECTURE",
}

_MIN_SKILL = 0.05
_MAX_SKILL = 0.99
_LEARNING_RATE = 0.08
_FORGETTING_RATE = 0.002
_BEGINNER_THRESH = 0.40
_ADVANCED_THRESH = 0.70


def get_role_kcs(role: str) -> list[str]:
    return ROLE_COMPETENCIES.get(role.upper(), [])


def question_to_kc(question: dict, role: str) -> str:
    for sg in question.get("skill_groups", []):
        kc = SKILL_GROUP_TO_KC.get(str(sg).upper())
        if kc:
            return kc
    kcs = get_role_kcs(role)
    return kcs[0] if kcs else "UNKNOWN"


def init_skill_vector(role: str, default_skill: float = 0.5) -> dict[str, float]:
    return {
        kc: round(float(np.clip(default_skill, _MIN_SKILL, _MAX_SKILL)), 4)
        for kc in get_role_kcs(role)
    }


def update_skill_after_answer(
    skill_vector: dict[str, float],
    kc: str,
    grade_score: float,
) -> dict[str, float]:
    sv = dict(skill_vector)
    if kc not in sv:
        return sv
    current = sv[kc]
    if grade_score >= 6.0:
        sv[kc] = current + _LEARNING_RATE * (1.0 - current)
    else:
        sv[kc] = current - _FORGETTING_RATE * current
    sv[kc] = round(float(np.clip(sv[kc], _MIN_SKILL, _MAX_SKILL)), 4)
    return sv


def compute_skill_from_assessment(
    role: str,
    stage1_results: list[dict],
    stage2_results: list[dict],
) -> dict[str, float]:
    kcs = get_role_kcs(role)
    buckets: dict[str, list[tuple[float, float]]] = {kc: [] for kc in kcs}
    for r in stage1_results:
        kc = r.get("kc", "")
        if kc in buckets:
            buckets[kc].append((r.get("score", 0.0) / 10.0, 0.4))
    for r in stage2_results:
        kc = r.get("kc", "")
        if kc in buckets:
            buckets[kc].append((r.get("score", 0.0) / 10.0, 0.6))
    sv: dict[str, float] = {}
    for kc in kcs:
        entries = buckets[kc]
        if not entries:
            sv[kc] = 0.5
        else:
            total_w = sum(w for _, w in entries)
            sv[kc] = round(float(np.clip(
                sum(s * w for s, w in entries) / total_w,
                _MIN_SKILL, _MAX_SKILL
            )), 4)
    return sv


def classify_level(stage1_score: float, stage2_score: float, stage2_is_hard: bool) -> str:
    s1_pass = stage1_score >= 0.5
    s2_pass = stage2_score >= 0.5
    if s1_pass:
        return "advanced" if s2_pass else "intermediate"
    return "intermediate" if s2_pass else "beginner"


def identify_weak_kcs(
    skill_vector: dict[str, float],
    threshold: float = _BEGINNER_THRESH,
    top_n: Optional[int] = None,
) -> list[str]:
    weak = sorted(
        [(kc, v) for kc, v in skill_vector.items() if v < threshold],
        key=lambda x: x[1]
    )
    result = [kc for kc, _ in weak]
    return result[:top_n] if top_n else result


def identify_strong_kcs(
    skill_vector: dict[str, float],
    threshold: float = _ADVANCED_THRESH,
    top_n: Optional[int] = None,
) -> list[str]:
    strong = sorted(
        [(kc, v) for kc, v in skill_vector.items() if v > threshold],
        key=lambda x: x[1], reverse=True
    )
    result = [kc for kc, _ in strong]
    return result[:top_n] if top_n else result


def overall_score(skill_vector: dict[str, float]) -> float:
    if not skill_vector:
        return 0.0
    return round(float(np.mean(list(skill_vector.values()))), 4)
