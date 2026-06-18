"""
Adaptive recommender for interview questions.

The recommender ranks questions from the current competency vector. It favors
weak skill areas by default and keeps the selected difficulty close to the
user's current level so the interview stays adaptive instead of random.
"""

import numpy as np


COMPETENCY_KEYS = [
    "sql",
    "analytics",
    "statistics",
    "visualization",
    "data_engineering",
    "big_data",
    "machine_learning",
    "deep_learning",
    "mlops",
    "programming",
]

TAG_COMPETENCY_HINTS = {
    "sql": ("SQL", "DATABASE", "DB_", "DAX"),
    "analytics": ("ANALYTICS", "BUSINESS", "COHORT", "RFM", "FUNNEL"),
    "statistics": ("STAT_", "AB_TESTING", "HYPOTHESIS", "CONFIDENCE"),
    "visualization": ("VISUALIZATION", "POWER_BI", "TABLEAU"),
    "data_engineering": ("PIPE_", "PIPELINE", "WAREHOUSE", "CDC", "AIRFLOW", "ORCHESTRATION"),
    "big_data": ("BIG_DATA", "SPARK", "KAFKA"),
    "machine_learning": ("ML_", "FEATURE_ENGINEERING", "MODEL_SELECTION", "TIME_SERIES"),
    "deep_learning": ("DL_", "DEEP_LEARNING"),
    "mlops": ("MLOPS", "MONITORING", "DRIFT", "EXPLAINABILITY"),
    "programming": ("PYTHON", "PANDAS", "CODING", "DATA_PREPROCESSING"),
}

ROLE_DEFAULT_COMPETENCIES = {
    "DA": "analytics",
    "DE": "data_engineering",
    "DS": "machine_learning",
    "MLE": "mlops",
    "BE": "programming",
    "FE": "programming",
}

DIFFICULTY_LABEL_TO_SCORE = {
    "easy": 2.5,
    "medium": 5.0,
    "hard": 7.5,
    "expert": 9.0,
}


def _question_competency(question: dict) -> str | None:
    """Infer an internal competency area from tags, role, and id."""
    tags = [str(tag).upper() for tag in question.get("skill_tags", [])]
    text = " ".join(tags)

    for domain, hints in TAG_COMPETENCY_HINTS.items():
        if any(hint in text for hint in hints):
            return domain

    question_id = str(question.get("question_id", "")).upper()
    primary_role = str(question.get("roles", {}).get("primary", "")).upper()
    if primary_role in ROLE_DEFAULT_COMPETENCIES:
        return ROLE_DEFAULT_COMPETENCIES[primary_role]
    for role, competency in ROLE_DEFAULT_COMPETENCIES.items():
        if question_id.startswith(role):
            return competency
    return None


def _difficulty_score(question: dict) -> float:
    score = question.get("difficulty_score")
    if score is not None:
        return float(np.clip(float(score), 1.0, 10.0))
    label = str(question.get("difficulty_label", "medium")).lower()
    return DIFFICULTY_LABEL_TO_SCORE.get(label, 5.0)


def adaptive_difficulty(current_score: float, streak: int = 0) -> str:
    """
    Pick the next difficulty from the user's current score.

    Args:
        current_score: Domain score from 0 to 10.
        streak: Positive means consecutive good answers, negative means misses.

    Returns:
        "easy", "medium", or "hard".
    """
    score = float(np.clip(current_score, 0.0, 10.0))

    if streak >= 3:
        score += 1.0
    elif streak <= -2:
        score -= 1.0

    if score < 4.0:
        return "easy"
    if score < 7.0:
        return "medium"
    return "hard"


def recommend_questions(
    competency_vector: np.ndarray,
    question_bank: list[dict],
    num_recommendations: int = 5,
    focus_weak: bool = True,
) -> list[dict]:
    """
    Recommend interview questions from a competency vector.

    The vector follows COMPETENCY_KEYS:
        sql, analytics, statistics, visualization, data_engineering, big_data,
        machine_learning, deep_learning, mlops, programming.

    Scoring formula when focus_weak=True:
        65% weak-skill priority + 30% difficulty fit + small coverage bonus.

    Scoring formula when focus_weak=False:
        45% readiness + 45% difficulty fit + small coverage bonus.

    Returned questions include explanation fields:
        recommendation_score, recommended_competency, target_difficulty.
    """
    if num_recommendations <= 0 or not question_bank:
        return []

    vector = np.asarray(competency_vector, dtype=float).flatten()
    if vector.size < len(COMPETENCY_KEYS):
        vector = np.pad(vector, (0, len(COMPETENCY_KEYS) - vector.size))
    vector = np.clip(vector[: len(COMPETENCY_KEYS)], 0.0, 10.0)

    scored_questions = []
    for index, question in enumerate(question_bank):
        competency = _question_competency(question)
        competency_index = COMPETENCY_KEYS.index(competency) if competency in COMPETENCY_KEYS else None
        competency_score = float(vector[competency_index]) if competency_index is not None else float(np.mean(vector))

        weak_priority = (10.0 - competency_score) / 10.0
        target_difficulty = DIFFICULTY_LABEL_TO_SCORE[adaptive_difficulty(competency_score)]
        difficulty_fit = 1.0 - min(abs(_difficulty_score(question) - target_difficulty) / 9.0, 1.0)
        coverage_bonus = 0.15 if competency_index is None else 0.0

        if focus_weak:
            score = 0.65 * weak_priority + 0.30 * difficulty_fit + coverage_bonus
        else:
            readiness = competency_score / 10.0
            score = 0.45 * readiness + 0.45 * difficulty_fit + coverage_bonus

        enriched = dict(question)
        enriched["recommendation_score"] = round(float(score), 4)
        enriched["recommended_competency"] = competency
        enriched["target_difficulty"] = adaptive_difficulty(competency_score).upper()
        scored_questions.append((score, -index, enriched))

    scored_questions.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [question for _, _, question in scored_questions[:num_recommendations]]
