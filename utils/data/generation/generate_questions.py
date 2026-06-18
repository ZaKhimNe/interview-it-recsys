"""
generate_questions.py — Sinh câu hỏi tự động bằng Gemini 2.5 Flash.

Cách dùng:
  python utils/data/generation/generate_questions.py --comp cloud_storage --role DE
  python utils/data/generation/generate_questions.py --comp python_da --role DA
  python utils/data/generation/generate_questions.py --all        # sinh tất cả theo GENERATION_PLAN

Output: data/raw/question_bank/generated_<comp>.json

Cross-model setup:
  Generate: Gemini 2.5 Flash  (file này)
  Review:   Claude Sonnet     (qc_rag.py)

Yêu cầu:
  pip install google-genai
  Set GEMINI_API_KEY trong environment hoặc file .env
"""

import json, os, re, sys, argparse, time, random
from datetime import date
import google.genai as genai

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.stdout.reconfigure(encoding="utf-8")

# ── API client ────────────────────────────────────────────────────────────────
def get_gemini_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        env_path = os.path.join(ROOT, ".env")
        if os.path.exists(env_path):
            for line in open(env_path, encoding="utf-8"):
                if "GEMINI_API_KEY" in line and "=" in line:
                    key = line.strip().split("=", 1)[1].strip().strip('"')
    if not key:
        raise ValueError("Chua set GEMINI_API_KEY trong .env")
    return key


# ── Thresholds ────────────────────────────────────────────────────────────────
DIFFICULTY_TARGET = {"EASY": 30, "MEDIUM": 40, "HARD": 20}

# ── Competency config (cố định) ───────────────────────────────────────────────
# (role, comp_name, taxonomy_key, skill_groups)
COMP_CONFIG = [
    ("DA", "analytics",       "ANALYTICS_BUSINESS",         ["ANALYTICS_COHORT", "ANALYTICS_FUNNEL", "ANALYTICS_BUSINESS"]),
    ("DA", "bi_tools",        "BI_VISUALIZATION",           ["TOOL_POWER_BI", "TOOL_TABLEAU", "BI_VISUALIZATION"]),
    ("DA", "statistics",      "STATISTICS_EXPERIMENTATION", ["STAT_AB_TESTING", "STAT_HYPOTHESIS_TESTING", "STAT_CONFIDENCE_INTERVAL"]),
    ("DA", "python_da",       "PYTHON_ANALYTICS",           ["PYTHON_PANDAS", "PYTHON_ANALYTICS", "LANG_PYTHON"]),
    ("DS", "evaluation",      "EVALUATION_METRICS",         ["EVALUATION_METRICS", "EVAL_CROSS_VALIDATION", "METRIC_F1_SCORE"]),
    ("DS", "data_eng_ds",     "DATA_PREPROCESSING",         ["DATA_PREPROCESSING", "FEATURE_ENGINEERING", "ENCODING_TECHNIQUES", "IMBALANCED_DATA_HANDLING"]),
    ("DS", "deep_learning",   "DEEP_LEARNING",              ["DL_TRAINING", "DL_CNN", "DL_UNSUPERVISED", "DL_FUNDAMENTALS"]),
    ("DS", "nlp",             "NLP",                        ["NLP", "NLP_PREPROCESSING", "NLP_EVALUATION"]),
    ("DS", "mlops_ts",        "TIME_SERIES",                ["ML_TIME_SERIES", "TIME_SERIES"]),
    ("DS", "mlops_ts",        "MLOPS",                      ["ML_MLOPS", "ML_MONITORING", "ML_EXPLAINABILITY"]),
    ("DE", "pipelines",       "DATA_PIPELINE",              ["PIPE_CDC", "PIPE_ELT", "PIPE_ETL", "PIPE_PERFORMANCE", "PIPE_ORCHESTRATION"]),
    ("DE", "data_architecture","DATA_ARCHITECTURE_MODELING",["DATA_WAREHOUSE", "DATA_LAKE", "MODELING_SCD", "MODELING_STAR_SCHEMA", "ARCH_DATA_ARCHITECTURE"]),
    ("DE", "databases",       "DATABASE_INTERNALS",         ["DATABASE_INTERNALS", "DATABASE_INDEXING", "DATABASE_SCALING", "DB_ACID"]),
    ("DE", "system",          "SYSTEM_ARCHITECTURE",        ["SYSTEM_ARCHITECTURE"]),
    ("DE", "cloud_storage",   "BIG_DATA_CLOUD_TOOLS",       ["CLOUD_AWS", "CLOUD_GCP", "CLOUD_S3", "FORMAT_PARQUET", "FORMAT_AVRO", "DEVOPS_DOCKER"]),
]


