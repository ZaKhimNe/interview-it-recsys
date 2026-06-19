"""
AI Tech Interview Prep -- InternHub
Run: streamlit run app.py
"""

import json
import os
import shutil
from pathlib import Path

import streamlit as st

from src.data.data_loader import load_question_bank, get_radar_profile_data
from src.api.serving import start_server, API_PORT


def _make_favicon():
    """Tạo PIL Image favicon từ SVG radar icon."""
    try:
        from PIL import Image, ImageDraw
        import math
        SIZE = 64
        img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = SIZE // 2, SIZE // 2

        def hex_pts(r, cx=cx, cy=cy):
            return [(cx + r * math.cos(math.radians(a - 90)),
                     cy + r * math.sin(math.radians(a - 90)))
                    for a in range(0, 360, 60)]

        # Hexagon rings
        for r in (30, 20, 12):
            draw.polygon(hex_pts(r), outline=(226, 232, 240, 100), fill=None)
        # Axes
        for pt in hex_pts(30):
            draw.line([(cx, cy), pt], fill=(226, 232, 240, 80), width=1)
        # Radar fill polygon
        data_pts = [(cx, cy-28), (cx+20, cy-10), (cx+23, cy+18),
                    (cx, cy+24), (cx-18, cy+10), (cx-18, cy-22)]
        draw.polygon(data_pts, fill=(59, 130, 246, 55), outline=(16, 185, 129, 220), width=2)
        # Dots
        dots = [(cx, cy-28, "#3b82f6"), (cx+20, cy-10, "#4f8fe8"),
                (cx+23, cy+18, "#5ec1b0"), (cx, cy+24, "#10b981"),
                (cx-18, cy+10, "#10b981"), (cx-18, cy-22, "#3b82f6")]
        for x, y, col in dots:
            r2 = 4
            draw.ellipse([x-r2, y-r2, x+r2, y+r2], fill=col)
        return img
    except Exception:
        return "🎯"

ROOT_DIR     = Path(__file__).parent
FRONTEND_DIR = ROOT_DIR / "app" / "frontend"
STATIC_DIR   = ROOT_DIR / "static"

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

import re as _re
def _infer_correct_answer(detailed: str):
    """Parse correct_answer from detailed text like '✓ True.' or '✗ False.'"""
    if not detailed:
        return None
    m = _re.search(r'[✓☑]\s*(True)', detailed, _re.IGNORECASE)
    if m:
        return True
    m = _re.search(r'[✗☒]\s*(False)', detailed, _re.IGNORECASE)
    if m:
        return False
    m = _re.match(r'\s*True[\.\s]', detailed, _re.IGNORECASE)
    if m:
        return True
    m = _re.match(r'\s*False[\.\s]', detailed, _re.IGNORECASE)
    if m:
        return False
    return None


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

    # Tach question_text -> title (dong dau ngan) + body (de bai). Neu khong co
    # title ngan thi de title rong, chi render body markdown.
    title_text, body_text = "", text
    if "\n\n" in text:
        head, rest = text.split("\n\n", 1)
        if "\n" not in head and len(head) <= 80:
            title_text, body_text = head.strip(), rest.strip()

    mapped: dict = {
        "id":            q.get("question_id", ""),
        "role":          role,
        "tags":          q.get("skill_tags", []),
        "skillGroups":   q.get("skill_groups", []),
        "difficulty":    _DIFFICULTY_MAP.get(diff, "INTERMEDIATE"),
        "difficultyScore": q.get("difficulty_score", 5),
        "estMin":        _EST_MIN_MAP.get(diff, 8),
        "questionType":  q.get("question_type", "THEORY"),
        "title_vi":      title_text,
        "title_en":      title_text,
        "body_vi":       body_text,
        "body_en":       body_text,
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
        ca = answers.get("correct_answer")
        if ca is None:
            ca = _infer_correct_answer(answers.get("detailed", "") or "")
        mapped["correctAnswer"] = ca
        mapped["explanation"] = answers.get("explanation", "") or answers.get("detailed", "")

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

    src_assets = ROOT_DIR / "app" / "assets"
    dst_assets = STATIC_DIR / "assets"
    dst_assets.mkdir(exist_ok=True)
    for img in list(src_assets.glob("*.png")) + list(src_assets.glob("*.svg")):
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
        '  <link rel="icon" type="image/svg+xml" href="assets/icon-radar.svg" />',
        '  <link rel="preconnect" href="https://fonts.googleapis.com" />',
        '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap" />',
        f'  <style>{CSS_VARS}{css_clean}</style>',
        '  <script src="https://unpkg.com/react@18.3.1/umd/react.development.js" crossorigin="anonymous"></script>',
        '  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" crossorigin="anonymous"></script>',
        '  <script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin="anonymous"></script>',
        '  <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js" crossorigin="anonymous"></script>',
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
        page_icon=_make_favicon(),
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(f"""
        <style>
        #MainMenu, header, footer {{ display: none !important; }}
        .block-container {{ padding: 0 !important; max-width: 100% !important; }}
        [data-testid="stAppViewContainer"] {{ padding: 0 !important; }}
        [data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
        </style>
        <script>
        (function() {{
            document.querySelectorAll("link[rel*='icon']").forEach(e => e.remove());
            var lnk = document.createElement('link');
            lnk.rel = 'icon'; lnk.type = 'image/svg+xml';
            lnk.href = 'http://localhost:{API_PORT}/ui/assets/icon-radar.svg';
            document.head.appendChild(lnk);
        }})();
        </script>
    """, unsafe_allow_html=True)

    start_server()   # FastAPI on :8000 in background thread (no-op if already running)

    project_data = get_project_data()
    build_ver = prepare_static(project_data)

    app_url = f"http://localhost:{API_PORT}/ui/index.html?v={build_ver}"

    st.markdown(
        f'<iframe src="{app_url}" style="width:100%;height:100vh;border:none;display:block;" '
        f'allow="clipboard-read; clipboard-write"></iframe>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
