"""
🧮 Competency Engine
=====================
Người phụ trách: Data & Backend Lead
Mục đích: Quản lý và tính toán vector năng lực người dùng.
          Cập nhật điểm năng lực sau mỗi lần test/phỏng vấn.
"""

import numpy as np
from typing import Optional


def create_competency_vector(scores: dict[str, float]) -> np.ndarray:
    """
    Tạo vector năng lực từ dict điểm số.

    Args:
        scores: Dict với key là domain, value là điểm (0-10)

    Returns:
        numpy array đại diện cho vector năng lực
    """
    domains = ["dsa", "system_design", "database", "oop", "networking", "devops"]
    return np.array([scores.get(d, 0.0) for d in domains])


def update_competency(
    current_vector: np.ndarray,
    new_scores: np.ndarray,
    learning_rate: float = 0.3,
) -> np.ndarray:
    """
    Cập nhật vector năng lực theo Exponential Moving Average.

    Args:
        current_vector: Vector năng lực hiện tại
        new_scores: Điểm số mới từ bài test/phỏng vấn
        learning_rate: Tốc độ cập nhật (0-1)

    Returns:
        Vector năng lực đã cập nhật
    """
    updated = (1 - learning_rate) * current_vector + learning_rate * new_scores
    return np.clip(updated, 0.0, 10.0)


def identify_weak_domains(
    vector: np.ndarray, threshold: float = 5.0
) -> list[str]:
    """Xác định các domain yếu cần cải thiện."""
    domains = ["dsa", "system_design", "database", "oop", "networking", "devops"]
    return [d for d, score in zip(domains, vector) if score < threshold]
