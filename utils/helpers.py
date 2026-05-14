"""
🛠️ Helper Functions
=====================
Người phụ trách: Shared
Mục đích: Hàm tiện ích nhỏ dùng chung xuyên suốt dự án.
"""

import json
import hashlib
from datetime import datetime


def generate_id(prefix: str = "ID") -> str:
    """Sinh ID duy nhất dựa trên timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    hash_suffix = hashlib.md5(timestamp.encode()).hexdigest()[:6]
    return f"{prefix}_{hash_suffix.upper()}"


def safe_json_parse(json_string: str) -> dict | None:
    """Parse JSON an toàn, trả về None nếu lỗi."""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None


def format_score(score: float) -> str:
    """Format điểm số hiển thị."""
    return f"{score:.1f}/10"
