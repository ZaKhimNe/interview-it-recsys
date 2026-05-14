"""
🧩 Shared UI Components
=========================
Người phụ trách: App Lead
Mục đích: Component dùng chung: sidebar, header, footer,
          notification toasts, loading spinners.
"""

import streamlit as st


def render_sidebar():
    """Render sidebar navigation chung."""
    with st.sidebar:
        st.image("assets/logo.png", width=200) if False else None
        st.title("🎯 AI Interview Prep")
        st.divider()

        page = st.radio(
            "📌 Điều hướng",
            options=["Dashboard", "Bài đánh giá", "Mô phỏng phỏng vấn"],
            index=0,
        )
        st.divider()
        st.caption("© 2026 InternHub Team")
    return page


def render_metric_card(label: str, value: str, delta: str = None):
    """Render metric card thống kê."""
    st.metric(label=label, value=value, delta=delta)
