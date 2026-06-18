"""
merge_to_question_bank.py — Merge tất cả câu hỏi vào question_bank.json.

Nguồn:
  - data/raw/question_bank/generated/generated_*.json  (AI-generated, đã QC)
  - data/raw/question_bank/scraped/scraped_sql.json
  - data/raw/question_bank/scraped/scraped_github.json
  - data/raw/question_bank/scraped/scraped_youssef.json
  - data/raw/question_bank/scraped/scraped_de.json
  - data/raw/question_bank/scraped/question_bank_v1.json

Output:
  - data/raw/question_bank/question_bank.json

Logic:
  - Dedup theo question_id, sau đó theo question_text (normalize whitespace)
  - Chuẩn hóa schema đồng nhất: 16 root fields, metadata 4 keys, options list[dict]
  - FILL_BLANK / CODING_EXERCISE bị loại (app chưa render được)
  - MC_SINGLE: options từ answers.options nếu thiếu ở root; str → {id,text}; không có options → THEORY
  - skill_group luôn được ưu tiên hơn roles field để infer primary role

Chạy: python utils/data/processing/merge_to_question_bank.py
"""

import os, sys, json, re
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

SKIP_TYPES     = {"CODING_EXERCISE"}   # FILL_BLANK ok nếu có template + accepted_answers
VALID_TYPES    = {"THEORY", "CODING", "PRACTICE", "MC_SINGLE", "TRUE_FALSE", "FILL_BLANK"}
VALID_DIFF     = {"EASY", "MEDIUM", "HARD"}

SUBTAG_TO_PARENT = {
    "TOOL_POWER_BI":            "BI_VISUALIZATION",
    "TOOL_TABLEAU":             "BI_VISUALIZATION",
    "PYTHON_PANDAS":            "PYTHON_ANALYTICS",
    "LANG_PYTHON":              "PYTHON_ANALYTICS",
    "ANALYTICS_COHORT":         "ANALYTICS_BUSINESS",
    "ANALYTICS_FUNNEL":         "ANALYTICS_BUSINESS",
    "STAT_AB_TESTING":          "STATISTICS_EXPERIMENTATION",
    "STAT_HYPOTHESIS_TESTING":  "STATISTICS_EXPERIMENTATION",
    "STAT_CONFIDENCE_INTERVAL": "STATISTICS_EXPERIMENTATION",
    "ML_TIME_SERIES":           "TIME_SERIES",
    "ML_MLOPS":                 "MLOPS",
    "ML_MONITORING":            "MLOPS",
    "ML_EXPLAINABILITY":        "ALGORITHM_THEORY",
    "NLP_PREPROCESSING":        "NLP",
    "NLP_EVALUATION":           "NLP",
    "IMBALANCED_DATA_HANDLING": "DATA_PREPROCESSING",
    "ENCODING_TECHNIQUES":      "DATA_PREPROCESSING",
    "FEATURE_ENGINEERING":      "DATA_PREPROCESSING",
    "EVAL_CROSS_VALIDATION":    "EVALUATION_METRICS",
    "METRIC_F1_SCORE":          "EVALUATION_METRICS",
    "DL_TRAINING":              "DEEP_LEARNING",
    "DL_UNSUPERVISED":          "DEEP_LEARNING",
    "DL_CNN":                   "DEEP_LEARNING",
    "DATABASE_INDEXING":        "DATABASE_INTERNALS",
    "DATABASE_SCALING":         "DATABASE_INTERNALS",
    "DB_ACID":                  "DATABASE_INTERNALS",
    "PIPE_CDC":                 "DATA_PIPELINE",
    "PIPE_PERFORMANCE":         "DATA_PIPELINE",
    "PIPE_ELT":                 "DATA_PIPELINE",
    "PIPE_ETL":                 "DATA_PIPELINE",
    "PIPE_ORCHESTRATION":       "DATA_PIPELINE",
    "ARCH_DATA_ARCHITECTURE":   "DATA_ARCHITECTURE_MODELING",
    "MODELING_STAR_SCHEMA":     "DATA_ARCHITECTURE_MODELING",
    "MODELING_SCD":             "DATA_ARCHITECTURE_MODELING",
    "DATA_WAREHOUSE":           "DATA_ARCHITECTURE_MODELING",
    "DATA_LAKE":                "DATA_ARCHITECTURE_MODELING",
    "CLOUD_S3":                 "BIG_DATA_CLOUD_TOOLS",
    "CLOUD_GCP":                "BIG_DATA_CLOUD_TOOLS",
    "CLOUD_AWS":                "BIG_DATA_CLOUD_TOOLS",
    "FORMAT_PARQUET":           "BIG_DATA_CLOUD_TOOLS",
    "FORMAT_AVRO":              "BIG_DATA_CLOUD_TOOLS",
}

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


