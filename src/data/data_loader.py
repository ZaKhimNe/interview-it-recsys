import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parents[2]  # src/data/ → src/ → root

QUESTION_DATA_PATH    = BASE_DIR / "data" / "raw" / "question_bank" / "question_bank.json"
USER_DATA_PATH        = BASE_DIR / "data" / "raw" / "simulation" / "virtual_users.json"
INTERACTION_LOG_PATH  = BASE_DIR / "data" / "raw" / "simulation" / "interaction_log.csv"
SELF_RATING_LOG_PATH  = BASE_DIR / "data" / "raw" / "simulation" / "self_rating_log.csv"

JD_REQUIREMENTS_PATH = BASE_DIR / "data" / "schemas" / "jd_requirements.schema.json"
SKILL_TAXONOMY_PATH  = BASE_DIR / "data" / "schemas" / "skill_taxonomy.schema.json"

VALID_ROLES = {"DA", "DE", "DS"}
VALID_QUESTION_TYPES = {
    "THEORY", "CODING", "PRACTICE",
    "MC_SINGLE", "TRUE_FALSE", "FILL_BLANK", "CODING_EXERCISE",
}
VALID_DIFFICULTIES = {"EASY", "MEDIUM", "HARD"}


def load_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = []
    if not path.exists():
        print(f"[data_loader] File not found: {path}")
        return default
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        print(f"[data_loader] Invalid JSON in {path}: {error}")
        return default


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_role(raw_roles: Any) -> Dict[str, Any]:
    if isinstance(raw_roles, dict):
        primary = raw_roles.get("primary") or "UNKNOWN"
        secondary = as_list(raw_roles.get("secondary"))
    elif isinstance(raw_roles, str):
        primary = raw_roles
        secondary = []
    elif isinstance(raw_roles, list) and raw_roles:
        primary = raw_roles[0]
        secondary = raw_roles[1:]
    else:
        primary = "UNKNOWN"
        secondary = []

    primary = str(primary).upper()
    if primary not in VALID_ROLES:
        primary = "UNKNOWN"
    secondary = [
        str(r).upper() for r in secondary if str(r).upper() in VALID_ROLES
    ]
    return {"primary": primary, "secondary": secondary}


def normalize_answers(raw_answers: Any) -> Dict[str, Any]:
    """Normalize answers while preserving ALL original fields."""
    if not isinstance(raw_answers, dict):
        return {
            "detailed": str(raw_answers) if raw_answers else "",
            "evaluation_points": [],
        }
    detailed = (
        raw_answers.get("detailed")
        or raw_answers.get("sample_answer")
        or raw_answers.get("expert_answer")
        or raw_answers.get("reference_answer")
        or ""
    )
    evaluation_points = as_list(
        raw_answers.get("evaluation_points")
        or raw_answers.get("rubric")
        or raw_answers.get("criteria")
        or []
    )
    # Preserve ALL original fields (needed for MC_SINGLE, TRUE_FALSE, FILL_BLANK)
    result = dict(raw_answers)
    result["detailed"] = detailed
    result["evaluation_points"] = evaluation_points
    return result