def compute_generation_plan(all_questions: list) -> list:
    """
    Tính số câu còn thiếu theo cách đếm nhất quán với distribution table:
    mỗi câu chỉ được đếm 1 lần, dưới primary skill group (skill_group đầu tiên khớp role).
    Returns: [(role, comp_name, skill_groups, need_easy, need_med, need_hard)]
    """
    from collections import Counter, defaultdict
    # taxonomy_key → role lookup (built from COMP_CONFIG)
    COMP_CONFIG_ROLE = {taxonomy_key: role for role, _, taxonomy_key, _ in COMP_CONFIG}

    # Build primary-skill-group counts (same method as distribution_type.html)
    psg_diff: dict = defaultdict(lambda: Counter())
    for q in all_questions:
        role = (q.get("roles") or {}).get("primary", "")
        sgs  = q.get("skill_groups") or []
        psg  = next((sg for sg in sgs if sg in COMP_CONFIG_ROLE and COMP_CONFIG_ROLE[sg] == role), None)
        if psg:
            psg_diff[psg][q.get("difficulty_label", "")] += 1

    plan = []
    for role, comp, taxonomy_key, skill_groups in COMP_CONFIG:
        diff = psg_diff[taxonomy_key]
        ne = max(0, DIFFICULTY_TARGET["EASY"]   - diff.get("EASY", 0))
        nm = max(0, DIFFICULTY_TARGET["MEDIUM"] - diff.get("MEDIUM", 0))
        nh = max(0, DIFFICULTY_TARGET["HARD"]   - diff.get("HARD", 0))
        if ne + nm + nh > 0:
            plan.append((role, comp, skill_groups, ne, nm, nh))
    return plan


def load_all_questions() -> list:
    """Load toàn bộ câu hỏi từ question_bank.json (single source of truth)."""
    bank_path = os.path.join(ROOT, "data/raw/question_bank/question_bank.json")
    if os.path.exists(bank_path):
        with open(bank_path, encoding="utf-8") as f:
            return json.load(f)
    return []


# GENERATION_PLAN được tính động khi chạy — không hardcode số câu
GENERATION_PLAN = []  # placeholder, sẽ được compute trong main()

# ── Mô tả competency để đưa vào prompt ───────────────────────────────────────
COMP_DESCRIPTION = {
    "cloud_storage":    "Cloud storage, AWS S3, GCP Cloud Storage, file formats Parquet và Avro cho Data Engineering",
    "python_da":        "Python cho Data Analyst: Pandas, NumPy, xử lý DataFrame, tính toán và phân tích dữ liệu",
    "analytics":        "Phân tích dữ liệu kinh doanh: Cohort Analysis, Funnel Analysis, RFM, Data Visualization",
    "bi_tools":         "BI Tools: Power BI (DAX, Relationships, Report), Tableau (Dashboard, Calculations)",
    "data_eng_ds":      "Data Engineering cho DS: Feature Engineering, Data Preprocessing, Encoding, xử lý Imbalanced Data",
    "mlops_ts":         "MLOps và Time Series: deploy model, monitoring drift, time series forecasting",
    "system":           "System Architecture và DevOps: Docker, container, system design cho data pipeline",
    "nlp":              "Natural Language Processing: preprocessing text, NLP models, evaluation metrics",
    "python_da_ds":     "Python nâng cao cho DS: OOP, generators, decorators, performance optimization",
    "evaluation":       "Model Evaluation: metrics (F1, AUC-ROC), cross-validation, classification report",
    "statistics":       "Thống kê cho DA: A/B Testing, Hypothesis Testing, Confidence Interval",
    "pipelines":        "Data Pipelines: CDC, ELT/ETL patterns, pipeline performance optimization",
    "deep_learning":    "Deep Learning nâng cao: training tricks, CNN architectures, unsupervised DL",
    "databases":        "Database internals: indexing strategies, database scaling, performance tuning",
}