def norm_text(t: str) -> str:
    return re.sub(r"\s+", " ", t.lower().strip())


def parse_str_option(s: str) -> dict:
    """'A. text' hoặc 'A) text' → {'id': 'A', 'text': 'text'}"""
    m = re.match(r"^([A-Za-z])[.)]\s*(.+)$", s.strip())
    if m:
        return {"id": m.group(1).upper(), "text": m.group(2).strip()}
    return {"id": s[:1], "text": s}


def infer_role(q: dict) -> dict:
    """Infer primary role từ skill_groups — luôn ưu tiên hơn roles field."""
    skill_groups = q.get("skill_groups") or q.get("skill_tags") or []
    primary = next((COMP_TO_ROLE[sg] for sg in skill_groups if sg in COMP_TO_ROLE), None)
    if not primary:
        qid = q.get("question_id", "").upper()
        primary = ("DA" if "_DA_" in qid or qid.startswith("DA") else
                   "DS" if "_DS_" in qid or qid.startswith("DS") else
                   "DE" if "_DE_" in qid or qid.startswith("DE") else "DA")
    secondary = [r for r in ("DA", "DS", "DE")
                 if r != primary and any(sg in JD_SKILLS[r] for sg in skill_groups)]
    return {"primary": primary, "secondary": secondary}


