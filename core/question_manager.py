"""
📋 Question Manager
====================
Phụ trách: Data Lead
Mục đích: Tạo bài kiểm tra chẩn đoán (diagnostic test) dựa trên JD requirements.
          Hỗ trợ lọc theo loại câu hỏi, ưu tiên skill group, ẩn đáp án.
"""

import json
import random
from pathlib import Path


JD_REQUIREMENTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "schemas"
    / "jd_requirements.schema.json"
)


def _load_jd_requirements():
    try:
        with open(JD_REQUIREMENTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"JD requirements not found at {JD_REQUIREMENTS_PATH}. "
            f"Ensure the file exists before running diagnostic selection."
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in JD requirements file: {e}")


def _normalize_question_bank(question_bank):
    if isinstance(question_bank, list):
        return question_bank

    if isinstance(question_bank, dict):
        if "questions" in question_bank:
            return question_bank["questions"]
        raise ValueError("question_bank dict must contain a 'questions' key.")

    raise TypeError("question_bank must be a list or a dict with 'questions'.")


def _hide_answer_fields(question):
    hidden_fields = {"answers", "test_cases"}
    return {key: value for key, value in question.items() if key not in hidden_fields}


def _question_matches_role(question, role, include_secondary=False):
    roles = question.get("roles", {})

    if roles.get("primary") == role:
        return True

    if include_secondary and role in roles.get("secondary", []):
        return True

    return False


def _question_matches_types(question, question_types):
    if not question_types:
        return True
    return question.get("question_type", "") in question_types


def get_diagnostic_questions(
    question_bank,
    role,
    n_questions=5,
    seed=None,
    question_types=None,
    include_secondary=False,
):
    """
    Generate a diagnostic test for a target role.

    Logic:
    1. Load JD requirements for the selected role.
    2. Get the role's expected skill groups, prioritized by required_vector score.
    3. Filter questions by role and optionally by question_type.
    4. Pick at most one question from each high-priority skill group.
    5. Fill remaining slots randomly from the filtered pool.
    6. Shuffle the final result.
    7. Return questions without answers/hidden fields.

    Args:
        question_bank: list of question dicts or dict with 'questions' key.
        role: target role code (e.g. 'DA', 'DE', 'DS').
        n_questions: how many questions to select.
        seed: random seed for reproducibility.
        question_types: optional set/list of allowed question_type values
                       (e.g. {'THEORY', 'MC_SINGLE'}). None = all types allowed.
        include_secondary: whether to include questions where role is secondary.
    """
    question_bank = _normalize_question_bank(question_bank)
    jd_requirements = _load_jd_requirements()

    if role not in jd_requirements:
        raise ValueError(
            f"Role '{role}' not found in JD requirements. "
            f"Supported: {list(jd_requirements.keys())}"
        )

    role_config = jd_requirements[role]
    skill_groups = role_config["skill_groups"]
    required_vector = role_config["required_vector"]

    sorted_groups = sorted(
        skill_groups,
        key=lambda group: required_vector.get(group, 0),
        reverse=True,
    )

    role_questions = [
        question
        for question in question_bank
        if _question_matches_role(question, role, include_secondary=include_secondary)
        and _question_matches_types(question, question_types)
    ]

    if len(role_questions) < n_questions:
        raise ValueError(
            f"Not enough questions for role '{role}'"
            + (f" with types {question_types}" if question_types else "")
            + f". Required {n_questions}, available {len(role_questions)}."
        )

    group_pools = {
        group: [
            question
            for question in role_questions
            if group in question.get("skill_groups", [])
        ]
        for group in sorted_groups
    }

    rng = random.Random(seed)
    selected = []
    used_ids = set()

    for group in sorted_groups[:n_questions]:
        available = [
            question
            for question in group_pools.get(group, [])
            if question.get("question_id") not in used_ids
        ]

        if not available:
            continue

        chosen = rng.choice(available)
        selected.append(chosen)
        used_ids.add(chosen["question_id"])

    if len(selected) < n_questions:
        remaining = [
            question
            for question in role_questions
            if question.get("question_id") not in used_ids
        ]

        shortage = n_questions - len(selected)

        if len(remaining) < shortage:
            raise ValueError(
                f"Not enough unique questions to fill {n_questions} slots. "
                f"Available unique: {len(remaining) + len(selected)}, "
                f"needed: {n_questions}."
            )

        selected.extend(rng.sample(remaining, shortage))

    rng.shuffle(selected)

    return [_hide_answer_fields(question) for question in selected]