DIFFICULTY_GUIDE = {
    "EASY":   ("2", "Định nghĩa khái niệm cơ bản, câu hỏi 1 bước suy luận, người mới bắt đầu trả lời được"),
    "MEDIUM": ("4", "Áp dụng vào tình huống thực tế, so sánh trade-off, cần giải thích WHY, 2-3 bước suy luận"),
    "HARD":   ("7", "Thiết kế hệ thống, edge case phức tạp, debug, tối ưu performance, đòi hỏi kinh nghiệm thực chiến"),
}

QUESTION_TYPES = ["THEORY", "SCENARIO", "PRACTICAL"]


def build_prompt(role: str, comp: str, skill_groups: list,
                 n_easy: int, n_medium: int, n_hard: int,
                 existing_questions: list) -> str:
    desc = COMP_DESCRIPTION.get(comp, comp)
    today = date.today().isoformat()

    # Few-shot: lấy tối đa 3 câu hiện có để model biết format
    few_shot = ""
    if existing_questions:
        samples = random.sample(existing_questions, min(3, len(existing_questions)))
        few_shot = "\n\nVí dụ format câu hỏi hiện có (KHÔNG được trùng):\n"
        for q in samples:
            few_shot += f"- [{q.get('difficulty_label')}] {q.get('question_text','')}\n"

    batch = []
    if n_easy   > 0: batch.append(f"{n_easy} câu EASY (score=2)")
    if n_medium > 0: batch.append(f"{n_medium} câu MEDIUM (score=4)")
    if n_hard   > 0: batch.append(f"{n_hard} câu HARD (score=7)")

    skill_groups_str = ", ".join(skill_groups)

    return f"""Bạn là chuyên gia phỏng vấn kỹ thuật cho vị trí {role} với 10 năm kinh nghiệm.

Nhiệm vụ: Sinh {n_easy + n_medium + n_hard} câu hỏi phỏng vấn về chủ đề: {desc}

Phân bổ:
- {chr(10).join(batch)}

Tiêu chí độ khó:
- EASY (score=2): {DIFFICULTY_GUIDE['EASY'][1]}
- MEDIUM (score=4): {DIFFICULTY_GUIDE['MEDIUM'][1]}
- HARD (score=7): {DIFFICULTY_GUIDE['HARD'][1]}

Skill groups hợp lệ cho chủ đề này: {skill_groups_str}
Chọn skill_group phù hợp nhất cho từng câu từ danh sách trên.

Quy tắc bắt buộc:
1. Câu hỏi bằng tiếng Việt, đáp án tiếng Việt
2. Mỗi câu có đúng 3 evaluation_points (tiêu chí chấm điểm ngắn gọn)
3. KHÔNG trùng lặp với câu hỏi đã có
4. question_type chọn từ: THEORY, SCENARIO, PRACTICAL
5. Câu SCENARIO bắt đầu bằng tình huống cụ thể ("Bạn đang làm...", "Công ty có...")
6. Câu HARD phải có chiều sâu kỹ thuật thực sự, không chỉ định nghĩa{few_shot}

Output: JSON array hợp lệ, KHÔNG có text thừa ngoài JSON. Format mỗi câu:
{{
  "question_id": "GEN_{role}_{comp.upper()}_001",
  "question_text": "...",
  "roles": {{"primary": "{role}", "secondary": []}},
  "difficulty_label": "EASY|MEDIUM|HARD",
  "difficulty_score": 2,
  "question_type": "THEORY|SCENARIO|PRACTICAL",
  "skill_groups": ["{skill_groups[0]}"],
  "skill_tags": ["{skill_groups[0]}"],
  "answers": {{
    "detailed": "Giải thích đầy đủ...",
    "evaluation_points": ["Điểm 1", "Điểm 2", "Điểm 3"]
  }},
  "metadata": {{
    "language": "vi",
    "source": "gemini_generated",
    "version": "v1.0",
    "created_at": "{today}"
  }}
}}"""


