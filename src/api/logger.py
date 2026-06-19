"""Logger — cau hinh logging tap trung, structured log cho grading events."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loguru import logger

_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Xoa handler mac dinh
logger.remove()

# Console (development)
logger.add(
    sys.stderr,
    level="DEBUG",
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    colorize=True,
)

# File (production) — absolute path
logger.add(
    str(_LOG_DIR / "app_{time:YYYY-MM-DD}.log"),
    level="INFO",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
)


def get_logger(module_name: str):
    """Lay logger instance cho module cu the."""
    return logger.bind(name=module_name)


# ── Structured log helpers ─────────────────────────────────────────────────────

def log_grade_event(
    user_id: str,
    question_id: str,
    question_type: str,
    score: float,
    method: str,
    is_correct: bool,
    latency_ms: Optional[float] = None,
    extra: Optional[dict] = None,
) -> None:
    """
    Ghi structured log sau moi lan cham diem.

    Fields: user_id, question_id, question_type, score, method, is_correct,
            latency_ms, timestamp, + extra fields tuy chon.
    """
    payload = {
        "event": "grade",
        "user_id": user_id,
        "question_id": question_id,
        "question_type": question_type,
        "score": round(float(score), 2),
        "method": method,
        "is_correct": is_correct,
        "latency_ms": round(latency_ms, 1) if latency_ms is not None else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)
    logger.info(payload)


def log_recommendation_event(
    user_id: str,
    role: str,
    n_recommended: int,
    focus_weak: bool,
    top_kcs: Optional[list[str]] = None,
) -> None:
    """Ghi log khi he thong goi y cau hoi."""
    logger.info({
        "event": "recommend",
        "user_id": user_id,
        "role": role,
        "n_recommended": n_recommended,
        "focus_weak": focus_weak,
        "top_kcs": top_kcs or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def log_assessment_event(
    user_id: str,
    role: str,
    stage: str,
    score: float,
    level: Optional[str] = None,
) -> None:
    """Ghi log ket qua assessment stage."""
    logger.info({
        "event": "assessment",
        "user_id": user_id,
        "role": role,
        "stage": stage,
        "score": round(float(score), 4),
        "level": level,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def log_error(
    module: str,
    function: str,
    error: Exception,
    context: Optional[dict] = None,
) -> None:
    """Ghi log loi co context."""
    logger.error({
        "event": "error",
        "module": module,
        "function": function,
        "error_type": type(error).__name__,
        "error_msg": str(error),
        "context": context or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
