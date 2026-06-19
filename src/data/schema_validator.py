"""
✅ Schema Validator
====================
Người phụ trách: Data & Backend Lead
Mục đích: Validate dữ liệu đầu vào theo Data Contract (JSON Schema).
          Đảm bảo tính toàn vẹn dữ liệu trước khi truyền sang AI module.
"""

import json
from pathlib import Path
from jsonschema import validate, ValidationError
from typing import Any

_BASE_DIR = Path(__file__).resolve().parents[2]
_SCHEMA_DIR = _BASE_DIR / "data" / "schemas"


def load_schema(schema_path: str) -> dict:
    """Load JSON Schema từ file (path tuyệt đối hoặc relative tới schemas/)."""
    p = Path(schema_path)
    if not p.is_absolute():
        p = _SCHEMA_DIR / p.name
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_user_profile(profile: dict) -> tuple[bool, str]:
    """
    Validate hồ sơ người dùng theo schema.

    Returns:
        (is_valid, error_message)
    """
    schema = load_schema("user_profile.schema.json")
    try:
        validate(instance=profile, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, str(e.message)


def validate_question(question: dict) -> tuple[bool, str]:
    """
    Validate câu hỏi theo schema.

    Returns:
        (is_valid, error_mess        (is_valid, error_message)
    """
    schema = load_schema("question_bank.schema.json")
    try:
        validate(instance=question, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, str(e.message)
    except Exception as e:
        return False, f"Schema load error: {e}"


def validate_batch(items: list[dict], schema_path: str) -> list[tuple[int, str]]:
    """
    Validate nhiều item cùng lúc.

    Returns: list (index, error_message) cho các item lỗi.
    """
    schema = load_schema(schema_path)
    errors = []
    for i, item in enumerate(items):
        try:
            validate(instance=item, schema=schema)
        except ValidationError as e:
            errors.append((i, str(e.message)))
    return errors