def call_gemini(gemini_key: str, prompt: str, max_retries: int = 3) -> list:
    """Gọi Gemini API và parse JSON. Retry nếu lỗi."""
    client = genai.Client(api_key=gemini_key)
    full_prompt = "Bạn là chuyên gia tạo câu hỏi phỏng vấn kỹ thuật. Chỉ trả về JSON array hợp lệ, không có text thừa.\n\n" + prompt
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=full_prompt,
            )
            content = resp.text.strip()
            # Strip markdown code blocks nếu có
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"  [attempt {attempt+1}] JSON parse error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            print(f"  [attempt {attempt+1}] API error: {e}")
            if attempt < max_retries - 1:
                time.sleep(15)
    return []


# ── Validation ────────────────────────────────────────────────────────────────
REQUIRED_FIELDS = ["question_id", "question_text", "roles", "difficulty_label",
                   "difficulty_score", "question_type", "skill_groups", "answers"]
VALID_DIFFICULTIES = {"EASY", "MEDIUM", "HARD"}
VALID_TYPES = {"THEORY", "SCENARIO", "PRACTICAL"}
SCORE_MAP = {"EASY": 2, "MEDIUM": 4, "HARD": 7}


def validate(q: dict, skill_groups_allowed: list, existing_texts: set) -> tuple[bool, str]:
    # Kiểm tra field bắt buộc
    for f in REQUIRED_FIELDS:
        if f not in q:
            return False, f"Missing field: {f}"

    # Độ dài câu hỏi
    if len(q.get("question_text", "")) < 15:
        return False, "question_text quá ngắn"

    # Difficulty hợp lệ
    diff = q.get("difficulty_label", "")
    if diff not in VALID_DIFFICULTIES:
        return False, f"difficulty_label không hợp lệ: {diff}"

    # difficulty_score khớp label
    expected_score = SCORE_MAP[diff]
    if q.get("difficulty_score") != expected_score:
        q["difficulty_score"] = expected_score  # auto-fix

    # question_type hợp lệ
    if q.get("question_type") not in VALID_TYPES:
        return False, f"question_type không hợp lệ: {q.get('question_type')}"

    # skill_groups nằm trong allowed list
    sg = q.get("skill_groups", [])
    if not sg:
        return False, "skill_groups rỗng"
    if sg[0] not in skill_groups_allowed:
        # Thử fix: dùng skill_group đầu tiên của allowed list
        q["skill_groups"] = [skill_groups_allowed[0]]
        q["skill_tags"]   = [skill_groups_allowed[0]]

    # evaluation_points >= 3
    pts = q.get("answers", {}).get("evaluation_points", [])
    if len(pts) < 3:
        return False, f"evaluation_points chỉ có {len(pts)} (cần >= 3)"

    # detailed answer không rỗng
    if len(q.get("answers", {}).get("detailed", "")) < 20:
        return False, "answers.detailed quá ngắn"

    # Không trùng câu hỏi hiện có
    text_key = re.sub(r'\s+', ' ', q["question_text"].lower().strip())
    if text_key in existing_texts:
        return False, "Trùng câu hỏi đã có"
    existing_texts.add(text_key)

    return True, "OK"


