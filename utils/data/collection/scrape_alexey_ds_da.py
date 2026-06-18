"""
Pipeline cào câu hỏi từ alexeygrigorev/data-science-interviews
Output: data/raw/question_bank/scraped_github.json

Chạy: python utils/data/collection/scrape_github_interviews.py
"""
import re, json, requests
from datetime import date
from collections import Counter

# ── Config ──────────────────────────────────────────────────────────────
BASE_URL = "https://raw.githubusercontent.com/alexeygrigorev/data-science-interviews/master"
FILES = {
    "theory":    f"{BASE_URL}/theory.md",
    "technical": f"{BASE_URL}/technical.md",
}

# ── Map section → (role, skill_group, skill_tags) ───────────────────────
SECTION_MAP = {
    "supervised machine learning":        ("DS", "ALGORITHM_THEORY",     ["ML_FUNDAMENTALS"]),
    "linear regression":                  ("DS", "ALGORITHM_THEORY",     ["ML_LINEAR_REGRESSION"]),
    "validation":                         ("DS", "EVALUATION_METRICS",   ["EVAL_CROSS_VALIDATION"]),
    "classification":                     ("DS", "ALGORITHM_THEORY",     ["ML_CLASSIFICATION"]),
    "regularization":                     ("DS", "ALGORITHM_THEORY",     ["ML_REGULARIZATION"]),
    "feature selection":                  ("DS", "DATA_PREPROCESSING",   ["FEATURE_ENGINEERING"]),
    "decision trees":                     ("DS", "ALGORITHM_THEORY",     ["ML_DECISION_TREE"]),
    "random forest":                      ("DS", "ALGORITHM_THEORY",     ["ML_ENSEMBLE"]),
    "gradient boosting":                  ("DS", "ALGORITHM_THEORY",     ["ML_ENSEMBLE"]),
    "parameter tuning":                   ("DS", "EVALUATION_METRICS",   ["ML_HYPERPARAMETER_TUNING"]),
    "neural networks":                    ("DS", "DEEP_LEARNING",        ["DL_FUNDAMENTALS"]),
    "optimization in neural networks":    ("DS", "DEEP_LEARNING",        ["DL_OPTIMIZATION"]),
    "neural networks for computer vision":("DS", "DEEP_LEARNING",        ["DL_CNN"]),
    "text classification":                ("DS", "NLP",                  ["NLP_TEXT_CLASSIFICATION"]),
    "clustering":                         ("DS", "ALGORITHM_THEORY",     ["ML_CLUSTERING"]),
    "dimensionality reduction":           ("DS", "DATA_PREPROCESSING",   ["ML_DIMENSIONALITY_REDUCTION"]),
    "ranking and search":                 ("DS", "ALGORITHM_THEORY",     ["ML_RANKING"]),
    "recommender systems":                ("DS", "ALGORITHM_THEORY",     ["ML_RECOMMENDER"]),
    "time series":                        ("DS", "TIME_SERIES",          ["TS_FUNDAMENTALS"]),
    # technical.md
    "sql":                                ("DA", "SQL_DATABASE",         ["SQL_FUNDAMENTALS","SQL_JOIN","SQL_AGGREGATION"]),
    "coding (python)":                    ("DS", "PYTHON_ANALYTICS",     ["PYTHON_PANDAS","PYTHON_FUNDAMENTALS"]),
    "algorithmic questions":              ("DS", "ALGORITHM_THEORY",     ["ALGORITHM_DS","ALGORITHM_SEARCHING"]),
}

DIFFICULTY_EMOJI = {
    "\U0001f476": ("EASY",   2),   # 👶
    "⭐️": ("MEDIUM", 5), # ⭐️
    "\U0001f680": ("EXPERT", 9),   # 🚀
}
DEFAULT_DIFF = ("MEDIUM", 5)


def detect_difficulty(text: str):
    for emoji, val in DIFFICULTY_EMOJI.items():
        if emoji in text:
            return val, text.replace(emoji, "").strip()
    return DEFAULT_DIFF, text.strip()


