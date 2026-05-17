import streamlit as st


def reset_to_onboarding():
    """
    Reset app về màn hình chọn role ban đầu.
    """
    st.session_state.user_role = None
    st.session_state.demo_step = "ONBOARDING"
    st.session_state.current_question = None
    st.session_state.user_answer = ""

    if "answer_history" in st.session_state:
        st.session_state.answer_history = []

    st.rerun()


def show_sidebar():
    """
    Sidebar hiển thị role hiện tại và nút chọn lại role.
    """
    role = st.session_state.get("user_role", None)

    role_name = {
        "DA": "Data Analyst",
        "DE": "Data Engineer",
        "DS": "Data Scientist"
    }.get(role, "Chưa chọn role")

    with st.sidebar:
        st.header("⚙️ Cấu hình")

        st.markdown("**Role hiện tại:**")
        st.success(role_name)

        st.markdown("---")

        if st.button("🔄 Chọn lại role", key="sidebar_reset_role"):
            reset_to_onboarding()