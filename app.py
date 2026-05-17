"""
🚀 AI Tech Interview Prep - MINI DEMO
=====================================
Chạy: streamlit run app.py
"""

import streamlit as st

from ui.session_manager import init_session_state
from ui.styles import inject_custom_css
from ui.onboarding import show_onboarding
from ui.sidebar import show_sidebar
from ui.screens import show_main_app

def init_task_1_state():
    """
    Khởi tạo thêm các biến session_state cần cho Nhiệm vụ 1.
    Nếu biến chưa tồn tại thì tạo mới.
    Nếu biến đã tồn tại thì giữ nguyên.
    """

    if "user_role" not in st.session_state:
        st.session_state.user_role = None

    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {
            "SQL_FUNDAMENTALS": 2,
            "PYTHON_PANDAS": 1,
            "DATA_VIZ_TABLEAU": 1,
            "STAT_FUNDAMENTALS": 1
        }

    if "current_question" not in st.session_state:
        st.session_state.current_question = None

    if "answer_history" not in st.session_state:
        st.session_state.answer_history = []

    if "user_answer" not in st.session_state:
        st.session_state.user_answer = ""

    if "demo_step" not in st.session_state:
        st.session_state.demo_step = "START"

def main():
    st.set_page_config(
        page_title="AI Prep Demo",
        page_icon="🎯",
        layout="wide"
    )

    # Inject CSS
    inject_custom_css()

    # Khởi tạo state từ file session_manager.py của project
    init_session_state()

    # Khởi tạo thêm state cho Nhiệm vụ 1
    init_task_1_state()

    # Nếu chưa chọn role thì hiển thị onboarding
    if st.session_state.user_role is None:
        show_onboarding()
        return

    show_sidebar()

    # Nếu đã chọn role thì vào app chính
    show_main_app()


if __name__ == "__main__":
    main()