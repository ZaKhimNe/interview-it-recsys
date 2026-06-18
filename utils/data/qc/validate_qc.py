"""
validate_qc.py — 3-tier validation cho QC pipeline.

Tang 1 — Calibrate reviewer (human lam gold standard):
  --sample    : Tao 153 cau stratified (17 KC x 3 diff x 3/cell) de human review
  --compute   : Tinh Cohen Kappa + Precision/Recall sau khi human label

Tang 2 — Automated proxy metrics (khong can human):
  --coverage  : 17 KC x 3 difficulty co du cau khong (>= 5/cell)
  --bleu      : Pairwise BLEU de do diversity (target avg < 0.30)
  --difficulty-calibration : So sanh difficulty_tag vs actual quality_score trong interaction log
  --length-dist : Phan bo do dai cau hoi (phat hien outlier qua ngan/qua dai)

Tang 3 — Pipeline agreement test:
  --pipeline-agreement : Lay 50 cau da human-label, chay qua ca 2 luong
                         (haiku_decision vs human), so sanh agreement

Chay:
  python utils/data/qc/validate_qc.py --sample
  python utils/data/qc/validate_qc.py --compute
  python utils/data/qc/validate_qc.py --coverage
  python utils/data/qc/validate_qc.py --bleu
  python utils/data/qc/validate_qc.py --difficulty-calibration
  python utils/data/qc/validate_qc.py --length-dist
  python utils/data/qc/validate_qc.py --pipeline-agreement
"""

import os, sys, json, csv, random, argparse, math
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

ROOT             = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BANK_PATH        = os.path.join(ROOT, "data/raw/question_bank/question_bank.json")
QC_CSV_PATH      = os.path.join(ROOT, "data/raw/question_bank/qc_rag_result.csv")
INTERACTION_PATH = os.path.join(ROOT, "data/simulation/interaction_log.json")
OUT_DIR          = os.path.join(ROOT, "data/raw/question_bank")
SAMPLE_CSV       = os.path.join(OUT_DIR, "human_review_sample.csv")
RESULT_CSV       = os.path.join(OUT_DIR, "human_review_result.csv")

SEED = 42

# Chỉ các KC có câu generated (bỏ SQL_DATABASE và ALGORITHM_THEORY — đã đủ từ scrape)
COMPETENCIES = [
    "BI_VISUALIZATION", "STATISTICS_EXPERIMENTATION",
    "ANALYTICS_BUSINESS", "PYTHON_ANALYTICS",
    "EVALUATION_METRICS", "DATA_PREPROCESSING", "DEEP_LEARNING",
    "NLP", "TIME_SERIES", "MLOPS", "DATA_PIPELINE",
    "DATA_ARCHITECTURE_MODELING", "BIG_DATA_CLOUD_TOOLS",
    "DATABASE_INTERNALS", "SYSTEM_ARCHITECTURE",
]
DIFFICULTIES = ["EASY", "MEDIUM", "HARD"]
PER_CELL = 2  # 15 KC x 3 diff x 2/cell = 90 cau, CI = +-0.103

# Chỉ sample từ câu generated để Haiku có thể judge hết
GENERATED_SOURCES = {"gemini_generated"}


# ── Load data ─────────────────────────────────────────────────────────────────
def load_bank():
    with open(BANK_PATH, encoding="utf-8") as f:
        return json.load(f)