def normalize_question(raw_question: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(raw_question, dict):
        return None
    question_id = raw_question.get("question_id")
    question_text = raw_question.get("question_text")
    if not question_id or not question_text:
        return None

    roles = normalize_role(raw_question.get("roles", {}))

    difficulty_label = str(raw_question.get("difficulty_label", "MEDIUM")).upper()
    if difficulty_label not in VALID_DIFFICULTIES:
        difficulty_label = "MEDIUM"

    try:
        difficulty_score = int(raw_question.get("difficulty_score", 0))
    except (TypeError, ValueError):
        difficulty_score = 0

    question_type = str(raw_question.get("question_type", "THEORY")).upper()
    if question_type not in VALID_QUESTION_TYPES:
        question_type = "THEORY"

    skill_tags = [str(s) for s in as_list(raw_question.get("skill_tags")) if s]
    skill_groups = [str(g) for g in as_list(raw_question.get("skill_groups")) if g]

    return {
        "question_id": str(question_id),
        "question_text": str(question_text),
        "roles": roles,
        "difficulty_label": difficulty_label,
        "difficulty_score": difficulty_score,
        "question_type": question_type,
        "skill_tags": skill_tags,
        "skill_groups": skill_groups,
        "answers": normalize_answers(raw_question.get("answers")),
        "metadata": raw_question.get("metadata", {}),
        # New-type fields (None when not applicable)
        "options": raw_question.get("options"),
        "template": raw_question.get("template"),
        "test_cases": raw_question.get("test_cases"),
        "starter_code": raw_question.get("starter_code"),
        "constraints": raw_question.get("constraints"),
        "allowed_languages": raw_question.get("allowed_languages"),
    }


@lru_cache(maxsize=1)
def load_question_bank() -> List[Dict[str, Any]]:
    raw_data = load_json(QUESTION_DATA_PATH, default=[])
    if isinstance(raw_data, dict):
        raw_questions = (
            raw_data.get("questions")
            or raw_data.get("question_bank")
            or raw_data.get("data")
            or raw_data.get("items")
            or []
        )
    elif isinstance(raw_data, list):
        raw_questions = raw_data
    else:
        raw_questions = []

    questions = []
    for raw_q in raw_questions:
        norm = normalize_question(raw_q)
        if norm is not None:
            questions.append(norm)
    return questions


def get_questions_by_role(role: str) -> List[Dict[str, Any]]:
    role = role.upper()
    return [q for q in load_question_bank() if q.get("roles", {}).get("primary") == role]


def get_questions_by_type(question_type: str) -> List[Dict[str, Any]]:
    question_type = question_type.upper()
    return [q for q in load_question_bank() if q.get("question_type") == question_type]


def get_questions_by_difficulty(difficulty_label: str) -> List[Dict[str, Any]]:
    difficulty_label = difficulty_label.upper()
    return [q for q in load_question_bank() if q.get("difficulty_label") == difficulty_label]


def get_questions(
    role: Optional[str] = None,
    question_type: Optional[str] = None,
    difficulty_label: Optional[str] = None,
) -> List[Dict[str, Any]]:
    questions = load_question_bank()
    if role:
        role = role.upper()
        questions = [q for q in questions if q.get("roles", {}).get("primary") == role]
    if question_type:
        question_type = question_type.upper()
        questions = [q for q in questions if q.get("question_type") == question_type]
    if difficulty_label:
        difficulty_label = difficulty_label.upper()
        questions = [q for q in questions if q.get("difficulty_label") == difficulty_label]
    return questions


def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    for q in load_question_bank():
        if q["question_id"] == question_id:
            return q
    return None


def get_available_types_for_role(role: str) -> List[str]:
    types: set = set()
    for q in get_questions_by_role(role):
        types.add(q["question_type"])
    return sorted(types)


def load_user_data() -> Any:
    return load_json(USER_DATA_PATH, default=[])


def load_user_info() -> Any:
    return load_json(USER_DATA_PATH, default={})


def load_answer_logs() -> Any:
    return load_json(INTERACTION_LOG_PATH, default=[])


@lru_cache(maxsize=1)
def load_jd_requirements() -> Dict[str, Any]:
    return load_json(JD_REQUIREMENTS_PATH, default={})


@lru_cache(maxsize=1)
def load_skill_taxonomy() -> Dict[str, Any]:
    return load_json(SKILL_TAXONOMY_PATH, default={})


def get_user_profile_by_role(role: str) -> Optional[Dict[str, Any]]:
    role = role.upper()
    users = load_user_data()
    if not isinstance(users, list):
        return None
    for user in users:
        if str(user.get("role", user.get("target_role", ""))).upper() == role:
            return user
    return None


def get_role_requirement(role: str) -> Dict[str, Any]:
    role = role.upper()
    requirements = load_jd_requirements()
    if not isinstance(requirements, dict):
        return {}
    return requirements.get(role, {})


def get_radar_profile_data(role: str) -> Dict[str, Any]:
    role = role.upper()
    user_profile = get_user_profile_by_role(role)
    role_requirement = get_role_requirement(role)
    taxonomy = load_skill_taxonomy()

    if not user_profile or not role_requirement:
        return {
            "role": role,
            "role_name": role,
            "labels": [],
            "skill_keys": [],
            "current_values": [],
            "target_values": [],
            "gaps": [],
            "user_profile": user_profile,
        }

    skill_keys = role_requirement.get("skill_groups", [])
    current_vector = user_profile.get("skill_vector", {})
    target_vector = role_requirement.get("required_vector", {})

    labels, current_values, target_values, gaps = [], [], [], []
    for skill_key in skill_keys:
        display_name = taxonomy.get(skill_key, {}).get("display_name", skill_key)
        current_score = float(current_vector.get(skill_key, 0))
        target_score = float(target_vector.get(skill_key, 0))
        labels.append(display_name)
        current_values.append(current_score)
        target_values.append(target_score)
        gaps.append(max(target_score - current_score, 0))

    return {
        "role": role,
        "role_name": role_requirement.get("role_name", role),
        "labels": labels,
        "skill_keys": skill_keys,
        "current_values": current_values,
        "target_values": target_values,
        "gaps": gaps,
        "user_profile": user_profile,
    }

