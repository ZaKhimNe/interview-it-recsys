"""
qc_rag.py — RAG-based QC pipeline cho câu hỏi AI-generated.

2 giai đoạn tách biệt:

  Giai đoạn 1 — JUDGE (Claude Haiku):
    Gán nhãn PASS/ENHANCE/FAIL cho từng câu, lưu vào field qc_decision.
    Không sửa nội dung câu hỏi.

  Giai đoạn 2 — ENHANCE (Claude Sonnet):
    Chỉ chạy trên câu có qc_decision=ENHANCE.
    Sonnet viết lại evaluation_points + answer chi tiết hơn.

Cross-model setup:
  Generate:  Gemini 3.5 Flash  (generate_questions.py)
  Reference: GPT-4o            (build_reference.py)
  Judge:     Claude Haiku 4.5  ← rẻ, đủ cho binary judgment
  Enhance:   Claude Sonnet 4.5 ← mạnh hơn cho rewrite chất lượng cao

Chạy:
  python utils/data/qc/qc_rag.py --judge --all              # giai đoạn 1: toàn bộ
  python utils/data/qc/qc_rag.py --judge --all --from-sample # giai đoạn 1: chỉ 153 câu sample
  python utils/data/qc/qc_rag.py --judge --all --only-new   # giai đoạn 1: skip đã judge
  python utils/data/qc/qc_rag.py --enhance --all            # giai đoạn 2: enhance toàn bộ ENHANCE
  python utils/data/qc/qc_rag.py --judge --all --dry-run    # xem số câu sẽ judge
"""

import os, sys, json, re, csv, time, argparse, random
from collections import defaultdict
from anthropic import Anthropic

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ── Mapping competency → reference file ──────────────────────────────────────
COMP_TO_REF = {
    "SQL_DATABASE":               "SQL_DATABASE.txt",
    "BI_VISUALIZATION":           "BI_VISUALIZATION.txt",
    "STATISTICS_EXPERIMENTATION": "STATISTICS_EXPERIMENTATION.txt",
    "ANALYTICS_BUSINESS":         "ANALYTICS_BUSINESS.txt",
    "PYTHON_ANALYTICS":           "PYTHON_ANALYTICS.txt",
    "ALGORITHM_THEORY":           "ALGORITHM_THEORY.txt",
    "EVALUATION_METRICS":         "EVALUATION_METRICS.txt",
    "DATA_PREPROCESSING":         "DATA_PREPROCESSING.txt",
    "DEEP_LEARNING":              "DEEP_LEARNING.txt",
    "NLP":                        "NLP.txt",
    "TIME_SERIES":                "TIME_SERIES.txt",
    "MLOPS":                      "MLOPS.txt",
    "DATA_PIPELINE":              "DATA_PIPELINE.txt",
    "DATA_ARCHITECTURE_MODELING": "DATA_ARCHITECTURE_MODELING.txt",
    "BIG_DATA_CLOUD_TOOLS":       "BIG_DATA_CLOUD_TOOLS.txt",
    "DATABASE_INTERNALS":         "DATABASE_INTERNALS.txt",
    "SYSTEM_ARCHITECTURE":        "SYSTEM_ARCHITECTURE.txt",
}

# Mapping generated file → competency (từ tên file)
FILE_TO_COMP = {
    "generated_analytics.json":     "ANALYTICS_BUSINESS",
    "generated_bi_tools.json":      "BI_VISUALIZATION",
    "generated_cloud_storage.json": "BIG_DATA_CLOUD_TOOLS",
    "generated_data_eng_ds.json":   "DATA_PREPROCESSING",
    "generated_databases.json":     "DATABASE_INTERNALS",
    "generated_deep_learning.json": "DEEP_LEARNING",
    "generated_evaluation.json":    "EVALUATION_METRICS",
    "generated_mlops_ts.json":      "MLOPS",
    "generated_nlp.json":           "NLP",
    "generated_pipelines.json":     "DATA_PIPELINE",
    "generated_python_da.json":     "PYTHON_ANALYTICS",
    "generated_statistics.json":    "STATISTICS_EXPERIMENTATION",
    "generated_system.json":        "SYSTEM_ARCHITECTURE",
    "generated_data_architecture.json": "DATA_ARCHITECTURE_MODELING",
}


