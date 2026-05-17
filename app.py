"""
🚀 AI Tech Interview Prep - MINI DEMO
=====================================
Chạy: streamlit run app.py
"""

import streamlit as st
import random
import numpy as np
import base64
from pathlib import Path
from textwrap import dedent

from core.data_loader import load_question_bank
from ui.components.charts import create_radar_chart
from ui.session_manager import init_session_state

def get_base64_image(image_path):
    """
    Đọc ảnh local và chuyển thành base64 để dùng làm CSS background.
    """
    path = Path(image_path)

    if not path.exists():
        return ""

    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def inject_custom_css():
    """
    Custom CSS cho onboarding dùng ảnh background trong assets/onboarding_bg.png.
    """

    bg_image = get_base64_image("assets/onboarding_bg.png")

    role_da_image = get_base64_image("assets/role_da_bg.png")
    role_de_image = get_base64_image("assets/role_de_bg.png")
    role_ds_image = get_base64_image("assets/role_ds_bg.png")

    if bg_image:
        page_background = (
            'linear-gradient(180deg, '
            'rgba(5, 8, 13, 0.76) 0%, '
            'rgba(5, 8, 13, 0.88) 48%, '
            'rgba(5, 8, 13, 0.96) 100%), '
            f'url("data:image/png;base64,{bg_image}")'
        )

        hero_background = (
            'linear-gradient(90deg, '
            'rgba(5, 8, 13, 0.92) 0%, '
            'rgba(5, 8, 13, 0.74) 46%, '
            'rgba(5, 8, 13, 0.38) 100%), '
            f'url("data:image/png;base64,{bg_image}")'
        )
        
    else:
        page_background = "linear-gradient(135deg, #07090d 0%, #0b0f17 50%, #080a0f 100%)"
        hero_background = "linear-gradient(135deg, #10131a 0%, #0b0f17 100%)"

    if role_da_image:
        role_da_background = f'url("data:image/png;base64,{role_da_image}")'
    else:
        role_da_background = "none"

    if role_de_image:
        role_de_background = f'url("data:image/png;base64,{role_de_image}")'
    else:
        role_de_background = "none"

    if role_ds_image:
        role_ds_background = f'url("data:image/png;base64,{role_ds_image}")'
    else:
        role_ds_background = "none"

    css = """
    <style>
    /* ===== GLOBAL ===== */
    .stApp {
        background: __PAGE_BG__;
        background-size: cover;
        background-position: center top;
        background-attachment: fixed;
        color: #f4f4f5;
    }

    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 4rem;
        max-width: 1180px;
    }

    /* ===== ANIMATION ===== */
    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(18px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes floatSticker {
        0% {
            transform: rotate(3deg) translateY(0);
        }
        100% {
            transform: rotate(2deg) translateY(-6px);
        }
    }

    @keyframes scanMove {
        0% {
            transform: translateX(-120%);
            opacity: 0;
        }
        35% {
            opacity: 0.28;
        }
        100% {
            transform: translateX(120%);
            opacity: 0;
        }
    }

    @keyframes softGlow {
        0% {
            box-shadow:
                0 0 0 rgba(34, 211, 238, 0),
                0 28px 80px rgba(0, 0, 0, 0.42);
        }
        100% {
            box-shadow:
                0 0 38px rgba(34, 211, 238, 0.08),
                0 32px 95px rgba(0, 0, 0, 0.55);
        }
    }

    @keyframes softPulse {
        from {
            box-shadow: 0 22px 70px rgba(0, 0, 0, 0.45);
        }
        to {
            box-shadow: 0 28px 90px rgba(0, 229, 255, 0.10);
        }
    }

    @keyframes heroBorderGlow {
        0% {
            box-shadow:
                0 0 0 rgba(34, 211, 238, 0),
                0 28px 80px rgba(0, 0, 0, 0.45);
            border-color: rgba(255, 255, 255, 0.14);
        }
        100% {
            box-shadow:
                0 0 32px rgba(34, 211, 238, 0.16),
                0 0 64px rgba(255, 51, 102, 0.08),
                0 32px 95px rgba(0, 0, 0, 0.58);
            border-color: rgba(34, 211, 238, 0.35);
        }
    }

    @keyframes heroScanLine {
        0% {
            left: -45%;
            opacity: 0;
        }
        20% {
            opacity: 0.45;
        }
        55% {
            opacity: 0.18;
        }
        100% {
            left: 110%;
            opacity: 0;
        }
    }

    @keyframes titleGlowPulse {
        0% {
            text-shadow:
                3px 3px 0 rgba(255, 51, 102, 0.58),
                0 0 0 rgba(34, 211, 238, 0);
        }
        100% {
            text-shadow:
                3px 3px 0 rgba(255, 51, 102, 0.72),
                0 0 22px rgba(34, 211, 238, 0.34);
        }
    }

    @keyframes stickerFloatStrong {
        0% {
            transform: rotate(3deg) translateY(0px);
        }
        100% {
            transform: rotate(1deg) translateY(-8px);
        }
    }

    /* ===== HERO ===== */
    .hero-card {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        min-height: 390px;
        border-radius: 28px;
        border: 1px solid rgba(255, 255, 255, 0.16);
        backdrop-filter: blur(12px);
        background: linear-gradient(
            90deg,
            rgba(5, 8, 13, 0.88) 0%,
            rgba(5, 8, 13, 0.70) 55%,
            rgba(5, 8, 13, 0.42) 100%
        );
        backdrop-filter: blur(8px);
        padding: 3.2rem;
        margin-bottom: 3.5rem;
        animation: fadeUp 0.75s ease-out, heroBorderGlow 2.8s ease-in-out infinite alternate;
    }

    .hero-card::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(180deg, rgba(255,255,255,0.08), transparent 18%),
            radial-gradient(circle at 78% 42%, rgba(34,211,238,0.18), transparent 22%);
        pointer-events: none;
    }

    .hero-card::after {
        content: "";
        position: absolute;
        top: 0;
        left: -45%;
        width: 38%;
        height: 100%;
        z-index: 1;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(34, 211, 238, 0.20),
            rgba(255, 51, 102, 0.10),
            transparent
        );
        transform: skewX(-14deg);
        animation: heroScanLine 4.2s ease-in-out infinite;
        pointer-events: none;
    }

    .hero-content {
        position: relative;
        z-index: 2;
        max-width: 680px;
    }

    .hero-kicker {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: #67e8f9;
        font-size: 0.78rem;
        font-weight: 800;
        margin-bottom: 1.1rem;
    }

    .hero-title {
        font-size: clamp(2.8rem, 5vw, 5rem);
        line-height: 0.95;
        font-weight: 950;
        letter-spacing: -0.07em;
        color: #fafafa;
        text-transform: uppercase;
        margin-bottom: 1.1rem;
    }

    .hero-title span {
        color: #38bdf8;
        text-shadow: 3px 3px 0 rgba(255, 51, 102, 0.58);
        animation: titleGlowPulse 2.4s ease-in-out infinite alternate;
    }

    .hero-subtitle {
        color: #e5e7eb;
        font-size: 1.18rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 0.7rem;
    }

    .hero-desc {
        color: #a1a1aa;
        line-height: 1.65;
        font-size: 1rem;
        max-width: 650px;
    }

    .hero-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-top: 2rem;
    }

    .hero-tag {
        display: inline-flex;
        align-items: center;
        padding: 0.58rem 0.9rem;
        border: 1px solid rgba(255,255,255,0.20);
        background: rgba(0, 0, 0, 0.34);
        backdrop-filter: blur(8px);
        color: #f4f4f5;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.76rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .hero-tag.cyan {
        color: #67e8f9;
        border-color: rgba(34, 211, 238, 0.55);
    }

    .hero-tag.pink {
        color: #f9a8d4;
        border-color: rgba(244, 114, 182, 0.55);
    }

    .hero-tag.yellow {
        color: #fde047;
        border-color: rgba(253, 224, 71, 0.55);
    }

    .hero-sticker {
        position: absolute;
        top: 1.5rem;
        right: 1.8rem;
        z-index: 3;
        background: #fde047;
        color: #09090b;
        border: 2px solid #09090b;
        box-shadow: 5px 5px 0 rgba(0,0,0,0.65);
        padding: 0.55rem 1.1rem;
        transform: rotate(3deg);
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-weight: 950;
        letter-spacing: 0.08em;
        font-size: 0.72rem;
        text-transform: uppercase;
        animation: stickerFloatStrong 2.4s ease-in-out infinite alternate;
    }

    /* ===== SECTION TITLE ===== */
    .street-title-wrap {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 0 auto 2rem auto;
        animation: fadeUp 0.85s ease-out;
    }

    .street-title-wrap::before,
    .street-title-wrap::after {
        content: "";
        height: 1px;
        flex: 1;
        background: linear-gradient(90deg, transparent, rgba(244,244,245,0.24), transparent);
    }

    .street-title {
        text-align: center;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        text-transform: uppercase;
        letter-spacing: 0.24em;
        font-weight: 950;
        color: #f4f4f5;
        font-size: 1.05rem;
        white-space: nowrap;
    }

    .street-title span {
        color: #ff3366;
    }

    /* ===== ROLE CARDS ===== */
    .role-card {
        position: relative;
        isolation: isolate;
        background: linear-gradient(180deg, rgba(24,24,27,0.96), rgba(10,13,18,0.96));
        border: 1px solid rgba(244,244,245,0.14);
        min-height: 430px;
        padding: 1.55rem;
        overflow: hidden;
        box-shadow: 9px 9px 0 rgba(255,255,255,0.045), 0 18px 55px rgba(0,0,0,0.32);
        margin-bottom: 0.85rem;
        animation: fadeUp 0.95s ease-out;
        transition: all 0.18s ease;
    }

    .role-card:hover {
        transform: translateY(-7px);
        box-shadow: 12px 12px 0 rgba(255,255,255,0.06), 0 24px 70px rgba(0,0,0,0.42);
    }

    .role-card::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        height: 6px;
        width: 100%;
        background: var(--role-color);
    }

    .role-card::after {
        content: attr(data-index);
        position: absolute;
        top: 1.1rem;
        right: 1rem;
        color: rgba(255,255,255,0.055);
        font-size: 5rem;
        font-weight: 950;
        letter-spacing: -0.08em;
        line-height: 1;
    }

    .role-card > * {
        position: relative;
        z-index: 2;
    }

    .role-da {
        --role-color: #00e5ff;
        animation-delay: 0.08s;
        background:
            linear-gradient(
                180deg,
                rgba(5, 8, 13, 0.68) 0%,
                rgba(5, 8, 13, 0.84) 72%,
                rgba(5, 8, 13, 0.95) 100%
            ),
            __ROLE_DA_BG__;
        background-size: cover;
        background-position: center;
    }

    .role-de {
        --role-color: #ff7a1a;
        animation-delay: 0.18s;
        background:
            linear-gradient(
                180deg,
                rgba(5, 8, 13, 0.68) 0%,
                rgba(5, 8, 13, 0.84) 72%,
                rgba(5, 8, 13, 0.95) 100%
            ),
            __ROLE_DE_BG__;
        background-size: cover;
        background-position: right center;
    }

    .role-ds {
        --role-color: #a3ff12;
        animation-delay: 0.28s;
        background:
            linear-gradient(
                180deg,
                rgba(5, 8, 13, 0.68) 0%,
                rgba(5, 8, 13, 0.84) 72%,
                rgba(5, 8, 13, 0.95) 100%
            ),
            __ROLE_DS_BG__;
        background-size: cover;
        background-position: center;
    }

    .role-kicker {
        display: inline-block;
        color: #0a0a0a;
        background: #f4f4f5;
        padding: 0.34rem 0.58rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.62rem;
        font-weight: 950;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 2rem;
        transform: rotate(-1deg);
    }

    .role-number {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        color: var(--role-color);
        font-weight: 950;
        font-size: 0.82rem;
        letter-spacing: 0.16em;
        margin-bottom: 0.6rem;
    }

    .role-name {
        color: #fafafa;
        font-weight: 950;
        font-size: 1.55rem;
        line-height: 1;
        letter-spacing: -0.04em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .role-desc {
        color: #c4c4cc;
        line-height: 1.55;
        font-size: 0.9rem;
        min-height: 70px;
        margin-bottom: 1rem;
    }

    .mission-label {
        margin-top: 0.75rem;
        margin-bottom: 0.38rem;
        color: var(--role-color);
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.68rem;
        font-weight: 950;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .focus-list {
        display: grid;
        gap: 0.35rem;
        margin-bottom: 0.95rem;
    }

    .focus-list div {
        color: #d4d4d8;
        font-size: 0.82rem;
        padding-left: 0.75rem;
        border-left: 2px solid var(--role-color);
        background: rgba(255, 255, 255, 0.035);
        padding-top: 0.28rem;
        padding-bottom: 0.28rem;
    }

    .readiness-wrap {
        margin-top: 1.15rem;
    }

    .readiness-text {
        display: flex;
        justify-content: space-between;
        color: #a1a1aa;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.68rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }

    .pending-profile {
        color: #a1a1aa;
        font-size: 0.78rem;
        line-height: 1.45;
        padding: 0.65rem 0.75rem;
        border: 1px dashed rgba(255, 255, 255, 0.18);
        background: rgba(0, 0, 0, 0.22);
    }

    .readiness-bar {
        height: 8px;
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.12);
        overflow: hidden;
    }

    .readiness-fill {
        height: 100%;
        background: var(--role-color);
        box-shadow: 0 0 18px var(--role-color);
    }

    .readiness-da {
        width: 60%;
    }

    .readiness-de {
        width: 70%;
    }

    .readiness-ds {
        width: 65%;
    }

    .skill-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
    }

    .skill-tag {
        border: 1px solid var(--role-color);
        color: var(--role-color);
        padding: 0.36rem 0.58rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-weight: 900;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        background: rgba(255,255,255,0.02);
    }

    /* ===== STREAMLIT BUTTONS ===== */
    .stButton > button {
        border-radius: 0 !important;
        border: 1px solid rgba(244,244,245,0.22) !important;
        background: rgba(9, 9, 11, 0.92) !important;
        color: #fafafa !important;
        min-height: 3.15rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        box-shadow: 6px 6px 0 rgba(255,255,255,0.10);
        transition: all 0.14s ease;
    }

    .stButton > button:hover {
        transform: translate(-2px, -2px);
        border-color: #fde047 !important;
        color: #fde047 !important;
        box-shadow: 8px 8px 0 rgba(253,224,71,0.22);
    }

    .stButton > button:active {
        transform: translate(2px, 2px);
        box-shadow: 2px 2px 0 rgba(253,224,71,0.16);
    }

    /* ===== PIPELINE HOW IT WORKS ===== */
    .pipeline-board {
        margin-top: 3.4rem;
        padding-top: 2.2em;
        border-top: 1px solid rgba(244, 244, 245, 0.16);
        animation: fadeUp 1.05s ease-out;
    }

    .pipeline-header-row {
        display: flex;
        justify-content: space-between;
        gap: 2rem;
        align-items: flex-end;
        margin-bottom: 1.8rem;
    }

    .pipeline-title {
        color: #fafafa;
        font-size: 1.45rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .pipeline-subtitle {
        color: #b6b6c2;     
        max-width: 460px;
        line-height: 1.55;
        font-size: 0.9rem;
        text-align: right;
    }

    .pipeline-flow {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        position: relative;
    }

    .pipeline-step {
        position: relative;
        background: linear-gradient(180deg, rgba(18, 22, 30, 0.92), rgba(8, 10, 15, 0.96));
        border: 1px solid rgba(244, 244, 245, 0.13);
        padding: 1.25rem;
        min-height: 190px;
        overflow: hidden;
        box-shadow: 7px 7px 0 rgba(255,255,255,0.035);
        transition: all 0.18s ease;
        animation: fadeUp 0.9s ease-out both;
    }

    .pipeline-step:hover {
        transform: translateY(-5px);
        border-color: var(--step-color);
        box-shadow: 9px 9px 0 rgba(255,255,255,0.055), 0 0 24px rgba(255,255,255,0.035);
    }

    .pipeline-step::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(circle at 80% 18%, var(--step-glow), transparent 34%),
            linear-gradient(135deg, rgba(255,255,255,0.045), transparent 35%);
        pointer-events: none;
    }

    .pipeline-step::after {
        content: "→";
        position: absolute;
        right: -0.9rem;
        top: 50%;
        transform: translateY(-50%);
        color: var(--step-color);
        font-size: 1.6rem;
        font-weight: 950;
        z-index: 4;
        text-shadow: 0 0 16px var(--step-color);
    }

    .pipeline-step:last-child::after {
        display: none;
    }

    .pipeline-1 {
        --step-color: #00e5ff;
        --step-glow: rgba(0, 229, 255, 0.16);
        animation-delay: 0.08s;
    }

    .pipeline-2 {
        --step-color: #ff7a1a;
        --step-glow: rgba(255, 122, 26, 0.16);
        animation-delay: 0.16s;
    }

    .pipeline-3 {
        --step-color: #a3ff12;
        --step-glow: rgba(163, 255, 18, 0.14);
        animation-delay: 0.24s;
    }

    .pipeline-4 {
        --step-color: #ff3366;
        --step-glow: rgba(255, 51, 102, 0.16);
        animation-delay: 0.32s;
    }

    .pipeline-step > * {
        position: relative;
        z-index: 2;
    }

    .pipeline-no {
        color: var(--step-color);
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-weight: 950;
        font-size: 0.85rem;
        letter-spacing: 0.16em;
        margin-bottom: 1rem;
    }

    .pipeline-step-title {
        color: #f4f4f5;
        font-size: 1rem;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        line-height: 1.25;
        margin-bottom: 0.7rem;
    }

    .pipeline-desc {
        color: #a1a1aa;
        line-height: 1.5;
        font-size: 0.84rem;
        margin-bottom: 1rem;
    }

    .pipeline-chip {
        display: inline-block;
        color: var(--step-color);
        border: 1px solid var(--step-color);
        background: rgba(0, 0, 0, 0.24);
        padding: 0.32rem 0.5rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.64rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .pipeline-output {
        margin-top: 1.2rem;
        padding: 1rem 1.1rem;
        border: 1px dashed rgba(244, 244, 245, 0.18);
        background: rgba(0, 0, 0, 0.22);
        color: #d4d4d8;
        font-size: 0.86rem;
        line-height: 1.55;
    }

    .pipeline-output strong {
        color: #fde047;
    }

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: rgba(8,10,15,0.98);
        border-right: 1px solid rgba(244,244,245,0.09);
    }
    </style>
    """

    css = css.replace("__PAGE_BG__", page_background)
    css = css.replace("__HERO_BG__", hero_background)
    css = css.replace("__ROLE_DA_BG__", role_da_background)
    css = css.replace("__ROLE_DE_BG__", role_de_background)
    css = css.replace("__ROLE_DS_BG__", role_ds_background)

    st.markdown(dedent(css).strip(), unsafe_allow_html=True)

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