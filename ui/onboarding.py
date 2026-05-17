from textwrap import dedent

import streamlit as st

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