# ── Load reference doc ────────────────────────────────────────────────────────
def load_reference(comp: str) -> str:
    ref_file = COMP_TO_REF.get(comp)
    if not ref_file:
        return ""
    path = os.path.join(ROOT, "data/reference", ref_file)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── Retrieve đoạn liên quan nhất (keyword matching) ──────────────────────────
SYNONYM_MAP = {
    "gbm": {"gradient", "boosting", "gradientboosting"},
    "xgb": {"xgboost", "gradient", "boosting"},
    "dl":  {"deep", "learning", "deeplearning", "neural"},
    "nlp": {"natural", "language", "processing"},
    "etl": {"extract", "transform", "load"},
    "elt": {"extract", "load", "transform"},
    "scd": {"slowly", "changing", "dimension"},
    "irt": {"item", "response", "theory"},
    "adf": {"augmented", "dickey", "fuller", "stationarity"},
    "knn": {"nearest", "neighbor", "neighbors"},
    "svm": {"support", "vector", "machine"},
    "pca": {"principal", "component", "analysis"},
    "rnn": {"recurrent", "neural", "network"},
    "cnn": {"convolutional", "neural", "network"},
    "lstm": {"long", "short", "memory"},
    "gru": {"gated", "recurrent", "unit"},
    "dag": {"directed", "acyclic", "graph"},
    "cdc": {"change", "data", "capture"},
    "olap": {"analytical", "processing", "multidimensional"},
    "oltp": {"transactional", "processing"},
    "acid": {"atomicity", "consistency", "isolation", "durability"},
    "cap": {"consistency", "availability", "partition"},
    "dax": {"data", "analysis", "expressions"},
    "lod": {"level", "detail"},
    "mae": {"mean", "absolute", "error"},
    "mse": {"mean", "squared", "error"},
    "rmse": {"root", "mean", "squared"},
    "mape": {"mean", "absolute", "percentage"},
    "auc": {"area", "under", "curve", "roc"},
    "roc": {"receiver", "operating", "characteristic"},
    "tpr": {"true", "positive", "rate", "recall", "sensitivity"},
    "fpr": {"false", "positive", "rate"},
}


def expand_query(q_words: set) -> set:
    """Mở rộng q_words với synonyms cho các viết tắt kỹ thuật."""
    expanded = set(q_words)
    for word in q_words:
        if word in SYNONYM_MAP:
            expanded |= SYNONYM_MAP[word]
    return expanded


def retrieve_context(reference: str, question_text: str, top_k: int = 3) -> str:
    """
    Chia reference thành paragraphs, score theo keyword overlap với câu hỏi.
    Có synonym expansion để không miss viết tắt kỹ thuật (GBM, NLP, ETL...).
    Lấy top_k đoạn liên quan nhất.
    """
    if not reference:
        return ""

    # Tokenize câu hỏi + expand synonyms
    q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', question_text.lower()))
    stopwords = {"the", "and", "for", "with", "that", "this", "are", "was",
                 "what", "how", "why", "when", "which", "can", "you", "your"}
    q_words -= stopwords
    q_words = expand_query(q_words)

    # Chia reference thành paragraphs
    paragraphs = [p.strip() for p in reference.split("\n\n") if len(p.strip()) > 50]

    # Score từng đoạn
    scored = []
    for para in paragraphs:
        para_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', para.lower()))
        overlap = len(q_words & para_words)
        scored.append((overlap, para))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [p for _, p in scored[:top_k] if _ > 0]

    return "\n\n".join(top) if top else "\n\n".join(p for _, p in scored[:2])


SAMPLE_CSV = os.path.join(ROOT, "data/raw/question_bank/human_review_sample.csv")

