"""
✅ Schema Validator
====================
Người phụ trách: Data & Backend Lead
Mục đích: Validate dữ liệu đầu vào theo Data Contract (JSON Schema).
          Đảm bảo tính toàn vẹn dữ liệu trước khi truyền sang AI module.
"""

import json
from jsonschema import validate, ValidationError
from typing import Any


def load_schema(schema_path: str) -> dict:
    """Load JSON Schema từ file."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_user_profile(profile: dict) -> tuple[bool, str]:
    """
    Validate hồ sơ người dùng theo schema.

    Returns:
        (is_valid, error_message)
    """
    schema = load_schema("data/schemas/user_profile.schema.json")
    try:
        validate(instance=profile, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, str(e.message)


def validate_question(question: dict) -> tuple[bool, str]:
    """
    Validate câu hỏi theo schema.

    Returns:
        (is_valid, error_message)
    """
    schema = load_schema("data/schemas/question_bank.schema.json")
    try:
        validate(instance=question, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, str(e.message)
