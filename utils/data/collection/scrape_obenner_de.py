"""
Script cào câu hỏi DE từ OBenner/data-engineering-interview-questions
Output: data/raw/question_bank/scraped_de.json

Chạy: python utils/data/collection/scrape_obenner_de.py
"""
import re, json, requests
from datetime import date
from collections import Counter

BASE = "https://raw.githubusercontent.com/OBenner/data-engineering-interview-questions/master/content"

# (cap, skill_group, skill_tags)
# Cap được tính để mỗi skill_group có ~80-120 câu, tránh BIG_DATA_CLOUD_TOOLS chiếm quá nhiều
#
# Target phân phối DE:
#   DATA_PIPELINE          ~50  (airflow=30, cdc=15 → tự nhiên thấp, giữ hết)
#   BIG_DATA_CLOUD_TOOLS   ~120 (7 files: kafka=23, spark=20, hadoop=20, hive=20,
#                                           bigquery=20, avro=23, flink=20 → 146)
#   DATABASE_INTERNALS     ~120 (cassandra=30, hbase=30, mongo=29, sql=35 → 124)
#   DATA_ARCHITECTURE      ~100 (redshift=40, dwha=40, data-modeling=15 → 95)
#   SYSTEM_ARCHITECTURE    ~11  (chỉ có 1 file nhỏ, giữ hết)
FILES = {
    # DATA_PIPELINE (~50)
    "airflow.md":       (30,  "DATA_PIPELINE",              ["PIPE_ORCHESTRATION", "TOOL_AIRFLOW"]),
    "cdc.md":           (99,  "DATA_PIPELINE",              ["PIPE_CDC", "STREAMING"]),
    # BIG_DATA_CLOUD_TOOLS (~146)
    "kafka.md":         (99,  "BIG_DATA_CLOUD_TOOLS",       ["TOOL_KAFKA", "STREAMING"]),
    "spark.md":         (20,  "BIG_DATA_CLOUD_TOOLS",       ["TOOL_SPARK", "BIG_DATA"]),
    "hadoop.md":        (20,  "BIG_DATA_CLOUD_TOOLS",       ["TOOL_HADOOP", "BIG_DATA"]),
    "hive.md":          (20,  "BIG_DATA_CLOUD_TOOLS",       ["TOOL_HIVE", "SQL_ON_HADOOP"]),
    "bigquery.md":      (20,  "BIG_DATA_CLOUD_TOOLS",       ["CLOUD_DW", "GCP"]),
    "avro.md":          (99,  "BIG_DATA_CLOUD_TOOLS",       ["DATA_FORMATS", "SERIALIZATION"]),
    "flink.md":         (20,  "BIG_DATA_CLOUD_TOOLS",       ["TOOL_FLINK", "STREAMING"]),
    # DATABASE_INTERNALS (~124)
    "cassandra.md":     (30,  "DATABASE_INTERNALS",         ["NOSQL", "DISTRIBUTED_DB"]),
    "hbase.md":         (30,  "DATABASE_INTERNALS",         ["NOSQL", "DISTRIBUTED_DB"]),
    "mongo.md":         (99,  "DATABASE_INTERNALS",         ["NOSQL", "DOCUMENT_DB"]),
    "sql.md":           (35,  "DATABASE_INTERNALS",         ["SQL_FUNDAMENTALS", "SQL_PERFORMANCE"]),
    # DATA_ARCHITECTURE_MODELING (~95)
    "redshift.md":      (40,  "DATA_ARCHITECTURE_MODELING", ["DATA_WAREHOUSE", "CLOUD_DW"]),
    "dwha.md":          (40,  "DATA_ARCHITECTURE_MODELING", ["DATA_WAREHOUSE", "DWH_ARCHITECTURE"]),
    "data-modeling.md": (99,  "DATA_ARCHITECTURE_MODELING", ["DATA_MODELING", "DIMENSIONAL_MODELING"]),
    # SYSTEM_ARCHITECTURE (~11, giữ hết)
    "system-design.md": (99,  "SYSTEM_ARCHITECTURE",        ["SYSTEM_DESIGN", "DISTRIBUTED_SYSTEMS"]),
    # delta.md và parquet.md bỏ vì nội dung "Will be available soon"
}

# Ước tính difficulty từ từ khoá trong câu hỏi
def estimate_difficulty(text: str):
    t = text.lower()
    hard_kw = ["design", "architect", "tradeoff", "trade-off", "optimize",
                "performance", "scale", "distributed", "exactly-once", "consistency"]
    easy_kw = ["what is", "what are", "define", "explain", "list", "mention"]
    if any(k in t for k in hard_kw):
        return "HARD", 7
    if any(k in t for k in easy_kw):
        return "EASY", 2
    return "MEDIUM", 5

