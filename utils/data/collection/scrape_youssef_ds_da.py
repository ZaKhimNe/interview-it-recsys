"""
Cào câu hỏi DS + DA từ youssefHosni/Data-Science-Interview-Questions-Answers
Format: ### Q1: question text ### \n Answer: ...\n\n### Q2: ...

Output: data/raw/question_bank/scraped_youssef.json

Chạy: python utils/data/collection/scrape_youssef_ds_da.py
"""
import re, json, requests
from datetime import date
from collections import Counter

BASE = "https://raw.githubusercontent.com/youssefHosni/Data-Science-Interview-Questions-Answers/main"

# (cap, role, skill_group, skill_tags)
FILES = {
    "Machine Learning Interview Questions %26 Answers for Data Scientists.md":
        (35, "DS", "ALGORITHM_THEORY",            ["ML_FUNDAMENTALS", "ML_CLASSIFICATION"]),
    "Deep Learning Questions %26 Answers for Data Scientists.md":
        (30, "DS", "DEEP_LEARNING",               ["DL_FUNDAMENTALS", "DL_OPTIMIZATION"]),
    "Statistics Interview Questions %26 Answers for Data Scientists.md":
        (30, "DA", "STATISTICS_EXPERIMENTATION",  ["STATS_FUNDAMENTALS", "STATS_HYPOTHESIS"]),
    "Probability Interview Questions %26 Answers for Data Scientists.md":
        (25, "DS", "EVALUATION_METRICS",          ["PROBABILITY", "STATS_FUNDAMENTALS"]),
    "Python Interview Questions %26 Answers for Data Scientists.md":
        (30, "DS", "PYTHON_ANALYTICS",            ["PYTHON_FUNDAMENTALS", "PYTHON_PANDAS"]),
    "SQL %26 DB Interview Questions %26 Answers for Data Scientists.md":
        (40, "DA", "SQL_DATABASE",                ["SQL_FUNDAMENTALS", "SQL_JOIN", "SQL_AGGREGATION"]),
}

CODING_KEYWORDS = ("write", "implement", "create", "query", "code", "script", "program")


def estimate_difficulty(text: str) -> tuple:
    t = text.lower()
    if any(k in t for k in ("design", "architect", "optimize", "tradeoff", "compare", "difference between")):
        return "HARD", 7
    if any(k in t for k in ("what is", "what are", "define", "list", "mention", "name")):
        return "EASY", 2
    return "MEDIUM", 5


def detect_type(q_text: str, answer: str, role: str, skill_group: str) -> str:
    has_code = "```" in answer
    is_coding = any(q_text.lower().startswith(kw) or f" {kw} " in q_text.lower()
                    for kw in CODING_KEYWORDS)
    if has_code or is_coding:
        return "CODING"
    if skill_group == "SQL_DATABASE":
        return "PRACTICE"
    return "THEORY"


def extract_eval_points(answer: str) -> list:
    clean = re.sub(r'```.*?```', '', answer, flags=re.DOTALL)
    clean = re.sub(r'!\[.*?\]\(.*?\)', '', clean)   # bỏ image markdown
    clean = re.sub(r'<[^>]+>', '', clean)
    bullets = re.findall(r'^\s*[*\-]\s+(.+)', clean, re.MULTILINE)
    if bullets:
        return [b.strip() for b in bullets[:3] if len(b.strip()) > 15]
    sentences = re.split(r'(?<=[.!?])\s+', clean.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 20][:3]


def parse_youssef_md(md: str, cap: int, role: str, skill_group: str, skill_tags: list) -> list:
    """
    Format:
      ### Q1: Question text? ###
      Answer:
      ...answer...

      ### Q2: ...
    """
    results = []

    # Tìm phần "Questions & Answers" — bỏ qua phần TOC ở đầu
    qa_start = md.find("## Questions & Answers ##")
    if qa_start == -1:
        qa_start = 0
    md = md[qa_start:]

    # Tách theo heading ### Q<số>:
    chunks = re.split(r'\n### Q\d+:', md)

    for chunk in chunks[1:]:
        if len(results) >= cap:
            break

        lines = chunk.strip().split('\n')
        # Dòng đầu: "question text ###" hoặc "question text"
        q_text = re.sub(r'\s*###\s*$', '', lines[0]).strip()
        if len(q_text) < 10:
            continue

        # Answer: phần còn lại, bỏ prefix "Answer:" nếu có
        body = '\n'.join(lines[1:]).strip()
        body = re.sub(r'^Answer:\s*', '', body, flags=re.IGNORECASE).strip()
        # Bỏ image-only answers
        body_no_img = re.sub(r'!\[.*?\]\(.*?\)', '', body).strip()
        if not body_no_img or len(body_no_img) < 20:
            continue

        diff_label, diff_score = estimate_difficulty(q_text)
        q_type = detect_type(q_text, body, role, skill_group)

        results.append({
            "q":    q_text,
            "role": role,
            "sg":   skill_group,
            "tags": skill_tags,
            "dl":   diff_label,
            "ds":   diff_score,
            "type": q_type,
            "ans":  body,
        })

    return results


def to_schema(raw: dict, idx: int, filename: str) -> dict:
    role = raw["role"]
    return {
        "question_id":      f"{role}_YH_{idx:03d}",
        "question_text":    raw["q"],
        "roles":            {"primary": role, "secondary": []},
        "difficulty_label": raw["dl"],
        "difficulty_score": raw["ds"],
        "question_type":    raw["type"],
        "skill_groups":     [raw["sg"]],
        "skill_tags":       raw["tags"],
        "answers": {
            "detailed":          raw["ans"],
            "evaluation_points": extract_eval_points(raw["ans"]),
        },
        "metadata": {
            "language":   "en",
            "source":     f"youssefHosni/Data-Science-Interview-Questions-Answers/{filename}",
            "version":    "v1.0",
            "created_at": str(date.today()),
        }
    }


if __name__ == "__main__":
    import os
    all_raw = []

    for filename, (cap, role, sg, tags) in FILES.items():
        url = f"{BASE}/{filename}"
        print(f"Fetching {filename[:50]}...")
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            parsed = parse_youssef_md(resp.text, cap, role, sg, tags)
            print(f"  -> {len(parsed)} questions [{sg}] ({role})")
            all_raw.extend([(r, filename) for r in parsed])
        except Exception as e:
            print(f"  !! FAILED: {e}")

    questions = [to_schema(r, i + 1, fn) for i, (r, fn) in enumerate(all_raw)]

    print("\n── Stats ──────────────────────────")
    print("Total:  ", len(questions))
    print("Roles:  ", dict(Counter(q["roles"]["primary"] for q in questions)))
    print("Types:  ", dict(Counter(q["question_type"] for q in questions)))
    print("Diff:   ", dict(Counter(q["difficulty_label"] for q in questions)))
    print("Groups: ", dict(Counter(q["skill_groups"][0] for q in questions)))

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/question_bank/scraped_youssef.json", "w", encoding="utf-8") as f:
        json.dump({"questions": questions}, f, ensure_ascii=False, indent=2)
    print("\nSaved -> data/raw/question_bank/scraped_youssef.json")