def load_existing_for_comp(comp: str) -> list:
    """Load câu hỏi đã có để tránh trùng và làm few-shot."""
    import json, os, re
    SKILL_GROUP_TO_COMPETENCY_LOCAL = {
        'PYTHON_PANDAS':'python_da','PYTHON_ANALYTICS':'python_da','LANG_PYTHON':'python_da',
        'TOOL_POWER_BI':'bi_tools','TOOL_TABLEAU':'bi_tools','BI_VISUALIZATION':'bi_tools',
        'CLOUD_AWS':'cloud_storage','CLOUD_GCP':'cloud_storage','CLOUD_S3':'cloud_storage',
        'FORMAT_AVRO':'cloud_storage','FORMAT_PARQUET':'cloud_storage',
        'ANALYTICS_COHORT':'analytics','ANALYTICS_FUNNEL':'analytics','ANALYTICS_BUSINESS':'analytics',
        'DATA_VISUALIZATION':'analytics','BI_CONCEPTS':'analytics','DAX_FUNDAMENTALS':'analytics','ANALYTICS_RFM':'analytics',
        'DATA_PREPROCESSING':'data_eng_ds','DATA_CLEANING':'data_eng_ds','FEATURE_ENGINEERING':'data_eng_ds',
        'ENCODING_TECHNIQUES':'data_eng_ds','IMBALANCED_DATA_HANDLING':'data_eng_ds',
        'TIME_SERIES':'mlops_ts','ML_TIME_SERIES':'mlops_ts','ML_MLOPS':'mlops_ts','ML_MONITORING':'mlops_ts',
        'SYSTEM_ARCHITECTURE':'system','DEVOPS_DOCKER':'system',
        'NLP':'nlp','NLP_PREPROCESSING':'nlp','NLP_EVALUATION':'nlp',
        'EVALUATION_METRICS':'evaluation','EVAL_CROSS_VALIDATION':'evaluation',
        'EVAL_CLASSIFICATION_REPORT':'evaluation','METRIC_F1_SCORE':'evaluation',
        'STAT_AB_TESTING':'statistics','STAT_HYPOTHESIS_TESTING':'statistics',
        'STAT_CONFIDENCE_INTERVAL':'statistics','STAT_FUNDAMENTALS':'statistics',
        'DATA_PIPELINE':'pipelines','PIPE_CDC':'pipelines','PIPE_ELT':'pipelines','PIPE_ETL':'pipelines','PIPE_PERFORMANCE':'pipelines',
        'DL_TRAINING':'deep_learning','DL_CNN':'deep_learning','DL_UNSUPERVISED':'deep_learning',
        'DATABASE_INTERNALS':'databases','DATABASE_INDEXING':'databases','DATABASE_SCALING':'databases','DATABASE_PERFORMANCE':'databases',
    }
    existing = []
    sources = ['data/raw/question_bank/question_bank.json','data/raw/question_bank/scraped/scraped_github.json',
               'data/raw/question_bank/scraped/scraped_youssef.json','data/raw/question_bank/scraped/scraped_sql.json','data/raw/question_bank/scraped/converted_tf_fb.json']
    for path in sources:
        fp = os.path.join(ROOT, path)
        if not os.path.exists(fp): continue
        try:
            with open(fp,'rb') as f: raw=f.read()
            data=json.loads(raw.rstrip(b'\x00').decode('utf-8'))
            qs=data if isinstance(data,list) else data.get('questions',[])
            for q in qs:
                grp=(q.get('skill_groups') or q.get('skill_tags') or ['?'])[0]
                if SKILL_GROUP_TO_COMPETENCY_LOCAL.get(grp)==comp:
                    existing.append(q)
        except: pass
    # Cũng load generated file hiện có để tránh trùng nội dung
    gen_path = os.path.join(ROOT, f"data/raw/question_bank/generated/generated_{comp}.json")
    if os.path.exists(gen_path):
        with open(gen_path, encoding='utf-8') as f:
            existing.extend(json.load(f))
    return existing


def generate_comp(gemini_key: str, role: str, comp: str, skill_groups: list,
                  n_easy: int, n_medium: int, n_hard: int) -> list:
    """Sinh câu hỏi cho 1 competency, chia batch 10 câu."""
    print(f"\n{'='*60}")
    print(f"Generating: {role}/{comp}  EASY={n_easy} MED={n_medium} HARD={n_hard}")
    print(f"{'='*60}")

    existing = load_existing_for_comp(comp)
    existing_texts = {re.sub(r'\s+', ' ', q.get('question_text','').lower().strip()) for q in existing}
    print(f"  Existing questions for this comp: {len(existing)}")

    # Sinh theo batch: mỗi batch tối đa 10 câu
    all_generated = []
    BATCH_SIZE = 5

    # Tìm ID lớn nhất trong file generated hiện có để tiếp nối
    import re as _re
    gen_path = os.path.join(ROOT, f"data/raw/question_bank/generated/generated_{comp}.json")
    id_start = 1
    if os.path.exists(gen_path):
        with open(gen_path, encoding='utf-8') as f:
            existing_gen_qs = json.load(f)
        nums = []
        for q in existing_gen_qs:
            m = _re.search(r'_(\d+)$', q.get('question_id', ''))
            if m: nums.append(int(m.group(1)))
        if nums: id_start = max(nums) + 1

    # Tạo danh sách (diff, count) để chia batch
    diff_queue = (
        [("EASY", 1)] * n_easy +
        [("MEDIUM", 1)] * n_medium +
        [("HARD", 1)] * n_hard
    )
    random.shuffle(diff_queue)

    # Chia thành batches
    batches = []
    i = 0
    while i < len(diff_queue):
        batch_diffs = diff_queue[i:i+BATCH_SIZE]
        be = sum(1 for d,_ in batch_diffs if d=="EASY")
        bm = sum(1 for d,_ in batch_diffs if d=="MEDIUM")
        bh = sum(1 for d,_ in batch_diffs if d=="HARD")
        batches.append((be, bm, bh))
        i += BATCH_SIZE

    for batch_idx, (be, bm, bh) in enumerate(batches):
        print(f"\n  Batch {batch_idx+1}/{len(batches)}: EASY={be} MED={bm} HARD={bh}")
        prompt = build_prompt(role, comp, skill_groups, be, bm, bh, existing)
        raw_qs = call_gemini(gemini_key, prompt)

        if not raw_qs:
            print("  [WARN] Batch returned empty, skipping")
            continue

        # Validate từng câu
        passed, failed = 0, 0
        for idx, q in enumerate(raw_qs):
            # Đảm bảo question_id unique
            q["question_id"] = f"GEN_{role}_{comp.upper()}_{id_start+len(all_generated)+idx:03d}"
            ok, reason = validate(q, skill_groups, existing_texts)
            if ok:
                all_generated.append(q)
                passed += 1
            else:
                print(f"  [SKIP] Q{idx+1}: {reason}")
                failed += 1

        print(f"  Batch result: {passed} passed, {failed} failed")
        time.sleep(6)  # rate limit: 10 RPM = 1 req/6s

    print(f"\n  Total generated for {comp}: {len(all_generated)} questions")
    return all_generated