CODING_KEYWORDS = ("write", "implement", "create", "build", "code", "query", "script",
                   "program", "design a query", "write a query")
QUESTION_WORDS   = ("what", "how", "why", "when", "which", "who", "explain",
                    "describe", "compare", "difference", "define", "list", "name")

def is_real_question(text: str) -> bool:
    """Lọc chỉ giữ heading trông như câu hỏi thật (không phải label mục)."""
    t = text.lower().strip()
    if t.endswith('?'):
        return True
    if any(t.startswith(w) for w in QUESTION_WORDS):
        return True
    # Tối thiểu có 4 từ và ít nhất 1 động từ/tính từ mô tả
    if len(t.split()) >= 4 and any(w in t for w in ("is ", "are ", "does ", "can ", "do ", "will ")):
        return True
    return False


def parse_obenner_md(md: str, skill_group: str, skill_tags: list, cap: int = 99) -> list:
    results = []
    blocks = re.split(r'\n## ', md)
    for block in blocks[1:]:
        if len(results) >= cap:
            break

        lines = block.strip().split('\n')
        q_text = lines[0].strip()
        # Bỏ qua navigation / table of contents / quá ngắn
        if q_text.startswith('[') or q_text.startswith('#') or len(q_text) < 10:
            continue
        # Lọc: chỉ giữ heading trông như câu hỏi
        if not is_real_question(q_text):
            continue

        answer_lines = []
        for line in lines[1:]:
            if line.strip().startswith('[Table of Contents]'):
                break
            answer_lines.append(line)

        answer = '\n'.join(answer_lines).strip()
        answer = re.sub(r'<[^>]+>', '', answer).strip()
        if not answer or len(answer) < 20:
            continue

        diff_label, diff_score = estimate_difficulty(q_text)

        # Detect question type — check cả question text lẫn code block trong answer
        has_code = '```' in answer
        is_coding_q = any(q_text.lower().startswith(kw) or f" {kw} " in q_text.lower()
                          for kw in CODING_KEYWORDS)
        if has_code or is_coding_q:
            q_type = "CODING"
        elif "sql" in skill_group.lower() or "sql" in " ".join(skill_tags).lower():
            q_type = "PRACTICE"
        else:
            q_type = "THEORY"

        eval_points = []
        bullets = re.findall(r'^\s*[+\-\*]\s+(.+)', answer, re.MULTILINE)
        if bullets:
            eval_points = [b.strip() for b in bullets[:3]]
        else:
            sentences = re.split(r'(?<=[.!?])\s+', answer)
            eval_points = [s.strip() for s in sentences if len(s.strip()) > 20][:3]

        results.append({
            "q": q_text,
            "skill_group": skill_group,
            "skill_tags":  skill_tags,
            "diff_label":  diff_label,
            "diff_score":  diff_score,
            "q_type":      q_type,
            "answer":      answer,
            "eval_points": eval_points,
        })
    return results


def to_schema(raw: dict, idx: int, filename: str) -> dict:
    return {
        "question_id":      f"DE_OB_{idx:03d}",
        "question_text":    raw["q"],
        "roles":            {"primary": "DE", "secondary": []},
        "difficulty_label": raw["diff_label"],
        "difficulty_score": raw["diff_score"],
        "question_type":    raw["q_type"],
        "skill_groups":     [raw["skill_group"]],
        "skill_tags":       raw["skill_tags"],
        "answers": {
            "detailed":          raw["answer"],
            "evaluation_points": raw["eval_points"],
        },
        "metadata": {
            "language":   "en",
            "source":     f"OBenner/data-engineering-interview-questions/{filename}",
            "version":    "v1.0",
            "created_at": str(date.today()),
        }
    }


if __name__ == "__main__":
    import os
    all_raw = []

    for filename, (cap, skill_group, skill_tags) in FILES.items():
        url = f"{BASE}/{filename}"
        print(f"Fetching {filename} ...")
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            parsed = parse_obenner_md(resp.text, skill_group, skill_tags, cap=cap)
            print(f"  -> {len(parsed)} questions [{skill_group}]")
            all_raw.extend([(r, filename) for r in parsed])
        except Exception as e:
            print(f"  !! FAILED: {e}")

    questions = [to_schema(r, i+1, fn) for i, (r, fn) in enumerate(all_raw)]

    print("\n── Stats ──────────────────────────")
    print("Total:  ", len(questions))
    print("Types:  ", dict(Counter(q["question_type"] for q in questions)))
    print("Diff:   ", dict(Counter(q["difficulty_label"] for q in questions)))
    print("Groups: ", dict(Counter(q["skill_groups"][0] for q in questions)))

    os.makedirs("data/raw", exist_ok=True)
    out = "data/raw/question_bank/scraped_de.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"questions": questions}, f, ensure_ascii=False, indent=2)
    print(f"\nSaved -> {out}")
