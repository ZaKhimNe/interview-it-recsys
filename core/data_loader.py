"""
📊 Data Loader
===============
Người phụ trách: Data & Backend Lead
Mục đích: Đọc, parse và validate dữ liệu từ JSON/CSV.
          Load Data Contract (schema) và mock data.
"""

import json
import os
from typing import Any


def load_json(filepath: str) -> Any:
    """Đọc và parse file JSON."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_question_bank(data_dir: str = "data/mock") -> list[dict]:
    """Load ngân hàng câu hỏi từ file mockdata.json mới."""
    filepath = os.path.join(data_dir, "mockdata.json")
    if not os.path.exists(filepath):
        # Fallback về file cũ nếu chưa có file mới
        filepath = os.path.join(data_dir, "sample_questions.json")
    return load_json(filepath)


def load_user_profiles(data_dir: str = "data/mock") -> list[dict]:
    """Load danh sách hồ sơ người dùng."""
    filepath = os.path.join(data_dir, "sample_users.json")
    return load_json(filepath)
