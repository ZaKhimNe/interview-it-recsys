"""
🚀 AI Tech Interview Prep - MINI DEMO
=====================================
Chạy: streamlit run app.py
"""

import streamlit as st
import random
import numpy as np
from textwrap import dedent

from core.data_loader import load_question_bank
from ui.components.charts import create_radar_chart
from ui.session_manager import init_session_state
from ui.styles import inject_custom_css

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


def show_onboarding():
    """
    Màn hình đầu tiên để người dùng chọn role muốn ứng tuyển.
    Dùng hero background từ assets/onboarding_bg.png.
    """

    st.markdown(dedent("""
    <div class="hero-card">
    <div class="hero-sticker">FOCUS / PREPARE / PERFORM</div>
    <div class="hero-content">
        <div class="hero-kicker">CAREER CONSOLE • LEVEL UP YOUR CAREER</div>
        <div class="hero-title">
        AI TECH<br>
        <span>INTERVIEW PREP</span>
        </div>
        <div class="hero-subtitle">Interview training for Data careers</div>
        <div class="hero-desc">
        Đánh giá năng lực → Luyện phỏng vấn → Nhận gợi ý kỹ năng cần cải thiện
        </div>
        <div class="hero-tags">
        <span class="hero-tag cyan">Skill Assessment</span>
        <span class="hero-tag pink">Role-Based Practice</span>
        <span class="hero-tag yellow">Skill Gap Recommendation</span>
        </div>
    </div>
    </div>
    """).strip(), unsafe_allow_html=True)

    st.markdown(dedent("""
    <div class="street-title-wrap">
        <div class="street-title">Choose your <span>target role</span></div>
    </div>
    """), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown("""<div class="role-card role-da" data-index="01">
        <div class="role-kicker">Analyze • Insight • Impact</div>
        <div class="role-number">01 / FOUNDATION TRACK</div>
        <div class="role-name">Data Analyst</div>
        <div class="mission-label">Mission</div>
        <div class="role-desc">Turn raw business data into clear insight through SQL, dashboards, and analytical thinking.</div>
        <div class="mission-label">Focus Areas</div>
        <div class="focus-list">
        <div>SQL Querying</div>
        <div>Dashboard Thinking</div>
        <div>Business Insight</div>
        </div>
        <div class="mission-label">Skill Loadout</div>
        <div class="skill-tags">
        <span class="skill-tag">SQL</span>
        <span class="skill-tag">BI</span>
        <span class="skill-tag">STATS</span>
        </div>
        <div class="readiness-wrap">
        <div class="readiness-text">
        <span>Assessment Status</span>
        <span>Not Started</span>
        </div>
        <div class="pending-profile">
        Start this track to build your first competency profile.
        </div>
        </div>
        </div>""", unsafe_allow_html=True)

        if st.button("Start Analyst Track  →", key="role_da", use_container_width=True):
            st.session_state.user_role = "DA"
            st.session_state.demo_step = "START"
            st.session_state.current_question = None
            st.session_state.user_answer = ""
            st.rerun()

    with col2:
        st.markdown("""<div class="role-card role-de" data-index="02">
        <div class="role-kicker">Build • Pipelines • Power Data</div>
        <div class="role-number">02 / INFRASTRUCTURE TRACK</div>
        <div class="role-name">Data Engineer</div>
        <div class="mission-label">Mission</div>
        <div class="role-desc">Build reliable data pipelines that collect, transform, and serve data at scale.</div>
        <div class="mission-label">Focus Areas</div>
        <div class="focus-list">
        <div>ETL Design</div>
        <div>Database Systems</div>
        <div>Cloud Pipeline</div>
        </div>
        <div class="mission-label">Skill Loadout</div>
        <div class="skill-tags">
        <span class="skill-tag">ETL</span>
        <span class="skill-tag">CLOUD</span>
        <span class="skill-tag">DATABASE</span>
        </div>
        <div class="readiness-wrap">
        <div class="readiness-text">
        <span>Assessment Status</span>
        <span>Not Started</span>
        </div>
        <div class="pending-profile">
        Start this track to build your first competency profile.
        </div>
        </div>
        </div>""", unsafe_allow_html=True)

        if st.button("Start Engineer Track  →", key="role_de", use_container_width=True):
            st.session_state.user_role = "DE"
            st.session_state.demo_step = "START"
            st.session_state.current_question = None
            st.session_state.user_answer = ""
            st.rerun()

    with col3:
        st.markdown("""<div class="role-card role-ds" data-index="03">
        <div class="role-kicker">Explore • Experiment • Explain</div>
        <div class="role-number">03 / MODELING TRACK</div>
        <div class="role-name">Data Scientist</div>
        <div class="mission-label">Mission</div>
        <div class="role-desc">Experiment, model, and explain data-driven decisions through machine learning.</div>
        <div class="mission-label">Focus Areas</div>
        <div class="focus-list">
        <div>Machine Learning</div>
        <div>Model Evaluation</div>
        <div>Experiment Thinking</div>
        </div>
        <div class="mission-label">Skill Loadout</div>
        <div class="skill-tags">
        <span class="skill-tag">PYTHON</span>
        <span class="skill-tag">ML</span>
        <span class="skill-tag">MODELING</span>
        </div>
        <div class="readiness-wrap">
        <div class="readiness-text">
        <span>Assessment Status</span>
        <span>Not Started</span>
        </div>
        <div class="pending-profile">
        Start this track to build your first competency profile.
        </div>
        </div>
        </div>""", unsafe_allow_html=True)

        if st.button("Start Scientist Track  →", key="role_ds", use_container_width=True):
            st.session_state.user_role = "DS"
            st.session_state.demo_step = "START"
            st.session_state.current_question = None
            st.session_state.user_answer = ""
            st.rerun()

    st.markdown("""<div class="pipeline-board">
    <div class="pipeline-header-row">
    <div>
    <div class="pipeline-title">How it works</div>
    </div>
    <div class="pipeline-subtitle">From role selection to interview answers, the system builds a competency profile and recommends what to improve next.</div>
    </div>
    <div class="pipeline-flow">
    <div class="pipeline-step pipeline-1">
    <div class="pipeline-no">01 / INPUT</div>
    <div class="pipeline-step-title">Choose Target Role</div>
    <div class="pipeline-desc">Select the career track you want to prepare for: Analyst, Engineer, or Scientist.</div>
    <div class="pipeline-chip">Role Context</div>
    </div>
    <div class="pipeline-step pipeline-2">
    <div class="pipeline-no">02 / INTERVIEW</div>
    <div class="pipeline-step-title">Answer Questions</div>
    <div class="pipeline-desc">Practice theory or coding questions designed around the selected role.</div>
    <div class="pipeline-chip">Response Data</div>
    </div>
    <div class="pipeline-step pipeline-3">
    <div class="pipeline-no">03 / PROFILE</div>
    <div class="pipeline-step-title">Build Competency Profile</div>
    <div class="pipeline-desc">Your answers are evaluated and converted into a skill profile for the current track.</div>
    <div class="pipeline-chip">Skill Profile</div>
    </div>
    <div class="pipeline-step pipeline-4">
    <div class="pipeline-no">04 / OUTPUT</div>
    <div class="pipeline-step-title">Gap & Recommendation</div>
    <div class="pipeline-desc">Compare your current profile with role requirements and suggest skills to improve.</div>
    <div class="pipeline-chip">Next Actions</div>
    </div>
    </div>
    <div class="pipeline-output"><strong>Demo flow:</strong> Choose role → answer interview questions → generate competency profile → view gap and skill recommendations.</div>
    </div>""", unsafe_allow_html=True)

def reset_app():
    """
    Reset toàn bộ trạng thái để người dùng chọn lại role từ đầu.
    """

    st.session_state.user_role = None
    st.session_state.demo_step = "START"
    st.session_state.current_question = None
    st.session_state.user_answer = ""
    st.session_state.answer_history = []
    st.rerun()


def show_sidebar():
    """
    Sidebar sau khi người dùng đã chọn role.
    Lưu ý: Không cho chọn role bằng selectbox nữa.
    Role phải lấy từ st.session_state.user_role.
    """

    with st.sidebar:
        st.header("⚙️ Cấu hình")

        role = st.session_state.user_role

        role_name = {
            "DA": "📊 Data Analyst",
            "DE": "🛠️ Data Engineer",
            "DS": "🧪 Data Scientist"
        }.get(role, role)

        st.write("Role hiện tại:")
        st.success(role_name)

        st.divider()

        if st.button("🔄 Chọn lại role", key="sidebar_reset_role"):
            reset_app()


def show_start_screen(role):
    """
    Màn hình START.
    Người dùng bấm nút để bắt đầu lấy câu hỏi đầu tiên.
    """

    st.info(
        f"Hệ thống đã sẵn sàng cho vị trí **{role}**. "
        "Nhấn nút bên dưới để bắt đầu câu hỏi đầu tiên."
    )

    if st.button("Bắt đầu Phỏng vấn", key="start_interview_button"):
        all_questions = load_question_bank()

        role_questions = [
            q for q in all_questions
            if q.get("roles", {}).get("primary") == role
        ]

        if role_questions:
            st.session_state.current_question = random.choice(role_questions)
            st.session_state.demo_step = "INTERVIEW"
            st.rerun()
        else:
            st.error(f"Xin lỗi, hiện chưa có dữ liệu cho role {role}")


def show_interview_screen():
    """
    Màn hình INTERVIEW.
    Hiển thị câu hỏi và cho người dùng nhập câu trả lời.
    """

    q = st.session_state.current_question

    if q is None:
        st.warning("Chưa có câu hỏi. Vui lòng quay lại bắt đầu phỏng vấn.")
        if st.button("Quay lại", key="back_to_start_from_interview"):
            st.session_state.demo_step = "START"
            st.rerun()
        return

    st.subheader(f"❓ Câu hỏi: {q['question_id']}")
    st.write(q["question_text"])

    answer = st.text_area(
        "Câu trả lời của bạn:",
        value=st.session_state.user_answer,
        placeholder="Nhập câu trả lời tại đây...",
        height=150
    )

    if st.button("Gửi câu trả lời", key="submit_answer_button"):
        if answer.strip():
            st.session_state.user_answer = answer

            st.session_state.answer_history.append(
                {
                    "question_id": q.get("question_id"),
                    "question_text": q.get("question_text"),
                    "user_answer": answer,
                    "skill_tags": q.get("skill_tags", []),
                    "role": st.session_state.user_role
                }
            )

            st.session_state.demo_step = "RESULT"
            st.rerun()
        else:
            st.warning("Vui lòng nhập câu trả lời trước khi gửi!")


def show_result_screen(role):
    """
    Màn hình RESULT.
    Hiển thị câu trả lời của người dùng, đáp án chuyên gia và radar chart giả lập.
    """

    q = st.session_state.current_question

    if q is None:
        st.warning("Không tìm thấy câu hỏi hiện tại.")
        if st.button("Quay lại", key="back_to_start_from_result"):
            st.session_state.demo_step = "START"
            st.rerun()
        return

    st.success("✅ Đã ghi nhận câu trả lời!")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Đánh giá & Đáp án")

        st.write("**Câu trả lời của bạn:**")
        st.info(st.session_state.user_answer)

        with st.expander("Xem đáp án chuyên gia", expanded=True):
            st.write(q["answers"]["detailed"])

            st.markdown("**Các ý chính cần có:**")
            for point in q["answers"].get("evaluation_points", []):
                st.write(f"- {point}")

    with col2:
        st.subheader("📊 Biểu đồ Năng lực (Giả lập)")

        # Vector giả lập để demo Radar Chart.
        # Sau này phần này sẽ được thay bằng điểm thật từ AI Evaluator.
        mock_vector = np.array([7.5, 6.0, 8.5, 4.0, 5.5, 3.0])

        fig = create_radar_chart(
            mock_vector,
            title=f"Năng lực sau phỏng vấn {role}"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info(
            "💡 Lưu ý: Điểm số trên là giả lập cho Demo. "
            "Bản chính thức sẽ dùng AI để chấm điểm thật."
        )

    st.divider()

    col_a, col_b = st.columns([1, 1])

    with col_a:
        if st.button("👉 Thử câu hỏi khác", key="try_another_question_button"):
            st.session_state.current_question = None
            st.session_state.user_answer = ""
            st.session_state.demo_step = "START"
            st.rerun()

    with col_b:
        if st.button("🔄 Chọn lại role", key="result_reset_role"):
            reset_app()


def show_main_app():
    """
    App chính sau khi người dùng đã hoàn thành onboarding.
    Điều hướng theo demo_step: START → INTERVIEW → RESULT.
    """

    role = st.session_state.user_role

    st.title("🎯 AI Tech Interview Prep - Mini Demo")

    show_sidebar()

    # Logic điều hướng demo
    if st.session_state.demo_step == "START":
        show_start_screen(role)

    elif st.session_state.demo_step == "INTERVIEW":
        show_interview_screen()

    elif st.session_state.demo_step == "RESULT":
        show_result_screen(role)

    else:
        st.warning("Trạng thái không hợp lệ. Đang reset về màn hình bắt đầu.")
        st.session_state.demo_step = "START"
        st.rerun()


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

    # Nếu đã chọn role thì vào app chính
    show_main_app()


if __name__ == "__main__":
    main()