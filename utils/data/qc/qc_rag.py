"""
qc_rag.py — RAG-based QC pipeline cho câu hỏi AI-generated.

Luồng:
  1. Load câu hỏi từ data/raw/question_bank/generated/
  2. Với mỗi câu: retrieve đoạn reference liên quan (keyword matching)
  3. Gửi Claude review dựa trên reference → PASS / ENHANCE / FAIL
  4. ENHANCE: Claude viết lại phần cần bổ sung
  5. Xuất reports/qc_rag_result.csv + lưu câu đã được enhance

Chạy:
  python utils/data/qc/qc_rag.py --all
  python utils/data/qc/qc_rag.py --comp SQL_DATABASE
  python utils/data/qc/qc_rag.py --all --sample 20   # test nhanh 20 câu/file
"""

import os, sys, json, re, csv, time, argparse, random
from collections import defaultdict
from openai import OpenAI

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
def retrieve_context(reference: str, question_text: str, top_k: int = 3) -> str:
    """
    Chia reference thành paragraphs, score theo keyword overlap với câu hỏi.
    Lấy top_k đoạn liên quan nhất.
    """
    if not reference:
        return ""

    # Tokenize câu hỏi
    q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', question_text.lower()))
    stopwords = {"the", "and", "for", "with", "that", "this", "are", "was",
                 "what", "how", "why", "when", "which", "can", "you", "your"}
    q_words -= stopwords

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


# ── Claude API (Anthropic, dùng OpenAI-compatible SDK) ───────────────────────
def get_claude_client() -> OpenAI:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        env_path = os.path.join(ROOT, ".env")
        if os.path.exists(env_path):
            for line in open(env_path, encoding="utf-8"):
                if "ANTHROPIC_API_KEY" in line and "=" in line:
                    key = line.strip().split("=", 1)[1].strip().strip('"')
    if not key:
        raise ValueError("Chua set ANTHROPIC_API_KEY trong .env")
    return OpenAI(
        api_key=key,
        base_url="https://api.anthropic.com/v1/"
    )


# ── Prompt review ─────────────────────────────────────────────────────────────
def build_review_prompt(q: dict, context: str) -> str:
    diff      = q.get("difficulty_label", "?")
    qtype     = q.get("question_type", "?")
    qtext     = q.get("question_text", "")
    detail    = q.get("answers", {}).get("detailed", "")
    points    = q.get("answers", {}).get("evaluation_points", [])
    comp      = q.get("_comp", "?")

    points_str = "\n".join(f"- {p}" for p in points) if points else "(none)"

    return f"""You are a senior technical interviewer reviewing a Data interview question.

REFERENCE KNOWLEDGE (ground truth):
---
{context if context else "(no reference available)"}
---

QUESTION TO REVIEW:
Competency: {comp} | Difficulty: {diff} | Type: {qtype}

Question: {qtext}

Answer: {detail}

Evaluation points:
{points_str}

Review this question against the reference. Decide:
- PASS: technically correct, appropriate difficulty, clear question, useful evaluation points
- ENHANCE: correct concept but needs improvement (add/clarify evaluation points, adjust difficulty wording, expand answer)
- FAIL: technically wrong, too vague, or not relevant to the competency

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "decision": "PASS" or "ENHANCE" or "FAIL",
  "accuracy": "OK" or "WRONG" or "PARTIAL",
  "difficulty_fit": "OK" or "TOO_EASY" or "TOO_HARD",
  "reason": "one concise sentence",
  "enhanced_evaluation_points": ["point1", "point2", "point3"] (if ENHANCE, else []),
  "enhanced_answer": "improved answer text" (if ENHANCE and answer needs fix, else "")
}}"""


def review_question(client: OpenAI, q: dict, context: str, max_retries: int = 2) -> dict:
    prompt = build_review_prompt(q, context)
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            content = resp.choices[0].message.content
            if not content:
                raise ValueError("Empty content from Gemini")
            content = content.strip()
            # Extract JSON từ response (Gemini hay wrap trong ```json ... ```)
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                raise ValueError("No JSON found in response")
            result = json.loads(json_match.group())
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return {
                    "decision": "UNREVIEWED",
                    "accuracy": "",
                    "difficulty_fit": "",
                    "reason": f"Parse error: {e}",
                    "enhanced_evaluation_points": [],
                    "enhanced_answer": ""
                }


