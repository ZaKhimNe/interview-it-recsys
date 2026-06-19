"""Helper Functions — tien ich dung chung cho API layer."""

import json
import hashlib
import re
from datetime import datetime, timezone
from typing import Any


def generate_id(prefix: str = "ID") -> str:
    """Sinh ID duy nhat dua tren timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    suffix = hashlib.md5(timestamp.encode()).hexdigest()[:6].upper()
    return f"{prefix}_{suffix}"


def safe_json_parse(json_string: str) -> dict | None:
    """Parse JSON an toan, tra None neu loi."""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None


def format_score(score: float) -> str:
    """Format diem so hien thi (tren thang 10)."""
    return f"{score:.1f}/10"


# ── API response wrappers ──────────────────────────────────────────────────────

def success_response(data: Any, message: str = "OK") -> dict:
    """
    Chuẩn hóa response thành công.

    Returns:
        {"status": "success", "message": ..., "data": ..., "timestamp": ...}
    """
    return {
        "status": "success",
        "message": message,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def error_response(message: str, code: str = "ERROR", detail: Any = None) -> dict:
    """
    Chuẩn hóa response lỗi.

    Returns:
        {"status": "error", "code": ..., "message": ..., "detail": ..., "timestamp": ...}
    """
    return {
        "status": "error",
        "code": code,
        "message": message,
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Validation ─────────────────────────────────────────────────────────────────

def validate_required_fields(data: dict, required: list[str]) -> tuple[bool, list[str]]:
    """
    Kiem tra cac truong bat buoc trong request body.

    Returns:
        (is_valid: bool, missing_fields: list[str])
    """
    missing = [f for f in required if f not in data or data[f] is None]
    return (len(missing) == 0), missing


def validate_role(role: str) -> bool:
    return str(role).upper() in {"DA", "DS", "DE"}


def validate_difficulty(difficulty: str) -> bool:
    return str(difficulty).upper() in {"EASY", "MEDIUM", "HARD"}


# ── Text utilities ─────────────────────────────────────────────────────────────

def truncate_text(text: str, max_len: int = 200) -> str:
    """Cat text dai cho log, them '...' neu bi cat."""
    if not text:
        return ""
    text = str(text)
    return text[:max_len] + "..." if len(text) > max_len else text


def sanitize_text(text: str) -> str:
    """Loai bo ky tu dac biet, giu lai chu + so + khoang trang."""
    return re.sub(r"[^\w\s\.,!?;:()\-]", "", text, flags=re.UNICODE).strip()


def normalize_question_type(qtype: str) -> str:
    """Chuan hoa question_type ve UPPERCASE, fallback THEORY."""
    valid = {"THEORY", "PRACTICE", "CODING", "MC_SINGLE", "TRUE_FALSE", "FILL_BLANK", "CODING_EXERCISE"}
    normalized = str(qtype).upper()
    return normalized if normalized in valid else "THEORY"


# ── Misc ───────────────────────────────────────────────────────────────────────

def safe_float(value: Any, default: float = 0.0) -> float:
    """Ep kieu sang float an toan."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