def save_generated(questions: list, comp: str):
    out_path = os.path.join(ROOT, f"data/raw/question_bank/generated/generated_{comp}.json")
    # Merge với file cũ nếu có
    existing_gen = []
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            existing_gen = json.load(f)
        print(f"  Merging with {len(existing_gen)} existing generated questions")

    merged = existing_gen + questions
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"  Saved -> {out_path}  ({len(merged)} total)")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--comp",  help="Competency cần sinh (vd: cloud_storage)")
    parser.add_argument("--role",  help="Role (DA/DS/DE)")
    parser.add_argument("--all",   action="store_true", help="Sinh tất cả theo GENERATION_PLAN")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ show plan, không gọi API")
    args = parser.parse_args()

    if args.dry_run:
        all_questions = load_all_questions()
        dynamic_plan  = compute_generation_plan(all_questions)
        print("=== GENERATION PLAN (tu dong tinh tu data hien co) ===")
        print(f"Target: EASY>={DIFFICULTY_TARGET['EASY']} MEDIUM>={DIFFICULTY_TARGET['MEDIUM']} HARD>={DIFFICULTY_TARGET['HARD']}")
        print()
        total = 0
        for role, comp, sgs, ne, nm, nh in dynamic_plan:
            n = ne+nm+nh
            total += n
            print(f"  {role:2} / {comp:20} | EASY=+{ne:2} MED=+{nm:2} HARD=+{nh:2} | can sinh={n:3}")
        if not dynamic_plan:
            print("  Tat ca competency da du nguong!")
        print(f"\nTong can sinh them: {total} cau")
        return

    # Tính động số câu còn thiếu
    all_questions = load_all_questions()
    dynamic_plan  = compute_generation_plan(all_questions)

    gemini_key = get_gemini_key()

    if args.all:
        plan = dynamic_plan
    elif args.comp and args.role:
        plan = [p for p in dynamic_plan if p[1] == args.comp and p[0] == args.role]
        if not plan:
            print(f"[{args.role}/{args.comp}] Da du so luong, khong can sinh them.")
            return
    else:
        parser.print_help()
        return

    summary = []
    for role, comp, skill_groups, ne, nm, nh in plan:
        if ne + nm + nh == 0:
            continue
        questions = generate_comp(gemini_key, role, comp, skill_groups, ne, nm, nh)
        if questions:
            path = save_generated(questions, comp)
            summary.append((role, comp, len(questions), path))
        time.sleep(2)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for role, comp, n, path in summary:
        print(f"  {role}/{comp}: {n} questions -> {os.path.basename(path)}")
    total = sum(n for _,_,n,_ in summary)
    print(f"\nTong da sinh: {total} cau")


if __name__ == "__main__":
    main()