# ── Apply ENHANCE vào câu hỏi ────────────────────────────────────────────────
def apply_enhance(q: dict, review: dict) -> dict:
    enhanced_points = review.get("enhanced_evaluation_points", [])
    enhanced_answer = review.get("enhanced_answer", "")

    if enhanced_points:
        q.setdefault("answers", {})["evaluation_points"] = enhanced_points
    if enhanced_answer:
        q.setdefault("answers", {})["detailed"] = enhanced_answer

    q["qc_reviewed"] = True
    q["_qc_enhanced"] = True
    return q


# ── Main pipeline ─────────────────────────────────────────────────────────────
def run_qc(comp_filter: str = None, sample: int = 0, only_new: bool = False):
    gen_dir     = os.path.join(ROOT, "data/raw/question_bank/generated")
    reports_dir = os.path.join(ROOT, "data", "raw", "question_bank")
    os.makedirs(reports_dir, exist_ok=True)

    client = get_claude_client()

    # Collect files cần review
    files_to_review = []
    for fname, comp in FILE_TO_COMP.items():
        if comp_filter and comp != comp_filter:
            continue
        fpath = os.path.join(gen_dir, fname)
        if os.path.exists(fpath):
            files_to_review.append((fpath, fname, comp))

    if not files_to_review:
        print("Khong tim thay file nao de review.")
        return

    csv_rows = []
    total_pass = total_enhance = total_fail = total_unreviewed = 0

    for fpath, fname, comp in files_to_review:
        print(f"\n{'='*55}")
        print(f"Reviewing: {comp} ({fname})")
        print(f"{'='*55}")

        with open(fpath, encoding="utf-8") as f:
            questions = json.load(f)

        # Dedup by question_id
        seen_ids = set()
        unique_qs = []
        for q in questions:
            qid = q.get("question_id", "")
            if qid not in seen_ids:
                seen_ids.add(qid)
                q["_comp"] = comp
                unique_qs.append(q)

        all_qs_map = {q["question_id"]: q for q in unique_qs}

        # Filter: chỉ review câu chưa có _qc_enhanced (câu mới chưa qua QC)
        to_review = unique_qs
        if only_new:
            to_review = [q for q in unique_qs if not q.get("qc_reviewed")]
            print(f"  Only-new: {len(to_review)}/{len(unique_qs)} questions chua duoc review")

        if sample and len(to_review) > sample:
            to_review = random.sample(to_review, sample)
            print(f"  Sampling {sample}/{len(unique_qs)} questions for review")

        if not to_review:
            print(f"  Tat ca da duoc review truoc do, bo qua.")
            continue

        print(f"  Questions to review: {len(to_review)}")

        # Load reference
        reference = load_reference(comp)
        if not reference:
            print(f"  WARNING: No reference doc for {comp}")

        # Review từng câu
        reviewed_qs = []
        for i, q in enumerate(to_review):
            qid   = q.get("question_id", "?")
            diff  = q.get("difficulty_label", "?")
            qtext = q.get("question_text", "")

            # Retrieve context
            context = retrieve_context(reference, qtext)

            print(f"  [{i+1:3d}/{len(unique_qs)}] {qid} ({diff})", end=" ", flush=True)

            review = review_question(client, q, context)
            decision = review.get("decision", "PASS")

            print(f"→ {decision}  {review.get('reason','')[:60]}")

            # Apply enhance
            if decision == "ENHANCE":
                q = apply_enhance(q, review)
                total_enhance += 1
            elif decision == "PASS":
                q["qc_reviewed"] = True
                total_pass += 1
            elif decision == "UNREVIEWED":
                total_unreviewed += 1
            else:
                total_fail += 1

            q["_review"] = review
            reviewed_qs.append(q)

            # CSV row
            points = q.get("answers", {}).get("evaluation_points", [])
            csv_rows.append({
                "decision":        decision,
                "reason":          review.get("reason", ""),
                "accuracy":        review.get("accuracy", ""),
                "difficulty_fit":  review.get("difficulty_fit", ""),
                "question_id":     qid,
                "competency":      comp,
                "difficulty":      diff,
                "question_text":   qtext[:120],
                "source_file":     fname,
                "eval_point_1":    points[0] if len(points) > 0 else "",
                "eval_point_2":    points[1] if len(points) > 1 else "",
                "eval_point_3":    points[2] if len(points) > 2 else "",
            })

            time.sleep(0.3)  # rate limit

        # Update all_qs_map với kết quả review, xóa FAIL
        fail_ids = set()
        for q in reviewed_qs:
            qid = q.get("question_id", "")
            decision = q.get("_review", {}).get("decision", "UNREVIEWED")
            if decision == "FAIL":
                fail_ids.add(qid)
            else:
                # Cập nhật enhanced fields vào map
                q_clean = {k: v for k, v in q.items() if not k.startswith("_")}
                all_qs_map[qid] = q_clean

        # Giữ tất cả câu không bị FAIL (kể cả chưa review)
        final_qs = [q for qid, q in all_qs_map.items() if qid not in fail_ids]
        for q in final_qs:
            q.pop("_review", None)
            q.pop("_comp", None)

        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(final_qs, f, ensure_ascii=False, indent=2)

        n_fail = len(fail_ids)
        print(f"\n  Saved {len(final_qs)} questions (removed {n_fail} FAIL)")

    # Xuất CSV
    csv_path = os.path.join(reports_dir, "qc_rag_result.csv")
    fieldnames = ["decision","reason","accuracy","difficulty_fit",
                  "question_id","competency","difficulty","question_text",
                  "source_file","eval_point_1","eval_point_2","eval_point_3"]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    # Summary
    total = total_pass + total_enhance + total_fail + total_unreviewed
    print(f"\n{'='*55}")
    print(f"QC SUMMARY — {total} questions reviewed")
    print(f"{'='*55}")
    print(f"  PASS:        {total_pass:3d} ({total_pass/total*100:.1f}%)")
    print(f"  ENHANCE:     {total_enhance:3d} ({total_enhance/total*100:.1f}%)")
    print(f"  FAIL:        {total_fail:3d} ({total_fail/total*100:.1f}%)")
    if total_unreviewed:
        print(f"  UNREVIEWED:  {total_unreviewed:3d} ({total_unreviewed/total*100:.1f}%) ← Claude parse error, giữ lại nhưng cần check")
    print(f"\n  Report: {csv_path}")
    print(f"\nBuoc tiep theo:")
    print(f"  Mo reports/qc_rag_result.csv kiem tra cac cau FAIL/ENHANCE")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all",      action="store_true", help="Review tất cả generated files")
    parser.add_argument("--comp",     help="Chỉ review 1 competency (vd: SQL_DATABASE)")
    parser.add_argument("--sample",   type=int, default=0, help="Test nhanh N câu mỗi file")
    parser.add_argument("--only-new", action="store_true", help="Chỉ review câu chưa qua QC lần nào")
    parser.add_argument("--dry-run",  action="store_true", help="Chỉ đếm số câu sẽ được review, không gọi API")
    args = parser.parse_args()

    if not args.all and not args.comp:
        print("Dung: python utils/data/qc/qc_rag.py --all")
        print("      python utils/data/qc/qc_rag.py --all --only-new        # chi review cau moi")
        print("      python utils/data/qc/qc_rag.py --all --only-new --dry-run  # xem truoc so cau")
        print("      python utils/data/qc/qc_rag.py --comp ANALYTICS_BUSINESS")
        print("      python utils/data/qc/qc_rag.py --all --sample 10")
        return

    only_new = getattr(args, "only_new", False)
    dry_run  = getattr(args, "dry_run", False)

    if dry_run:
        gen_dir = os.path.join(ROOT, "data/raw/question_bank/generated")
        total_new = total_all = 0
        for fname, comp in FILE_TO_COMP.items():
            if args.comp and comp != args.comp:
                continue
            fpath = os.path.join(gen_dir, fname)
            if not os.path.exists(fpath):
                continue
            qs = json.load(open(fpath, encoding="utf-8"))
            n_all = len(qs)
            n_new = len([q for q in qs if not q.get("qc_reviewed")])
            total_all += n_all
            total_new += n_new
            flag = "(new)" if only_new else "(all)"
            count = n_new if only_new else n_all
            print(f"  {comp}: {count}/{n_all} se review {flag}")
        print(f"\nTong: {total_new if only_new else total_all} cau se duoc review")
        return

    run_qc(comp_filter=args.comp, sample=args.sample, only_new=only_new)


if __name__ == "__main__":
    main()