def normalize_question(q: dict) -> dict | None:
    qid   = str(q.get("question_id", "")).strip()
    qtext = str(q.get("question_text", "")).strip()
    if not qid or not qtext:
        return None

    qtype = str(q.get("question_type", "THEORY")).upper()
    if qtype in SKIP_TYPES:
        return None
    # SCENARIO / PRACTICAL từ Gemini → PRACTICE
    if qtype in {"SCENARIO", "PRACTICAL"}:
        qtype = "PRACTICE"
    if qtype not in VALID_TYPES:
        qtype = "THEORY"
    # THEORY có dạng tình huống → PRACTICE (rule-based, không cần API)
    if qtype == "THEORY":
        t = qtext.lower()
        SCENARIO_PREFIXES = [
            "bạn đang", "bạn được giao", "bạn làm việc", "bạn là ",
            "công ty bạn", "công ty có", "giả sử ", "suppose ", "imagine ",
            "you are working", "you are a ", "you have been",
        ]
        if any(t.startswith(p) for p in SCENARIO_PREFIXES):
            qtype = "PRACTICE"
    # FILL_BLANK phải có template + accepted_answers mới usable
    if qtype == "FILL_BLANK":
        if not q.get("template") or not (q.get("answers") or {}).get("accepted_answers"):
            return None

    diff = str(q.get("difficulty_label", "MEDIUM")).upper()
    if diff not in VALID_DIFF:
        diff = "MEDIUM"

    try:
        diff_score = int(q.get("difficulty_score", 0))
        if not (1 <= diff_score <= 10):
            diff_score = {"EASY": 2, "MEDIUM": 5, "HARD": 8}[diff]
    except (TypeError, ValueError):
        diff_score = {"EASY": 2, "MEDIUM": 5, "HARD": 8}[diff]

    # skill_groups: normalize subtags → parent
    raw_sgs = [str(g) for g in (q.get("skill_groups") or q.get("skill_tags") or []) if g]
    skill_groups: list = []
    for sg in raw_sgs:
        mapped = SUBTAG_TO_PARENT.get(sg, sg)
        if mapped not in skill_groups:
            skill_groups.append(mapped)
    skill_tags = [str(t) for t in (q.get("skill_tags") or []) if t]

    # options: fix MC_SINGLE
    options = None
    if qtype == "MC_SINGLE":
        root_opts = q.get("options")
        ans_opts  = (q.get("answers") or {}).get("options")
        resolved  = root_opts or ans_opts
        if not resolved:
            qtype = "THEORY"       # không có options → downgrade
        else:
            if isinstance(resolved, list) and resolved and isinstance(resolved[0], str):
                resolved = [parse_str_option(o) for o in resolved]
            options = resolved

    # metadata: chuẩn hóa đúng 4 keys
    meta = dict(q.get("metadata") or {})
    metadata = {
        "language":   meta.get("language", "vi"),
        "source":     meta.get("source", "unknown"),
        "version":    meta.get("version", "v1.0"),
        "created_at": meta.get("created_at", ""),
    }

    return {
        "question_id":       qid,
        "question_text":     qtext,
        "roles":             infer_role({**q, "skill_groups": skill_groups}),
        "difficulty_label":  diff,
        "difficulty_score":  diff_score,
        "question_type":     qtype,
        "skill_tags":        skill_tags,
        "skill_groups":      skill_groups,
        "answers":           q.get("answers") or {},
        "metadata":          metadata,
        "options":           options,
        "template":          q.get("template"),
        "test_cases":        q.get("test_cases"),
        "starter_code":      q.get("starter_code"),
        "constraints":       q.get("constraints"),
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

    # Scraped files theo thứ tự ưu tiên
    for fname in [
        "scraped_sql.json",
        "scraped_github.json",
        "scraped_youssef.json",
        "scraped_de.json",
        "question_bank_v1.json",
        # converted_tf_fb.json bị loại — FILL_BLANK thiếu template/accepted_answers
    ]:
        p = os.path.join(scraped_dir, fname)
        if os.path.exists(p):
            sources.append(p)

    # Load + normalize + dedup (id trước, text sau)
    seen_ids   = set()
    seen_texts = set()
    all_qs     = []

    for path in sources:
        fname  = os.path.basename(path)
        raw_qs = load_source(path)
        added = skip_type = skip_id = skip_text = 0

        for q in raw_qs:
            qtype = str(q.get("question_type", "")).upper()
            if qtype in SKIP_TYPES:
                skip_type += 1
                continue

            norm = normalize_question(q)
            if not norm:
                continue

            if norm["question_id"] in seen_ids:
                skip_id += 1
                continue

            nt = norm_text(norm["question_text"])
            if nt in seen_texts:
                skip_text += 1
                continue

            seen_ids.add(norm["question_id"])
            seen_texts.add(nt)
            all_qs.append(norm)
            added += 1

        print(f"  {fname:<40} +{added:>4}  (skip type={skip_type} id={skip_id} text={skip_text})")

    # Save
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_qs, f, ensure_ascii=False, indent=2)

    print(f"\nTotal merged: {len(all_qs)} questions → {out_path}")

    # Coverage check
    print("\n=== Coverage per competency (target 90) ===")
    from collections import defaultdict
    comp_cnt = defaultdict(int)
    for q in all_qs:
        role = q["roles"]["primary"]
        sgs  = q["skill_groups"]
        psg  = next((sg for sg in sgs if sg in JD_SKILLS.get(role, [])), None)
        if psg:
            comp_cnt[psg] += 1

    all_ok = True
    for role in ["DA", "DS", "DE"]:
        for comp in JD_SKILLS[role]:
            cnt    = comp_cnt[comp]
            status = "OK  " if cnt >= 90 else f"LOW "
            if cnt < 90: all_ok = False
            print(f"  {status} [{role}] {comp:<35} {cnt}")

    print()
    print("Ket qua:", "TAT CA >= 90" if all_ok else "Con thieu mot so competency")


if __name__ == "__main__":
    main()
