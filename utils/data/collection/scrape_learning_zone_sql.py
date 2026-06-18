"""
Cào câu hỏi DA/SQL từ learning-zone/sql-interview-questions
3 file với 3 format khác nhau:
  - README.md           → THEORY + CODING   (## Q. question?)
  - sql-query-practice.md → PRACTICE/CODING (## Q. Write SQL... + <details> answer)
  - sql-mcq.md          → MC_SINGLE         (**Q.** + options + > Answer: X)

Output: data/raw/question_bank/scraped_sql.json
Chạy:  python utils/data/collection/scrape_learning_zone_sql.py
"""
import re, json, requests
from datetime import date
from collections import Counter

BASE = "https://raw.githubusercontent.com/learning-zone/sql-interview-questions/master"

# (cap, question_type_override_or_None)
FILES = {
    "README.md":              (60,  None),         # type detect tự động
    "sql-query-practice.md":  (50,  "PRACTICE"),   # toàn bộ là bài thực hành
    "sql-mcq.md":             (40,  "MC_SINGLE"),  # multiple choice
}

ROLE       = "DA"
SKILL_GROUP = "SQL_DATABASE"
SKILL_TAGS  = ["SQL_FUNDAMENTALS", "SQL_JOIN", "SQL_AGGREGATION", "SQL_WINDOW_FUNCTION"]


# ── Difficulty ───────────────────────────────────────────────────────────
def estimate_difficulty(text: str) -> tuple:
    t = text.lower()
    if any(k in t for k in ("recursive", "pivot", "window function", "cte",
                             "optimize", "index", "execution plan", "partition",
                             "merge", "upsert", "hierarchy", "median")):
        return "HARD", 7
    if any(k in t for k in ("what is", "what are", "define", "explain",
                             "list", "difference between", "types of")):
        return "EASY", 2
    return "MEDIUM", 5


def detect_type(q_text: str, answer: str, override=None) -> str:
    if override:
        return override
    has_code = "```" in answer
    is_write = any(q_text.lower().startswith(k) or f" {k} " in q_text.lower()
                   for k in ("write", "create", "implement", "query", "find using"))
    if has_code and is_write:
        return "PRACTICE"
    if has_code:
        return "CODING"
    return "THEORY"


def clean_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)        # image markdown
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)         # link markdown
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_eval_points(answer: str) -> list:
    clean = re.sub(r'```.*?```', '', answer, flags=re.DOTALL)
    clean = clean_html(clean)
    bullets = re.findall(r'^\s*[*\-]\s+(.+)', clean, re.MULTILINE)
    if bullets:
        return [b.strip() for b in bullets[:3] if len(b.strip()) > 15]
    sentences = re.split(r'(?<=[.!?])\s+', clean.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 20][:3]


# ── Parser 1: README.md — ## Q. question? ──────────────────────────────
def parse_readme(md: str, cap: int, type_override) -> list:
    results = []
    chunks = re.split(r'\n## Q\. ', md)
    for chunk in chunks[1:]:
        if len(results) >= cap:
            break
        lines = chunk.strip().split('\n')
        q_text = lines[0].strip().rstrip('?').strip() + '?'
        if len(q_text) < 15:
            continue

        answer = '\n'.join(lines[1:]).strip()
        # Bỏ "back to top" nav links
        answer = re.sub(r'<div align.*?</div>', '', answer, flags=re.DOTALL)
        answer = clean_html(answer)
        if not answer or len(answer) < 20:
            continue

        diff_label, diff_score = estimate_difficulty(q_text)
        q_type = detect_type(q_text, answer, type_override)
        results.append(_build(q_text, answer, diff_label, diff_score, q_type))
    return results


# ── Parser 2: sql-query-practice.md — answer trong <details> ───────────
def parse_practice(md: str, cap: int, type_override) -> list:
    results = []
    chunks = re.split(r'\n## Q\. ', md)
    for chunk in chunks[1:]:
        if len(results) >= cap:
            break
        lines = chunk.strip().split('\n')
        q_text = lines[0].strip()
        if len(q_text) < 10:
            continue

        body = '\n'.join(lines[1:])

        # Lấy answer từ <details>...</details>
        detail_match = re.search(r'<details[^>]*>(.*?)</details>', body, re.DOTALL)
        if detail_match:
            answer = detail_match.group(1)
            # Bỏ <summary> tag
            answer = re.sub(r'<summary>.*?</summary>', '', answer, flags=re.DOTALL)
            answer = clean_html(answer).strip()
        else:
            # Không có <details>, lấy toàn bộ body (code blocks)
            answer = clean_html(body).strip()

        if not answer or len(answer) < 20:
            continue

        diff_label, diff_score = estimate_difficulty(q_text)
        q_type = type_override or "PRACTICE"
        results.append(_build(q_text, answer, diff_label, diff_score, q_type))
    return results