# ── Anthropic client ──────────────────────────────────────────────────────────
def get_anthropic_client() -> Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        env_path = os.path.join(ROOT, ".env")
        if os.path.exists(env_path):
            for line in open(env_path, encoding="utf-8"):
                if "ANTHROPIC_API_KEY" in line and "=" in line:
                    key = line.strip().split("=", 1)[1].strip().strip('"')
    if not key:
        raise ValueError("Chua set ANTHROPIC_API_KEY trong .env")
    return Anthropic(api_key=key)


def load_sample_ids() -> set:
    """Load danh sach question_id tu human_review_sample.csv."""
    if not os.path.exists(SAMPLE_CSV):
        raise FileNotFoundError(f"Chua co file sample. Chay validate_qc.py --sample truoc.")
    ids = set()
    with open(SAMPLE_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            qid = row.get("question_id", "").strip()
            if qid:
                ids.add(qid)
    return ids


# ── Prompt: JUDGE (Haiku) ─────────────────────────────────────────────────────
def build_judge_prompt(q: dict, context: str) -> str:
    diff   = q.get("difficulty_label", "?")
    qtype  = q.get("question_type", "?")
    qtext  = q.get("question_text", "")
    detail = q.get("answers", {}).get("detailed", "")
    points = q.get("answers", {}).get("evaluation_points", [])
    comp   = q.get("_comp", "?")
    points_str = "\n".join(f"- {p}" for p in points) if points else "(none)"

    return f"""You are a senior technical interviewer. Judge this interview question.

REFERENCE (ground truth):
---
{context if context else "(no reference available)"}
---

QUESTION:
Competency: {comp} | Difficulty: {diff} | Type: {qtype}
Question: {qtext}
Answer: {detail}
Evaluation points:
{points_str}

Judge:
- PASS: technically correct, appropriate difficulty, evaluation points are specific and useful
- ENHANCE: correct concept but evaluation points are too generic, answer needs more depth, or wording needs adjustment
- FAIL: technically wrong, too vague, or irrelevant to competency

Respond ONLY with valid JSON:
{{
  "decision": "PASS" or "ENHANCE" or "FAIL",
  "accuracy": "OK" or "WRONG" or "PARTIAL",
  "difficulty_fit": "OK" or "TOO_EASY" or "TOO_HARD",
  "reason": "one concise sentence explaining the decision"
}}"""


# ── Prompt: ENHANCE (Sonnet) ──────────────────────────────────────────────────
def build_enhance_prompt(q: dict, context: str) -> str:
    diff   = q.get("difficulty_label", "?")
    qtype  = q.get("question_type", "?")
    qtext  = q.get("question_text", "")
    detail = q.get("answers", {}).get("detailed", "")
    points = q.get("answers", {}).get("evaluation_points", [])
    comp   = q.get("_comp", "?")
    reason = q.get("qc_reason", "needs improvement")
    points_str = "\n".join(f"- {p}" for p in points) if points else "(none)"

    return f"""You are a senior technical interviewer. Improve this interview question.

REFERENCE (ground truth):
---
{context if context else "(no reference available)"}
---

QUESTION TO IMPROVE:
Competency: {comp} | Difficulty: {diff} | Type: {qtype}
Question: {qtext}
Current answer: {detail}
Current evaluation points:
{points_str}

Judge's reason for ENHANCE: {reason}

Rewrite to make it excellent:
1. evaluation_points: 3-5 specific, technical points that distinguish strong vs weak answers. Each point must be concrete (not generic like "explain clearly").
2. detailed_answer: comprehensive answer a strong candidate would give, with technical depth appropriate for {diff} level.

Respond ONLY with valid JSON:
{{
  "enhanced_evaluation_points": ["point1", "point2", "point3"],
  "enhanced_answer": "improved detailed answer"
}}"""


# ── API calls ─────────────────────────────────────────────────────────────────
def call_claude(client: Anthropic, prompt: str, model: str, max_tokens: int, max_retries: int = 2) -> str:
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                raise e
    return ""


def parse_json(text: str) -> dict:
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group())


