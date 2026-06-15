"""
AI Tech Interview Prep -- InternHub
Run: streamlit run app.py
"""

import json
import os
import shutil
from pathlib import Path

import streamlit as st

from src.data_loader import load_question_bank, get_radar_profile_data

ROOT_DIR     = Path(__file__).parent
FRONTEND_DIR = ROOT_DIR / "app" / "frontend"
STATIC_DIR   = ROOT_DIR / "app" / "static"

JSX_ORDER = [
    "state.jsx",
    "chrome.jsx",
    "widgets.jsx",
    "screens-public.jsx",
    "screens-practice.jsx",
    "screens-progress.jsx",
    "screens-social.jsx",
    "screens-diagnostic.jsx",
    "router.jsx",
]

CSS_VARS = """:root {
  --bg-0:#05080d;--bg-1:#080a0f;--bg-2:#0d1018;--bg-3:#131620;--bg-4:#1c1f2e;
  --fg-0:#f4f4f5;--fg-1:#d4d4d8;--fg-2:#b4b4bc;
  --fg-3:#9a9aa6;--fg-4:#7e7e8a;--fg-5:#636370;--fg-6:#505060;
  --accent-cyan:#00e5ff;--accent-orange:#ff7a1a;
  --accent-green:#a3ff12;--accent-pink:#ff3366;
  --accent-warn:#fde047;--accent-hot:#ff3366;
  --success:#a3ff12;--warn:#fde047;--danger:#ff3366;
  --line-soft:rgba(244,244,245,0.08);--line-med:rgba(244,244,245,0.14);
  --line:rgba(244,244,245,0.10);--line-strong:rgba(244,244,245,0.20);
  --ease-out:cubic-bezier(0.22,1,0.36,1);
  --font-sans:'Inter',system-ui,sans-serif;
  --font-mono:'JetBrains Mono','Fira Code',monospace;
  --font-body:'Inter',system-ui,sans-serif;
}
"""

_DIFFICULTY_MAP = {"EASY": "BEGINNER", "MEDIUM": "INTERMEDIATE", "HARD": "ADVANCED"}
_EST_MIN_MAP    = {"EASY": 5, "MEDIUM": 8, "HARD": 15}
_SCALE          = 2.0  # Python 0-5, React 0-10


def _map_question(q: dict) -> dict:
    """Map one question from Python -> React format."""
    text = q.get("question_text", "")
    role = q.get("roles", {}).get("primary", "DA")
    diff = q.get("difficulty_label", "MEDIUM")
    answers = q.get("answers", {})
    expert = answers.get("detailed", "")
    points = answers.get("evaluation_points", [])
    expert_full = expert
    if points:
        expert_full += "\n\n" + "\n".join(f"- {p}" for p in points)
    # Fallback cho MC_SINGLE / TRUE_FALSE / FILL_BLANK: dùng explanation nếu không có detailed
    if not expert_full.strip():
        expert_full = answers.get("explanation", "")

    mapped: dict = {
        "id":            q.get("question_id", ""),
        "role":          role,
        "tags":          q.get("skill_tags", []),
        "skillGroups":   q.get("skill_groups", []),
        "difficulty":    _DIFFICULTY_MAP.get(diff, "INTERMEDIATE"),
        "difficultyScore": q.get("difficulty_score", 5),
        "estMin":        _EST_MIN_MAP.get(diff, 8),
        "questionType":  q.get("question_type", "THEORY"),
        "title_vi":      text,
        "title_en":      text,
        "body_vi":       text,
        "body_en":       text,
        "expert_vi":     expert_full,
        "expert_en":     expert_full,
    }

    qtype = q.get("question_type", "THEORY")

    # MC_SINGLE
    if q.get("options") is not None:
        mapped["options"] = q["options"]
        mapped["correctOptionId"] = answers.get("correct_option_id", "")
        mapped["explanation"] = answers.get("explanation", "")

    # TRUE_FALSE
    if qtype == "TRUE_FALSE":
        mapped["correctAnswer"] = answers.get("correct_answer")
        mapped["explanation"] = answers.get("explanation", "")

    # FILL_BLANK
    if q.get("template") is not None:
        mapped["template"] = q["template"]
        mapped["acceptedAnswers"] = answers.get("accepted_answers", [])
        mapped["explanation"] = answers.get("explanation", "")

    # CODING_EXERCISE / CODING with starter code
    if q.get("test_cases") is not None:
        mapped["testCases"] = q["test_cases"]
    if q.get("starter_code") is not None:
        mapped["starterCode"] = q["starter_code"]
    if q.get("constraints") is not None:
        mapped["constraints"] = q["constraints"]
    if q.get("allowed_languages") is not None:
        mapped["allowedLanguages"] = q["allowed_languages"]

    return mapped


