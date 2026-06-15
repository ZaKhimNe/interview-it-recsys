"""
merge_to_question_bank.py — Merge tất cả câu hỏi vào mock_question_data.json.

Nguồn:
  - data/raw/question_bank/generated/generated_*.json  (AI-generated, đã QC)
  - data/raw/question_bank/scraped/*.json              (scraped từ nguồn thực)

Output:
  - data/raw/question_bank/question_bank.json    (app đọc từ đây)

Logic:
  - Dedup theo question_id
  - Chuẩn hóa format theo schema app (roles, skill_groups, difficulty_label...)
  - Mỗi lần chạy lại sẽ rebuild hoàn toàn từ sources

Chạy: python utils/data/processing/merge_to_question_bank.py
"""

import os, sys, json, re
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

VALID_DIFFICULTIES = {"EASY", "MEDIUM", "HARD"}
VALID_TYPES = {"THEORY", "CODING", "PRACTICE", "MC_SINGLE", "TRUE_FALSE", "FILL_BLANK"}

# Mapping competency → primary role
COMP_TO_ROLE = {
    "SQL_DATABASE":               "DA",
    "BI_VISUALIZATION":           "DA",
    "STATISTICS_EXPERIMENTATION": "DA",
    "ANALYTICS_BUSINESS":         "DA",
    "PYTHON_ANALYTICS":           "DA",
    "ALGORITHM_THEORY":           "DS",
    "EVALUATION_METRICS":         "DS",
    "DATA_PREPROCESSING":         "DS",
    "DEEP_LEARNING":              "DS",
    "NLP":                        "DS",
    "TIME_SERIES":                "DS",
    "MLOPS":                      "DS",
    "DATA_PIPELINE":              "DE",
    "DATA_ARCHITECTURE_MODELING": "DE",
    "BIG_DATA_CLOUD_TOOLS":       "DE",
    "DATABASE_INTERNALS":         "DE",
    "SYSTEM_ARCHITECTURE":        "DE",
}

JD_SKILLS = {
    "DA": ["SQL_DATABASE","BI_VISUALIZATION","STATISTICS_EXPERIMENTATION","ANALYTICS_BUSINESS","PYTHON_ANALYTICS"],
    "DS": ["ALGORITHM_THEORY","EVALUATION_METRICS","DATA_PREPROCESSING","DEEP_LEARNING","NLP","TIME_SERIES","MLOPS"],
    "DE": ["DATA_PIPELINE","DATA_ARCHITECTURE_MODELING","BIG_DATA_CLOUD_TOOLS","DATABASE_INTERNALS","SYSTEM_ARCHITECTURE"],
}


def infer_role(q: dict) -> dict:
    """Infer primary role từ skill_groups nếu roles chưa có."""
    existing = q.get("roles")
    if isinstance(existing, dict) and existing.get("primary") in {"DA","DS","DE"}:
        return existing

    skill_groups = q.get("skill_groups", q.get("skill_tags", []))
    primary = None
    for sg in skill_groups:
        if sg in COMP_TO_ROLE:
            primary = COMP_TO_ROLE[sg]
            break

    if not primary:
        qid = q.get("question_id", "")
        if "_DA_" in qid: primary = "DA"
        elif "_DS_" in qid: primary = "DS"
        elif "_DE_" in qid: primary = "DE"
        else: primary = "DA"

    # Secondary roles: roles khác cũng có competency này
    secondary = []
    for sg in skill_groups:
        for role, comps in JD_SKILLS.items():
            if sg in comps and role != primary and role not in secondary:
                secondary.append(role)

    return {"primary": primary, "secondary": secondary}


def normalize_question(q: dict) -> dict | None:
    qid = str(q.get("question_id", "")).strip()
    qtext = str(q.get("question_text", "")).strip()
    if not qid or not qtext:
        return None

    difficulty = str(q.get("difficulty_label", "MEDIUM")).upper()
    if difficulty not in VALID_DIFFICULTIES:
        difficulty = "MEDIUM"

    try:
        diff_score = int(q.get("difficulty_score", 0))
    except (TypeError, ValueError):
        diff_score = 0

    qtype = str(q.get("question_type", "THEORY")).upper()
    if qtype not in VALID_TYPES:
        qtype = "THEORY"

    skill_groups = [str(g) for g in (q.get("skill_groups") or q.get("skill_tags") or []) if g]
    skill_tags   = [str(t) for t in (q.get("skill_tags") or []) if t]

    return {
        "question_id":    qid,
        "question_text":  qtext,
        "roles":          infer_role(q),
        "difficulty_label": difficulty,
        "difficulty_score": diff_score,
        "question_type":  qtype,
        "skill_tags":     skill_tags,
        "skill_groups":   skill_groups,
        "answers":        q.get("answers", {}),
        "metadata":       q.get("metadata", {}),
        "options":        q.get("options"),
        "template":       q.get("template"),
        "test_cases":     q.get("test_cases"),
        "starter_code":   q.get("starter_code"),
        "constraints":    q.get("constraints"),
        "allowed_languages": q.get("allowed_languages"),
    }


def load_source(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("questions", [])


def main():
    gen_dir     = os.path.join(ROOT, "data/raw/question_bank/generated")
    scraped_dir = os.path.join(ROOT, "data/raw/question_bank/scraped")
    out_path    = os.path.join(ROOT, "data/raw/question_bank/question_bank.json")

    sources = []

    # Generated files
    for fname in sorted(os.listdir(gen_dir)):
        if fname.startswith("generated_") and fname.endswith(".json"):
            sources.append(os.path.join(gen_dir, fname))

    # Scraped files
    for fname in ["scraped_sql.json", "scraped_github.json",
                  "scraped_youssef.json", "converted_tf_fb.json"]:
        p = os.path.join(scraped_dir, fname)
        if os.path.exists(p):
            sources.append(p)

    # Load + normalize + dedup
    seen_ids = set()
    all_qs = []
    for path in sources:
        fname = os.path.basename(path)
        raw_qs = load_source(path)
        added = 0
        for q in raw_qs:
            norm = normalize_question(q)
            if not norm:
                continue
            if norm["question_id"] in seen_ids:
                continue
            seen_ids.add(norm["question_id"])
            all_qs.append(norm)
            added += 1
        print(f"  {fname}: {added} questions loaded")

    # Save
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_qs, f, ensure_ascii=False, indent=2)

    print(f"\nTotal merged: {len(all_qs)} questions → {out_path}")

    # Coverage check
    print("\n=== Coverage per competency ===")
    jd = json.load(open(os.path.join(ROOT, "data/schemas/jd_requirements.schema.json"), encoding="utf-8"))
    for role in ["DA", "DS", "DE"]:
        for comp in jd[role]["skill_groups"]:
            matched = [q for q in all_qs if comp in q.get("skill_groups", [])]
            status = "OK" if len(matched) >= 5 else "LOW"
            print(f"  {status} [{role}] {comp}: {len(matched)}")


if __name__ == "__main__":
    main()