# ── Helper: load + dedup questions từ generated files ────────────────────────
def load_generated(comp_filter: str = None) -> list[tuple]:
    """Return list of (fpath, fname, comp, questions)."""
    gen_dir = os.path.join(ROOT, "data/raw/question_bank/generated")
    result = []
    for fname, comp in FILE_TO_COMP.items():
        if comp_filter and comp != comp_filter:
            continue
        fpath = os.path.join(gen_dir, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, encoding="utf-8") as f:
            questions = json.load(f)
        seen = set()
        unique = []
        for q in questions:
            qid = q.get("question_id", "")
            if qid not in seen:
                seen.add(qid)
                q["_comp"] = comp
                unique.append(q)
        result.append((fpath, fname, comp, unique))
    return result


def save_file(fpath: str, questions: list):
    clean = []
    for q in questions:
        q = {k: v for k, v in q.items() if not k.startswith("_")}
        clean.append(q)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)


def write_csv(rows: list, csv_path: str):
    fieldnames = ["decision","reason","accuracy","difficulty_fit",
                  "question_id","competency","difficulty","question_text","source_file"]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ── Giai đoạn 1: JUDGE (Haiku) ───────────────────────────────────────────────
def run_judge(comp_filter: str = None, only_new: bool = False, from_sample: bool = False):
    """
    Haiku gán nhãn PASS/ENHANCE/FAIL cho từng câu.
    Lưu vào field qc_decision + qc_reason. Không sửa nội dung.
    """
    client  = get_anthropic_client()
    reports = os.path.join(ROOT, "data/raw/question_bank")
    os.makedirs(reports, exist_ok=True)

    sample_ids = load_sample_ids() if from_sample else None
    if from_sample:
        print(f"Mode: --from-sample ({len(sample_ids)} cau tu human_review_sample.csv)")

    files = load_generated(comp_filter)
    if not files:
        print("Khong tim thay file nao.")
        return

    csv_rows = []
    total_pass = total_enhance = total_fail = total_unreviewed = 0

    SUBTAG_TO_COMP = {
        "ML_TIME_SERIES": "TIME_SERIES", "TIME_SERIES": "TIME_SERIES",
        "ML_MLOPS": "MLOPS", "ML_MONITORING": "MLOPS", "ML_EXPLAINABILITY": "MLOPS",
    }

    for fpath, fname, comp, unique_qs in files:
        print(f"\n{'='*55}")
        print(f"JUDGE: {comp} ({fname})")
        print(f"{'='*55}")

        # Filter
        to_judge = unique_qs
        if from_sample:
            to_judge = [q for q in unique_qs if q.get("question_id","") in sample_ids]
        elif only_new:
            to_judge = [q for q in unique_qs if not q.get("qc_decision")]

        if not to_judge:
            print(f"  Skip — tat ca da duoc judge.")
            continue

        print(f"  To judge: {len(to_judge)}/{len(unique_qs)}")

        reference = load_reference(comp)
        if not reference:
            print(f"  WARNING: No reference doc for {comp}")

        qs_map = {q["question_id"]: q for q in unique_qs}

        for i, q in enumerate(to_judge):
            qid  = q.get("question_id", "?")
            diff = q.get("difficulty_label", "?")

            # Dùng skill_group thực của câu để pick đúng reference doc
            sgs = q.get("skill_groups") or q.get("skill_tags") or []
            actual_comp = next((SUBTAG_TO_COMP.get(sg, sg) for sg in sgs
                                if SUBTAG_TO_COMP.get(sg, sg) in COMP_TO_REF), comp)
            ref_for_q = load_reference(actual_comp) or reference
            context = retrieve_context(ref_for_q, q.get("question_text", ""))
            print(f"  [{i+1:3d}/{len(to_judge)}] {qid} ({diff})", end=" ", flush=True)

            try:
                raw    = call_claude(client, build_judge_prompt(q, context),
                                     model="claude-haiku-4-5-20251001", max_tokens=512)
                result = parse_json(raw)
                decision = result.get("decision", "UNREVIEWED")
            except Exception as e:
                result   = {"decision": "UNREVIEWED", "reason": str(e), "accuracy": "", "difficulty_fit": ""}
                decision = "UNREVIEWED"

            print(f"→ {decision}  {result.get('reason','')[:60]}")

            # Ghi nhãn vào câu, KHÔNG sửa content
            qs_map[qid]["qc_decision"] = decision
            qs_map[qid]["qc_reason"]   = result.get("reason", "")
            qs_map[qid]["qc_accuracy"] = result.get("accuracy", "")
            qs_map[qid]["qc_diff_fit"] = result.get("difficulty_fit", "")

            if decision == "FAIL":
                qs_map[qid]["qc_reviewed"] = True  # đánh dấu đã xử lý
                total_fail += 1
            elif decision == "PASS":
                qs_map[qid]["qc_reviewed"] = True
                total_pass += 1
            elif decision == "ENHANCE":
                total_enhance += 1
            else:
                total_unreviewed += 1

            csv_rows.append({
                "decision":       decision,
                "reason":         result.get("reason", ""),
                "accuracy":       result.get("accuracy", ""),
                "difficulty_fit": result.get("difficulty_fit", ""),
                "question_id":    qid,
                "competency":     comp,
                "difficulty":     diff,
                "question_text":  q.get("question_text", "")[:120],
                "source_file":    fname,
            })

            time.sleep(0.3)

        # Xóa câu FAIL, giữ lại tất cả còn lại (kể cả ENHANCE chưa sửa)
        final = [q for q in qs_map.values() if q.get("qc_decision") != "FAIL"]
        removed = len(qs_map) - len(final)
        save_file(fpath, final)
        print(f"\n  Saved {len(final)} questions (removed {removed} FAIL)")

    csv_path = os.path.join(reports, "qc_rag_result.csv")
    write_csv(csv_rows, csv_path)

    total = total_pass + total_enhance + total_fail + total_unreviewed
    if total == 0:
        return
    print(f"\n{'='*55}")
    print(f"JUDGE SUMMARY — {total} questions")
    print(f"{'='*55}")
    print(f"  PASS:       {total_pass:4d} ({total_pass/total*100:.1f}%)")
    print(f"  ENHANCE:    {total_enhance:4d} ({total_enhance/total*100:.1f}%)  ← se enhance sau")
    print(f"  FAIL:       {total_fail:4d} ({total_fail/total*100:.1f}%)  ← da xoa khoi file")
    if total_unreviewed:
        print(f"  UNREVIEWED: {total_unreviewed:4d} ({total_unreviewed/total*100:.1f}%)")
    print(f"\n  Report: {csv_path}")
    print(f"\nBuoc tiep theo:")
    if total_enhance > 0:
        print(f"  python utils/data/qc/qc_rag.py --enhance --all   # Sonnet enhance {total_enhance} cau")