def build_project_data() -> dict:
    raw_questions = load_question_bank()
    questions = [_map_question(q) for q in raw_questions]

    skill_axes   = {}
    role_targets = {}
    role_radars  = {}

    for role in ("DA", "DE", "DS"):
        radar = get_radar_profile_data(role)
        labels  = radar.get("labels", [])
        current = [round(v * _SCALE, 2) for v in radar.get("current_values", [])]
        target  = [round(v * _SCALE, 2) for v in radar.get("target_values", [])]

        skill_axes[role]   = labels
        role_targets[role] = target
        if current:
            role_radars[role] = {
                "skill_keys": radar.get("skill_keys", []),
                "current":    current,
                "target":     target,
            }

    return {
        "questions":   questions,
        "skillAxes":   skill_axes,
        "roleTargets": role_targets,
        "roleRadars":  role_radars,
    }


_PROJECT_DATA: dict = {}


def get_project_data() -> dict:
    global _PROJECT_DATA
    if not _PROJECT_DATA:
        try:
            _PROJECT_DATA = build_project_data()
        except Exception as e:
            print(f"[app] Warning: could not load project data: {e}")
            _PROJECT_DATA = {}
    return _PROJECT_DATA


def prepare_static(project_data: dict):
    STATIC_DIR.mkdir(exist_ok=True)

    src_assets = ROOT_DIR / "assets"
    dst_assets = STATIC_DIR / "assets"
    dst_assets.mkdir(exist_ok=True)
    for img in src_assets.glob("*.png"):
        dst = dst_assets / img.name
        if not dst.exists() or img.stat().st_mtime > dst.stat().st_mtime:
            shutil.copy2(img, dst)

    for fname in JSX_ORDER:
        src = FRONTEND_DIR / fname
        dst = STATIC_DIR / fname
        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
            content = src.read_text(encoding="utf-8")
            content = content.replace("../assets/", "assets/")
            dst.write_text(content, encoding="utf-8")

    build_v = int(max(
        (FRONTEND_DIR / f).stat().st_mtime
        for f in JSX_ORDER if (FRONTEND_DIR / f).exists()
    ))
    scripts_tags = "\n".join(
        f'  <script type="text/babel" src="{f}?v={build_v}"></script>'
        for f in JSX_ORDER
    )
    raw_css = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")
    css_clean = "\n".join(
        line for line in raw_css.splitlines()
        if not line.strip().startswith("@import")
    )
    data_json = json.dumps(project_data, ensure_ascii=False)

    html_parts = [
        '<!doctype html>',
        '<html lang="en">',
        '<head>',
        '  <meta charset="utf-8" />',
        '  <meta name="viewport" content="width=1280" />',
        '  <title>InternHub</title>',
        '  <link rel="preconnect" href="https://fonts.googleapis.com" />',
        '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap" />',
        f'  <style>{CSS_VARS}{css_clean}</style>',
        '  <script src="https://unpkg.com/react@18.3.1/umd/react.development.js" crossorigin="anonymous"></script>',
        '  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" crossorigin="anonymous"></script>',
        '  <script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin="anonymous"></script>',
        '</head>',
        '<body>',
        '  <div id="root"></div>',
        f'  <script>window.__INTERNHUB_DATA__ = {data_json};</script>',
        scripts_tags,
        '  <script type="text/babel">',
        "    requestAnimationFrame(() => requestAnimationFrame(() => {",
        "      ReactDOM.createRoot(document.getElementById('root')).render(<App />);",
        "    }));",
        '  </script>',
        '</body>',
        '</html>',
    ]
    html = "\n".join(html_parts)

    (STATIC_DIR / "index.html").write_text(html, encoding="utf-8")
    return build_v


def main():
    st.set_page_config(
        page_title="InternHub",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown("""
        <style>
        #MainMenu, header, footer { display: none !important; }
        .block-container { padding: 0 !important; max-width: 100% !important; }
        [data-testid="stAppViewContainer"] { padding: 0 !important; }
        [data-testid="stVerticalBlock"] { gap: 0 !important; }
        </style>
    """, unsafe_allow_html=True)

    project_data = get_project_data()
    build_ver = prepare_static(project_data)

    port = os.environ.get("STREAMLIT_SERVER_PORT", "8501")
    app_url = f"http://localhost:{port}/app/static/index.html?v={build_ver}"

    st.markdown(
        f'<iframe src="{app_url}" style="width:100%;height:100vh;border:none;display:block;" '
        f'allow="clipboard-read; clipboard-write"></iframe>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
