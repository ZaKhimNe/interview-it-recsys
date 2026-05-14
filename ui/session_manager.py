"""
🔄 Session State Manager
==========================
Người phụ trách: App Lead
Mục đích: Quản lý tập trung Streamlit Session State.
          Khởi tạo, đọc, cập nhật state cho toàn bộ ứng dụng.
"""

import streamlit as st
from typing import Any, Optional


def init_session_state():
    """Khởi tạo tất cả session state keys với giá trị mặc định."""
    defaults = {
        "user_profile": None,
        "competency_vector": None,
        "current_page": "Dashboard",
        "test_in_progress": False,
        "test_answers": [],
        "interview_history": [],
        "grading_results": [],
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def get_state(key: str, default: Any = None) -> Any:
    """Lấy giá trị từ session state."""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any):
    """Cập nhật giá trị trong session state."""
    st.session_state[key] = value


def reset_session():
    """Reset toàn bộ session state về mặc định."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()
