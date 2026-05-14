"""
📝 Test Generator
==================
Người phụ trách: Data & Backend Lead
Mục đích: Sinh bài test đầu vào (Entry Assessment) dựa trên
          cấu hình role và mức độ khó mong muốn.
"""

import random
from typing import Optional
from core.data_loader import load_question_bank


def generate_entry_test(
    target_role: str,
    num_questions: int = 10,
    difficulty_mix: Optional[dict[str, int]] = None,
) -> list[dict]:
    """
    Sinh bài test đầu vào cho ứng viên.

    Args:
        target_role: Vị trí ứng tuyển
        num_questions: Số câu hỏi
        difficulty_mix: Phân bổ độ khó {"easy": 4, "medium": 4, "hard": 2}

    Returns:
        Danh sách câu hỏi được chọn
    """
    if difficulty_mix is None:
        difficulty_mix = {"easy": 4, "medium": 4, "hard": 2}

    question_bank = load_question_bank()
    selected = []

    for difficulty, count in difficulty_mix.items():
        pool = [q for q in question_bank if q["difficulty"] == difficulty]
        selected.extend(random.sample(pool, min(count, len(pool))))

    random.shuffle(selected)
    return selected[:num_questions]
