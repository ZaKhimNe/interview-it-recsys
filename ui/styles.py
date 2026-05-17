import base64
from pathlib import Path
from textwrap import dedent

import streamlit as st

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