# ── Giai đoạn 2: ENHANCE (Sonnet) ────────────────────────────────────────────
def run_enhance(comp_filter: str = None):
    """
    Sonnet viết lại evaluation_points + answer cho các câu có qc_decision=ENHANCE.
    """
    client = get_anthropic_client()
    files  = load_generated(comp_filter)

    total_enhanced = 0

    for fpath, fname, comp, unique_qs in files:
        to_enhance = [q for q in unique_qs if q.get("qc_decision") == "ENHANCE"
                      and not q.get("qc_enhanced")]

        if not to_enhance:
            continue

        print(f"\n{'='*55}")
        print(f"ENHANCE: {comp} — {len(to_enhance)} cau")
        print(f"{'='*55}")

        reference = load_reference(comp)
        qs_map    = {q["question_id"]: q for q in unique_qs}

        for i, q in enumerate(to_enhance):
            qid = q.get("question_id", "?")
            print(f"  [{i+1:3d}/{len(to_enhance)}] {qid}", end=" ", flush=True)

            context = retrieve_context(reference, q.get("question_text", ""))

            try:
                raw    = call_claude(client, build_enhance_prompt(q, context),
                                     model="claude-sonnet-4-5", max_tokens=4096)
                result = parse_json(raw)

                new_points = result.get("enhanced_evaluation_points", [])
                new_answer = result.get("enhanced_answer", "")

                if new_points:
                    qs_map[qid].setdefault("answers", {})["evaluation_points"] = new_points
                if new_answer:
                    qs_map[qid].setdefault("answers", {})["detailed"] = new_answer

                qs_map[qid]["qc_enhanced"] = True
                qs_map[qid]["qc_reviewed"] = True
                total_enhanced += 1
                print(f"→ OK ({len(new_points)} eval points)")
            except Exception as e:
                print(f"→ ERROR: {e}")

            time.sleep(0.5)

        save_file(fpath, list(qs_map.values()))

    print(f"\n{'='*55}")
    print(f"ENHANCE DONE — {total_enhanced} cau da duoc Sonnet rewrite")
    print(f"{'='*55}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge",       action="store_true", help="[Giai doan 1] Haiku gan nhan PASS/ENHANCE/FAIL")
    parser.add_argument("--enhance",     action="store_true", help="[Giai doan 2] Sonnet rewrite cac cau ENHANCE")
    parser.add_argument("--all",         action="store_true", help="Chay tat ca competency")
    parser.add_argument("--comp",        help="Chi chay 1 competency (vd: SQL_DATABASE)")
    parser.add_argument("--only-new",    action="store_true", help="[Judge] Chi judge cau chua co quyet dinh")
    parser.add_argument("--from-sample", action="store_true", help="[Judge] Chi judge 153 cau trong human_review_sample.csv")
    parser.add_argument("--dry-run",     action="store_true", help="Xem so cau se xu ly, khong goi API")
    args = parser.parse_args()

    if not args.all and not args.comp:
        print("Giai doan 1 — JUDGE (Haiku):")
        print("  python utils/data/qc/qc_rag.py --judge --all --from-sample  # 153 cau sample truoc")
        print("  python utils/data/qc/qc_rag.py --judge --all --only-new     # phan con lai")
        print("  python utils/data/qc/qc_rag.py --judge --all --dry-run      # xem so cau")
        print()
        print("Giai doan 2 — ENHANCE (Sonnet):")
        print("  python utils/data/qc/qc_rag.py --enhance --all              # rewrite cac cau ENHANCE")
        return

    only_new    = getattr(args, "only_new", False)
    from_sample = getattr(args, "from_sample", False)
    dry_run     = getattr(args, "dry_run", False)

    if dry_run:
        files = load_generated(args.comp)
        total_judge = total_enhance_pending = 0
        sample_ids = load_sample_ids() if from_sample else None
        for fpath, fname, comp, qs in files:
            if from_sample and sample_ids:
                n = len([q for q in qs if q.get("question_id","") in sample_ids])
            elif only_new:
                n = len([q for q in qs if not q.get("qc_decision")])
            else:
                n = len(qs)
            n_enh = len([q for q in qs if q.get("qc_decision") == "ENHANCE" and not q.get("qc_enhanced")])
            total_judge += n
            total_enhance_pending += n_enh
            print(f"  {comp}: judge={n}  enhance_pending={n_enh}")
        print(f"\nTong se judge: {total_judge}")
        print(f"Tong cho enhance: {total_enhance_pending}")
        return

    if args.judge:
        run_judge(comp_filter=args.comp, only_new=only_new, from_sample=from_sample)
    elif args.enhance:
        run_enhance(comp_filter=args.comp)
    else:
        print("Can chi dinh --judge hoac --enhance")


if __name__ == "__main__":
    main()