def load_qc_decisions():
    """Load PASS/FAIL/ENHANCE decision từ qc_rag_result.csv."""
    decisions = {}
    if not os.path.exists(QC_CSV_PATH):
        return decisions
    with open(QC_CSV_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            qid = row.get("question_id", "")
            dec = row.get("decision", "")
            if qid:
                decisions[qid] = dec
    return decisions


# ── Step 1: Stratified sample ─────────────────────────────────────────────────
def cmd_sample(per_cell: int = PER_CELL, n_kc: int = 11):
    random.seed(SEED)
    questions = load_bank()
    qc_decisions = load_qc_decisions()

    # Chỉ lấy câu generated (prefix GEN_), scraped không cần Haiku review
    questions = [q for q in questions if q.get("question_id", "").startswith("GEN_")]

    # Group by (competency, difficulty)
    cells = defaultdict(list)
    for q in questions:
        comp = next((sg for sg in q.get("skill_groups", []) if sg in COMPETENCIES), None)
        diff = q.get("difficulty_label", "")
        if comp and diff in DIFFICULTIES:
            cells[(comp, diff)].append(q)

    # Chọn n_kc KC có nhiều câu nhất để đảm bảo đủ per_cell
    kc_pool = sorted(
        COMPETENCIES,
        key=lambda c: sum(len(cells.get((c, d), [])) for d in DIFFICULTIES),
        reverse=True
    )[:n_kc]

    sampled = []
    missing_cells = []
    for comp in kc_pool:
        for diff in DIFFICULTIES:
            pool = cells.get((comp, diff), [])
            if len(pool) < per_cell:
                missing_cells.append(f"{comp}/{diff} (chi co {len(pool)})")
                picks = pool
            else:
                picks = random.sample(pool, per_cell)

            for q in picks:
                qid = q.get("question_id", "")
                sampled.append({
                    "question_id":      qid,
                    "competency":       comp,
                    "difficulty":       diff,
                    "question_type":    q.get("question_type", ""),
                    "question_text":    q.get("question_text", ""),
                    "detailed_answer":  q.get("answers", {}).get("detailed", ""),
                    "eval_point_1":     (q.get("answers", {}).get("evaluation_points") or [""])[0],
                    "eval_point_2":     (q.get("answers", {}).get("evaluation_points") or ["",""])[1] if len(q.get("answers", {}).get("evaluation_points") or []) > 1 else "",
                    "eval_point_3":     (q.get("answers", {}).get("evaluation_points") or ["","",""])[2] if len(q.get("answers", {}).get("evaluation_points") or []) > 2 else "",
                    "sonnet_decision":  qc_decisions.get(qid, "NOT_REVIEWED"),
                    "human_label":      "",  # ban tu dien: PASS hoac FAIL
                    "human_note":       "",  # tuy chon: ghi chu them
                })

    # Export CSV
    fieldnames = ["question_id", "competency", "difficulty", "question_type",
                  "question_text", "detailed_answer",
                  "eval_point_1", "eval_point_2", "eval_point_3",
                  "sonnet_decision", "human_label", "human_note"]

    with open(SAMPLE_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sampled)

    print(f"Stratified sample: {len(sampled)} cau ({len(kc_pool)} KC x {len(DIFFICULTIES)} diff x {per_cell} cau/cell) — chi generated")
    if missing_cells:
        print(f"\nWARNING — cells thieu cau (< {per_cell}):")
        for c in missing_cells:
            print(f"  {c}")
    print(f"\nSaved -> {SAMPLE_CSV}")
    print(f"\nHuong dan:")
    print(f"  1. Mo file CSV tren Excel/Google Sheets")
    print(f"  2. Dien cot 'human_label': PASS hoac FAIL cho tung cau")
    print(f"  3. (Tuy chon) Ghi chu 'human_note' neu muon")
    print(f"  4. Luu lai va chay: python utils/data/qc/validate_qc.py --compute")


# ── Step 2: Compute metrics ───────────────────────────────────────────────────
def cmd_compute():
    if not os.path.exists(SAMPLE_CSV):
        print("Chua co file sample. Chay --sample truoc.")
        return

    # Load Haiku decisions tu qc_rag_result.csv (moi nhat)
    haiku_decisions = load_qc_decisions()

    rows = []
    with open(SAMPLE_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    # Filter cac cau da co human_label
    labeled = [r for r in rows if r.get("human_label", "").strip().upper() in ("PASS", "FAIL")]
    if not labeled:
        print("Chua co cau nao duoc label. Dien cot 'human_label' trong CSV truoc.")
        return

    print(f"Labeled: {len(labeled)}/{len(rows)} cau")

    # Lay Haiku decision tu qc_rag_result.csv, fallback sang sonnet_decision trong CSV
    def get_haiku_decision(row):
        qid = row.get("question_id", "")
        dec = haiku_decisions.get(qid, row.get("sonnet_decision", "NOT_REVIEWED"))
        return dec

    # Haiku decision → binary (PASS/ENHANCE = PASS, FAIL = FAIL, NOT_REVIEWED = FAIL)
    def haiku_binary(dec):
        return "PASS" if dec.strip().upper() in ("PASS", "ENHANCE") else "FAIL"

    human   = [r["human_label"].strip().upper() for r in labeled]
    sonnet  = [haiku_binary(get_haiku_decision(r)) for r in labeled]

    # Report phan tram NOT_REVIEWED
    n_not_reviewed = sum(1 for r in labeled if get_haiku_decision(r).upper() == "NOT_REVIEWED")
    if n_not_reviewed > 0:
        print(f"  WARNING: {n_not_reviewed} cau chua co Haiku decision (NOT_REVIEWED) → tinh la FAIL")

    # Cohen's Kappa
    def cohen_kappa(y1, y2):
        labels = list(set(y1 + y2))
        n = len(y1)
        po = sum(a == b for a, b in zip(y1, y2)) / n
        pe = sum(
            (y1.count(l) / n) * (y2.count(l) / n)
            for l in labels
        )
        return (po - pe) / (1 - pe) if pe < 1 else 1.0

    kappa = cohen_kappa(human, sonnet)
    if kappa >= 0.80:   interp = "Almost perfect (>= 0.80) -- Rat tot"
    elif kappa >= 0.60: interp = "Substantial (0.60-0.79) -- Du tin cay"
    elif kappa >= 0.40: interp = "Moderate (0.40-0.59) -- Chap nhan duoc"
    elif kappa >= 0.20: interp = "Fair (0.20-0.39) -- Can cai thien"
    else:               interp = "Poor (< 0.20) -- Khong du tin cay"

    # Precision / Recall (human PASS = positive)
    tp = sum(h == "PASS" and s == "PASS" for h, s in zip(human, sonnet))
    fp = sum(h == "FAIL" and s == "PASS" for h, s in zip(human, sonnet))
    fn = sum(h == "PASS" and s == "FAIL" for h, s in zip(human, sonnet))
    tn = sum(h == "FAIL" and s == "FAIL" for h, s in zip(human, sonnet))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # CI kappa (±1.96 * SE)
    import math
    se = math.sqrt(max(0, kappa * (1 - kappa)) / len(labeled)) if len(labeled) > 0 else 0
    ci = 1.96 * se

    print(f"\n{'='*50}")
    print(f"QC VALIDATION METRICS")
    print(f"{'='*50}")
    print(f"  Sample size:   {len(labeled)} cau")
    print(f"  Cohen Kappa:   {kappa:.3f}  ({interp})")
    print(f"  CI (95%):      +/- {ci:.3f}")
    print(f"")
    print(f"  TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"  Precision:     {precision:.3f}  (trong so Sonnet PASS, bao nhieu Human cung PASS)")
    print(f"  Recall:        {recall:.3f}  (trong so Human PASS, Sonnet bat duoc bao nhieu)")
    print(f"  F1:            {f1:.3f}")

    # Breakdown by difficulty
    print(f"\n  --- Kappa by difficulty ---")
    for diff in DIFFICULTIES:
        subset = [(h, s) for h, s, r in zip(human, sonnet, labeled) if r["difficulty"] == diff]
        if len(subset) >= 2:
            h_sub = [x[0] for x in subset]
            s_sub = [x[1] for x in subset]
            k = cohen_kappa(h_sub, s_sub)
            print(f"  {diff:8}: kappa={k:.3f}  (n={len(subset)})")

    # Save result
    import shutil
    shutil.copy(SAMPLE_CSV, RESULT_CSV)
    print(f"\nSaved result -> {RESULT_CSV}")


# ── Step 3: Coverage check ────────────────────────────────────────────────────
def cmd_coverage():
    questions = load_bank()
    cells = defaultdict(int)
    for q in questions:
        comp = next((sg for sg in q.get("skill_groups", []) if sg in COMPETENCIES), None)
        diff = q.get("difficulty_label", "")
        if comp and diff in DIFFICULTIES:
            cells[(comp, diff)] += 1

    total_cells = len(COMPETENCIES) * len(DIFFICULTIES)
    cells_ge5   = sum(1 for v in cells.values() if v >= 5)
    cells_empty = [(c, d) for c in COMPETENCIES for d in DIFFICULTIES if cells.get((c, d), 0) == 0]

    print(f"{'='*50}")
    print(f"COVERAGE REPORT")
    print(f"{'='*50}")
    print(f"  Total cells (KC x diff): {total_cells}")
    print(f"  Cells >= 5 cau:          {cells_ge5} ({cells_ge5/total_cells*100:.1f}%)")
    print(f"  Cells empty:             {len(cells_empty)}")
    if cells_empty:
        for c, d in cells_empty:
            print(f"    {c}/{d}")

    print(f"\n  --- Per competency (EASY/MED/HARD) ---")
    for comp in COMPETENCIES:
        counts = [cells.get((comp, d), 0) for d in DIFFICULTIES]
        total  = sum(counts)
        flag   = " <-- THIN" if total < 50 else ""
        print(f"  {comp:35} E={counts[0]:3} M={counts[1]:3} H={counts[2]:3} | total={total:4}{flag}")


# ── Step 4: Pairwise BLEU ─────────────────────────────────────────────────────
def cmd_bleu():
    try:
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        import nltk
        try: nltk.data.find("tokenizers/punkt")
        except: nltk.download("punkt", quiet=True)
    except ImportError:
        print("Can cai nltk: pip install nltk")
        return

    questions = load_bank()
    smoother  = SmoothingFunction().method1

    # Group by competency
    groups = defaultdict(list)
    for q in questions:
        comp = next((sg for sg in q.get("skill_groups", []) if sg in COMPETENCIES), None)
        if comp:
            text = q.get("question_text", "").lower().split()
            if text:
                groups[comp].append(text)

    print(f"{'='*50}")
    print(f"PAIRWISE BLEU (avg per competency)")
    print(f"{'='*50}")
    print(f"  Target: avg BLEU < 0.30 (khong trung lap)")
    print()

    all_scores = []
    for comp in COMPETENCIES:
        texts = groups.get(comp, [])
        if len(texts) < 2:
            print(f"  {comp:35}: skip (< 2 cau)")
            continue
        # Sample toi da 30 cau de tinh nhanh
        sample = texts[:30]
        scores = []
        for i in range(len(sample)):
            for j in range(i+1, len(sample)):
                s = sentence_bleu([sample[i]], sample[j], smoothing_function=smoother)
                scores.append(s)
        avg = sum(scores) / len(scores) if scores else 0
        flag = " <-- CAO (trung lap)" if avg >= 0.30 else ""
        print(f"  {comp:35}: {avg:.3f}{flag}")
        all_scores.extend(scores)

    if all_scores:
        overall = sum(all_scores) / len(all_scores)
        verdict = "OK -- khong trung lap" if overall < 0.30 else "WARN -- co the trung lap"
        print(f"\n  Overall avg BLEU: {overall:.3f}  ({verdict})")


# ── Tang 2: Difficulty calibration ───────────────────────────────────────────
def cmd_difficulty_calibration():
    """
    So sanh difficulty_tag trong question_bank vs actual quality_score trong interaction log.
    Easy question -> user correct rate cao = calibrated tot.
    Neu easy question co correct rate thap -> difficulty tag sai.
    """
    if not os.path.exists(INTERACTION_PATH):
        print(f"Khong tim thay interaction log: {INTERACTION_PATH}")
        print("Chay simulate_interaction.py truoc.")
        return

    with open(INTERACTION_PATH, encoding="utf-8") as f:
        interactions = json.load(f)

    # Group interactions by question_id
    q_stats = defaultdict(lambda: {"total": 0, "correct": 0, "quality_scores": []})
    for row in interactions:
        qid = row.get("question_id", "")
        score = row.get("quality_score", 0)
        q_stats[qid]["total"] += 1
        q_stats[qid]["quality_scores"].append(score)
        if score >= 1:
            q_stats[qid]["correct"] += 1

    # Load question bank de lay difficulty_tag
    questions = load_bank()
    q_diff = {q.get("question_id", ""): q.get("difficulty_label", "") for q in questions}

    # Group correct rate theo difficulty_tag
    diff_correct = defaultdict(list)
    for qid, stats in q_stats.items():
        diff = q_diff.get(qid, "UNKNOWN")
        if stats["total"] >= 3:  # chi tinh cau co du data
            rate = stats["correct"] / stats["total"]
            diff_correct[diff].append(rate)

    print(f"{'='*50}")
    print(f"DIFFICULTY CALIBRATION")
    print(f"{'='*50}")
    print(f"  Ly thuyet: EASY > MEDIUM > HARD ve correct rate")
    print()

    results = {}
    for diff in ["EASY", "MEDIUM", "HARD"]:
        rates = diff_correct.get(diff, [])
        if rates:
            avg = sum(rates) / len(rates)
            results[diff] = avg
            print(f"  {diff:8}: avg correct rate = {avg:.3f}  (n={len(rates)} questions)")
        else:
            print(f"  {diff:8}: no data")

    # Kiem tra thu tu
    if all(k in results for k in ["EASY", "MEDIUM", "HARD"]):
        print()
        if results["EASY"] > results["MEDIUM"] > results["HARD"]:
            print("  OK -- Difficulty tags calibrated dung huong")
        else:
            print("  WARN -- Thu tu correct rate khong dung: EASY > MEDIUM > HARD bi vi pham")
            if results["EASY"] <= results["MEDIUM"]:
                print("    EASY <= MEDIUM: cac cau EASY co the bi gan difficulty sai")
            if results["MEDIUM"] <= results["HARD"]:
                print("    MEDIUM <= HARD: cac cau HARD co the bi gan difficulty sai")


# ── Tang 2: Length distribution ───────────────────────────────────────────────
def cmd_length_dist():
    """
    Phan bo do dai question_text va detailed_answer.
    Phat hien outlier: cau hoi qua ngan (< 20 words) hoac qua dai (> 200 words).
    """
    questions = load_bank()

    q_lengths = []
    a_lengths = []
    short_questions = []
    long_questions  = []

    for q in questions:
        qtext  = q.get("question_text", "")
        detail = q.get("answers", {}).get("detailed", "")
        qlen   = len(qtext.split())
        alen   = len(detail.split()) if detail else 0

        q_lengths.append(qlen)
        a_lengths.append(alen)

        if qlen < 10:
            short_questions.append((q.get("question_id",""), qlen, qtext[:80]))
        elif qlen > 150:
            long_questions.append((q.get("question_id",""), qlen, qtext[:80]))

    def stats(lst):
        if not lst: return {}
        lst_s = sorted(lst)
        n = len(lst_s)
        return {
            "min": lst_s[0], "max": lst_s[-1],
            "avg": sum(lst_s)/n,
            "p25": lst_s[n//4], "p50": lst_s[n//2], "p75": lst_s[3*n//4],
        }

    qs = stats(q_lengths)
    as_ = stats(a_lengths)

    print(f"{'='*50}")
    print(f"LENGTH DISTRIBUTION")
    print(f"{'='*50}")
    print(f"  Total questions: {len(questions)}")
    print()
    print(f"  Question text (words):")
    print(f"    min={qs['min']}  p25={qs['p25']}  p50={qs['p50']}  p75={qs['p75']}  max={qs['max']}  avg={qs['avg']:.1f}")
    print()
    print(f"  Detailed answer (words):")
    print(f"    min={as_['min']}  p25={as_['p25']}  p50={as_['p50']}  p75={as_['p75']}  max={as_['max']}  avg={as_['avg']:.1f}")

    if short_questions:
        print(f"\n  SHORT questions (< 10 words): {len(short_questions)}")
        for qid, ln, txt in short_questions[:10]:
            print(f"    [{ln:3d}w] {qid}: {txt}")
    else:
        print(f"\n  OK -- Khong co question qua ngan (< 10 words)")

    if long_questions:
        print(f"\n  LONG questions (> 150 words): {len(long_questions)}")
        for qid, ln, txt in long_questions[:10]:
            print(f"    [{ln:3d}w] {qid}: {txt}")
    else:
        print(f"\n  OK -- Khong co question qua dai (> 150 words)")


# ── Tang 3: Pipeline agreement test ──────────────────────────────────────────
def cmd_pipeline_agreement():
    """
    Tang 3: Lay cac cau da co human_label trong RESULT_CSV,
    so sanh haiku_decision vs human gold.
    Bao cao: agreement rate, Cohen Kappa, confusion matrix.
    Dung de justify viec dung Claude Haiku lam reviewer.
    """
    if not os.path.exists(RESULT_CSV):
        print("Chua co human_review_result.csv. Chay --sample -> label -> --compute truoc.")
        return

    rows = []
    with open(RESULT_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    labeled = [r for r in rows if r.get("human_label","").strip().upper() in ("PASS","FAIL")]
    if not labeled:
        print("Chua co human label. Dien cot human_label trong CSV truoc.")
        return

    def to_binary(dec):
        return "PASS" if dec.strip().upper() in ("PASS","ENHANCE") else "FAIL"

    human = [r["human_label"].strip().upper() for r in labeled]
    haiku = [to_binary(r.get("sonnet_decision","")) for r in labeled]

    def cohen_kappa(y1, y2):
        labels = list(set(y1 + y2))
        n = len(y1)
        po = sum(a == b for a, b in zip(y1, y2)) / n
        pe = sum((y1.count(l)/n)*(y2.count(l)/n) for l in labels)
        return (po - pe) / (1 - pe) if pe < 1 else 1.0

    kappa = cohen_kappa(human, haiku)
    agree = sum(h == k for h, k in zip(human, haiku)) / len(human)

    tp = sum(h=="PASS" and k=="PASS" for h,k in zip(human,haiku))
    fp = sum(h=="FAIL" and k=="PASS" for h,k in zip(human,haiku))
    fn = sum(h=="PASS" and k=="FAIL" for h,k in zip(human,haiku))
    tn = sum(h=="FAIL" and k=="FAIL" for h,k in zip(human,haiku))

    prec = tp/(tp+fp) if (tp+fp)>0 else 0
    rec  = tp/(tp+fn) if (tp+fn)>0 else 0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0

    se = math.sqrt(kappa*(1-kappa)/len(labeled)) if len(labeled)>0 else 0
    ci = 1.96 * se

    if kappa >= 0.80:   verdict = "Almost perfect -- Pipeline dang tin cay cao"
    elif kappa >= 0.60: verdict = "Substantial -- Du tin cay de dung automated QC"
    elif kappa >= 0.40: verdict = "Moderate -- Can cai thien prompt hoac model"
    else:               verdict = "Poor -- Khong du tin cay, can xem lai pipeline"

    print(f"{'='*50}")
    print(f"PIPELINE AGREEMENT TEST (Tang 3)")
    print(f"{'='*50}")
    print(f"  Reviewer: Claude Haiku 4.5 vs Human gold")
    print(f"  Sample:   {len(labeled)} cau da human-labeled")
    print()
    print(f"  Agreement rate: {agree:.3f}  ({agree*100:.1f}%)")
    print(f"  Cohen Kappa:    {kappa:.3f}  +/- {ci:.3f}")
    print(f"  Verdict:        {verdict}")
    print()
    print(f"  Confusion matrix (Human=row, Haiku=col):")
    print(f"              Haiku PASS  Haiku FAIL")
    print(f"  Human PASS:   {tp:5d}       {fn:5d}")
    print(f"  Human FAIL:   {fp:5d}       {tn:5d}")
    print()
    print(f"  Precision: {prec:.3f}  (Haiku PASS, bao nhieu Human cung PASS?)")
    print(f"  Recall:    {rec:.3f}  (Human PASS, Haiku bat duoc bao nhieu?)")
    print(f"  F1:        {f1:.3f}")
    print()
    if kappa >= 0.60:
        print(f"  -> JUSTIFY: Co the dung Claude Haiku de review toan bo corpus.")
        print(f"     Bao cao trong thesis: Cohen kappa(Haiku vs Human) = {kappa:.3f}")
    else:
        print(f"  -> WARN: Kappa thap. Xem xet:")
        print(f"     1. Cai thien review prompt trong qc_rag.py")
        print(f"     2. Dung model manh hon (Sonnet) cho review")
        print(f"     3. Human review them cau de co ground truth tot hon")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample",                action="store_true", help="[Tang 1] Tao stratified sample CSV de human review")
    parser.add_argument("--compute",               action="store_true", help="[Tang 1] Tinh Cohen Kappa + Precision/Recall sau khi label")
    parser.add_argument("--coverage",              action="store_true", help="[Tang 2] Check coverage cells KC x difficulty")
    parser.add_argument("--bleu",                  action="store_true", help="[Tang 2] Tinh pairwise BLEU de do diversity")
    parser.add_argument("--difficulty-calibration",action="store_true", help="[Tang 2] So sanh difficulty_tag vs actual correct rate")
    parser.add_argument("--length-dist",           action="store_true", help="[Tang 2] Phan bo do dai, phat hien outlier")
    parser.add_argument("--pipeline-agreement",    action="store_true", help="[Tang 3] So sanh Haiku vs Human gold (sau khi da co human label)")
    parser.add_argument("--per-cell", type=int, default=PER_CELL, help="So cau moi cell cho --sample (default=3)")
    parser.add_argument("--n-kc",     type=int, default=15,      help="So KC dua vao sample (default=15 → 90 cau)")
    args = parser.parse_args()

    if args.sample:
        cmd_sample(args.per_cell, getattr(args, "n_kc", 11))
    elif args.compute:
        cmd_compute()
    elif args.coverage:
        cmd_coverage()
    elif args.bleu:
        cmd_bleu()
    elif getattr(args, "difficulty_calibration", False):
        cmd_difficulty_calibration()
    elif getattr(args, "length_dist", False):
        cmd_length_dist()
    elif getattr(args, "pipeline_agreement", False):
        cmd_pipeline_agreement()
    else:
        print("3-tier validation pipeline:")
        print()
        print("  [Tang 1 — Calibrate reviewer]")
        print("  --sample               : Tao 153 cau stratified de human review")
        print("  --compute              : Tinh Cohen Kappa sau khi human label xong")
        print()
        print("  [Tang 2 — Automated proxy metrics]")
        print("  --coverage             : Check KC x difficulty coverage")
        print("  --bleu                 : Pairwise BLEU diversity (target < 0.30)")
        print("  --difficulty-calibration: So difficulty_tag vs correct rate thuc te")
        print("  --length-dist          : Phan bo do dai, phat hien outlier")
        print()
        print("  [Tang 3 — Pipeline agreement]")
        print("  --pipeline-agreement   : Haiku vs Human gold (can --compute truoc)")

if __name__ == "__main__":
    main()