# ── Parser 3: sql-mcq.md — **Q.** + options + > Answer ─────────────────
def parse_mcq(md: str, cap: int, type_override) -> list:
    results = []
    # Tách theo \n\n**Q.**
    chunks = re.split(r'\n\n\*\*Q\.\*\*\s*', md)
    for chunk in chunks[1:]:
        if len(results) >= cap:
            break

        # Question text = phần trước options (trước "- A)")
        parts = re.split(r'\n- [A-D]\)', chunk, maxsplit=1)
        q_text = parts[0].strip()
        # Bỏ code block trong question nếu có, giữ lại như context
        q_text = re.sub(r'```.*?```', '', q_text, flags=re.DOTALL).strip()
        q_text = clean_html(q_text)
        if len(q_text) < 10:
            continue

        rest = chunk[len(parts[0]):]

        # Lấy options
        options = re.findall(r'- ([A-D])\)\s*(.+)', rest)

        # Lấy answer + explanation
        ans_match = re.search(r'>\s*\*\*Answer:\s*([A-D])\*\*(.*?)(?=\n\n|\Z)', rest, re.DOTALL)
        if not ans_match:
            continue
        correct = ans_match.group(1)
        explanation = clean_html(ans_match.group(2)).strip()

        # Build answer text
        options_text = '\n'.join(f"{k}) {v}" for k, v in options)
        answer = f"Correct: {correct}\n{options_text}"
        if explanation:
            answer += f"\n\nExplanation: {explanation}"

        if len(answer) < 20:
            continue

        diff_label, diff_score = estimate_difficulty(q_text)
        results.append(_build(q_text, answer, diff_label, diff_score, "MC_SINGLE"))
    return results


# ── Helper ───────────────────────────────────────────────────────────────
def _build(q_text, answer, diff_label, diff_score, q_type) -> dict:
    return {
        "q":  q_text,
        "ans": answer,
        "dl":  diff_label,
        "ds":  diff_score,
        "type": q_type,
    }


PARSERS = {
    "README.md":              parse_readme,
    "sql-query-practice.md":  parse_practice,
    "sql-mcq.md":             parse_mcq,
}


def to_schema(raw: dict, idx: int, filename: str) -> dict:
    return {
        "question_id":      f"DA_LZ_{idx:03d}",
        "question_text":    raw["q"],
        "roles":            {"primary": ROLE, "secondary": []},
        "difficulty_label": raw["dl"],
        "difficulty_score": raw["ds"],
        "question_type":    raw["type"],
        "skill_groups":     [SKILL_GROUP],
        "skill_tags":       SKILL_TAGS,
        "answers": {
            "detailed":          raw["ans"],
            "evaluation_points": extract_eval_points(raw["ans"]),
        },
        "metadata": {
            "language":   "en",
            "source":     f"learning-zone/sql-interview-questions/{filename}",
            "version":    "v1.0",
            "created_at": str(date.today()),
        }
    }


if __name__ == "__main__":
    import os
    all_raw = []

    for filename, (cap, type_override) in FILES.items():
        url = f"{BASE}/{filename}"
        print(f"Fetching {filename} ...")
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            parser = PARSERS[filename]
            parsed = parser(resp.text, cap, type_override)
            print(f"  -> {len(parsed)} questions [{type_override or 'auto'}]")
            all_raw.extend([(r, filename) for r in parsed])
        except Exception as e:
            print(f"  !! FAILED: {e}")

    questions = [to_schema(r, i + 1, fn) for i, (r, fn) in enumerate(all_raw)]

    print("\n── Stats ──────────────────────────")
    print("Total:  ", len(questions))
    print("Types:  ", dict(Counter(q["question_type"] for q in questions)))
    print("Diff:   ", dict(Counter(q["difficulty_label"] for q in questions)))

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/question_bank/scraped_sql.json", "w", encoding="utf-8") as f:
        json.dump({"questions": questions}, f, ensure_ascii=False, indent=2)
    print("\nSaved -> data/raw/question_bank/scraped_sql.json")