def detect_type(q_text: str, section: str, has_code: bool) -> str:
    if has_code:
        return "CODING"
    if section in ("sql",):
        return "PRACTICE"
    if any(w in q_text.lower() for w in ("implement", "write", "calculate", "compute")):
        return "CODING"
    return "THEORY"


def extract_eval_points(answer: str) -> list:
    clean = re.sub(r'```.*?```', '', answer, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', '', clean)
    sentences = re.split(r'(?<=[.!?])\s+', clean.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 20][:3]


# Cap số câu mỗi section trong theory.md
# ALGORITHM_THEORY có 11 sections → giới hạn để không chiếm quá nhiều
SECTION_CAPS = {
    # ALGORITHM_THEORY sections (mỗi cái ~5 câu để trải đều sub-topic)
    "supervised machine learning": 5,
    "linear regression":           4,
    "classification":              5,
    "regularization":              4,
    "decision trees":              5,
    "random forest":               4,
    "gradient boosting":           4,
    "clustering":                  5,
    "ranking and search":          4,
    "recommender systems":         4,
    "algorithmic questions":       5,
    # Các group khác đã ít, giữ nguyên tất cả
    "validation":                  99,
    "feature selection":           99,
    "parameter tuning":            99,
    "neural networks":             99,
    "optimization in neural networks": 99,
    "neural networks for computer vision": 99,
    "text classification":         99,
    "dimensionality reduction":    99,
    "time series":                 99,
}


def parse_theory_md(md: str) -> list:
    """
    theory.md format: **Question text? 👶**\n\nAnswer...
    Bold text IS the question.
    """
    results = []
    section_counts: dict = {}

    blocks = re.split(r'\n## ', md)
    for block in blocks[1:]:
        lines = block.strip().split('\n')
        section_title = re.sub(r'<[^>]+>', '', lines[0]).strip().lower()
        role, skill_group, skill_tags = SECTION_MAP.get(
            section_title, ("DS", "ALGORITHM_THEORY", ["ML_FUNDAMENTALS"])
        )
        # Section không có trong SECTION_MAP → mặc định ALGORITHM_THEORY, giới hạn 5
        default_cap = 5 if section_title not in SECTION_MAP else 99
        cap = SECTION_CAPS.get(section_title, default_cap)
        content = '\n'.join(lines[1:])

        pattern = re.compile(r'\*\*(.+?)\*\*', re.DOTALL)
        matches = list(pattern.finditer(content))

        for i, m in enumerate(matches):
            if section_counts.get(section_title, 0) >= cap:
                break

            q_raw = m.group(1).strip()
            if len(q_raw) < 10:
                continue
            (diff_label, diff_score), q_clean = detect_difficulty(q_raw)

            start = m.end()
            end   = matches[i+1].start() if i+1 < len(matches) else len(content)
            answer_raw = content[start:end].strip()
            answer_clean = re.sub(r'<[^>]+>', '', answer_raw).strip()
            answer_clean = re.sub(r'\n{3,}', '\n\n', answer_clean).strip()
            if not answer_clean or len(answer_clean) < 10:
                continue

            has_code = '```' in answer_clean
            q_type = detect_type(q_clean, section_title, has_code)

            results.append({
                "question_text":    q_clean,
                "role":             role,
                "skill_group":      skill_group,
                "skill_tags":       skill_tags,
                "difficulty_label": diff_label,
                "difficulty_score": diff_score,
                "question_type":    q_type,
                "answer_detailed":  answer_clean,
                "section":          section_title,
            })
            section_counts[section_title] = section_counts.get(section_title, 0) + 1
    return results


def parse_technical_md(md: str) -> list:
    """
    technical.md format: **N)** Question text  (hoặc **N) Title.**)
    Bold text chỉ chứa số thứ tự → câu hỏi thật nằm SAU bold.

    Patterns gặp trong file:
      SQL:    **1)** The number of active ads.\n\n```sql\nSEL...\n```
      Python: **1) FizzBuzz.**  Write a function...\n\n```python\n...\n```
      Algo:   **1) Two sum.**   Given an array...\n\n```python\n...\n```
    """
    results = []
    blocks = re.split(r'\n## ', md)
    for block in blocks[1:]:
        lines = block.strip().split('\n')
        section_title = re.sub(r'<[^>]+>', '', lines[0]).strip().lower()
        if "table of contents" in section_title:
            continue
        role, skill_group, skill_tags = SECTION_MAP.get(
            section_title, ("DS", "ALGORITHM_THEORY", ["ML_FUNDAMENTALS"])
        )
        content = '\n'.join(lines[1:])

        # Tách theo pattern **N)  hoặc **N) Title.**
        # Group 1 = optional title (phần trong ** sau số)
        # Group 2 = phần còn lại
        chunks = re.split(r'\*\*\d+\)\s*', content)
        for chunk in chunks[1:]:
            # Phần đầu chunk: "Title.** body" hoặc "** body"
            # Cắt tại ** đóng
            m = re.match(r'([^*\n]*?)\*\*\s*\n?(.*)', chunk, re.DOTALL)
            if not m:
                continue
            title_part = m.group(1).strip(' .*')
            body = m.group(2).strip()

            if not body or len(body) < 15:
                continue

            # Xác định question_text
            if len(title_part) >= 5:
                # Title nằm trong ** (VD: "FizzBuzz"), body là description + code
                q_text = title_part.rstrip('.')
            else:
                # SQL case: không có title, dòng đầu body là câu hỏi
                first_line = body.split('\n')[0].strip()
                q_text = first_line
                # body giữ nguyên (câu hỏi + code bên dưới)

            if len(q_text) < 5:
                continue

            has_code = '```' in body
            q_type = detect_type(q_text, section_title, has_code)

            results.append({
                "question_text":    q_text,
                "role":             role,
                "skill_group":      skill_group,
                "skill_tags":       skill_tags,
                "difficulty_label": "MEDIUM",
                "difficulty_score": 5,
                "question_type":    q_type,
                "answer_detailed":  body,
                "section":          section_title,
            })
    return results


def parse_md(md: str, file_key: str) -> list:
    """Dispatcher: chọn parser phù hợp theo file."""
    if file_key == "technical":
        return parse_technical_md(md)
    return parse_theory_md(md)


def to_schema(raw: dict, idx: int) -> dict:
    role = raw["role"]
    return {
        "question_id":      f"{role}_GH_{idx:03d}",
        "question_text":    raw["question_text"],
        "roles":            {"primary": role, "secondary": []},
        "difficulty_label": raw["difficulty_label"],
        "difficulty_score": raw["difficulty_score"],
        "question_type":    raw["question_type"],
        "skill_groups":     [raw["skill_group"]],
        "skill_tags":       raw["skill_tags"],
        "answers": {
            "detailed":          raw["answer_detailed"],
            "evaluation_points": extract_eval_points(raw["answer_detailed"]),
        },
        "metadata": {
            "language":   "en",
            "source":     "alexeygrigorev/data-science-interviews",
            "version":    "v1.0",
            "created_at": str(date.today()),
        }
    }


if __name__ == "__main__":
    import os
    all_raw = []
    for key, url in FILES.items():
        print(f"Fetching {key}.md ...")
        md = requests.get(url, timeout=20).text
        parsed = parse_md(md, key)
        print(f"  -> {len(parsed)} questions parsed")
        all_raw.extend(parsed)

    questions = [to_schema(r, i+1) for i, r in enumerate(all_raw)]

    print("\n── Stats ──────────────────────────")
    print("Total:  ", len(questions))
    print("Roles:  ", dict(Counter(q["roles"]["primary"] for q in questions)))
    print("Types:  ", dict(Counter(q["question_type"] for q in questions)))
    print("Diff:   ", dict(Counter(q["difficulty_label"] for q in questions)))
    print("Groups: ", dict(Counter(q["skill_groups"][0] for q in questions)))

    os.makedirs("data/raw", exist_ok=True)
    out = "data/raw/question_bank/scraped_github.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"questions": questions}, f, ensure_ascii=False, indent=2)
    print(f"\nSaved -> {out}")
    print("Next: chạy scripts/validate_and_merge.py để merge vào question bank")
