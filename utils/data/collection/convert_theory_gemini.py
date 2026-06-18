"""
convert_theory_gemini.py — Convert GEN_ questions để đảm bảo mỗi skill có đủ loại câu.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOGIC TỔNG QUAN (đọc đây trước)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mục tiêu: Mỗi skill phải có ít nhất MIN_PER_TYPE câu mỗi loại
          (MC_SINGLE, CODING, TRUE_FALSE) để user không bị nhàm.

Chiến lược: Skill-first — xử lý từng skill, fill đúng loại còn thiếu.

Hai nguồn convert (chỉ GEN_, không đụng scraped):
  THEORY  → TRUE_FALSE  (câu lý thuyết → phát biểu đúng/sai rất tự nhiên)
  THEORY  → MC_SINGLE   (câu lý thuyết → chọn đáp án đúng)
  PRACTICE → CODING     (câu tình huống → viết code giải quyết tự nhiên)
  PRACTICE → MC_SINGLE  (câu tình huống → chọn approach tốt nhất)

  Ưu tiên source theo target type:
    TRUE_FALSE → từ THEORY trước
    CODING     → từ PRACTICE trước
    MC_SINGLE  → từ THEORY trước, fallback sang PRACTICE nếu thiếu

Quy trình mỗi skill:
  1. Đếm số câu hiện có mỗi type
  2. Tính need = max(0, MIN_PER_TYPE - hiện_có)
  3. Với mỗi type còn thiếu: lấy pool phù hợp, stratified sample (3x buffer),
     gọi Gemini từng câu, Gemini tự quyết good_fit=true/false
  4. Nếu good_fit=false → SKIP, lấy câu kế trong buffer
  5. Save sau mỗi skill (crash-safe)

Skip conditions:
  - Skill có tổng < MIN_SKILL_SIZE câu (quá nhỏ, không đáng convert)
  - Pool của skill = 0 (toàn scraped, không có GEN_ để lấy)
  - Câu đã converted (type_converted=True trong generated files)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chạy:
  python utils/data/collection/convert_theory_gemini.py --dry-run
  python utils/data/collection/convert_theory_gemini.py
  python utils/data/collection/convert_theory_gemini.py --role DA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json, os, re, sys, time, argparse, random
from collections import defaultdict, Counter
import google.genai as genai

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.stdout.reconfigure(encoding="utf-8")

BANK_PATH     = os.path.join(ROOT, "data", "raw", "question_bank", "question_bank.json")
GENERATED_DIR = os.path.join(ROOT, "data", "raw", "question_bank", "generated")
SEED = 42
random.seed(SEED)

# ── Ngưỡng tối thiểu ──────────────────────────────────────────────────────────
MIN_PER_TYPE  = 4    # tối thiểu câu/type/skill để không bị mono (session=40 câu, 4 đủ break mono mà không giảm THEORY quá nhiều)
MIN_SKILL_SIZE = 8   # bỏ qua skill quá nhỏ

# Type nào convert từ source nào (ưu tiên)
SOURCE_PRIORITY = {
    "TRUE_FALSE": ["THEORY", "PRACTICE"],
    "CODING":     ["PRACTICE", "THEORY"],
    "MC_SINGLE":  ["THEORY", "PRACTICE"],
}

# ── Prompt ────────────────────────────────────────────────────────────────────
TYPE_GUIDELINES = {
    "MC_SINGLE":  "Rewrite as multiple choice with 4 options (A/B/C/D), one correct answer. Best for knowledge checks, comparisons, or 'which is correct' style.",
    "CODING":     "Rewrite as a hands-on task asking to implement, write, or debug code/SQL/queries. Best for algorithms, data processing, technical implementation.",
    "TRUE_FALSE": "Rewrite as a clear factual statement that is definitively TRUE or FALSE. Best for precise technical facts or common misconceptions.",
}

PROMPT_TEMPLATE = """You are a technical interview question designer.

ORIGINAL QUESTION:
Skill: {skill}
Difficulty: {difficulty}
Question: {question_text}
Answer: {answer}

TARGET TYPE: {target_type}
{type_guideline}

Decide: does this question convert NATURALLY to {target_type}?
- If YES: rewrite it as {target_type} format
- If NO (fundamentally unsuitable): respond with SKIP

OUTPUT FORMAT (strict JSON, no markdown):
{{
  "good_fit": true or false,
  "question_text": "rewritten question (empty string if SKIP)",
  "answers": {{
    "detailed": "comprehensive answer explanation",
    "evaluation_points": ["point 1", "point 2", "point 3", "point 4", "point 5"],
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_option": "A" | "B" | "C" | "D",
    "is_true": true or false,
    "code_template": "starter code if CODING, else empty string"
  }}
}}

RULES:
- good_fit: true only if conversion feels natural, false if forced
- If good_fit false: set question_text to empty string
- options + correct_option: required for MC_SINGLE, empty for others
- is_true: required for TRUE_FALSE, omit for others
- code_template: required for CODING, empty string for others
- Keep same difficulty: {difficulty}
- evaluation_points: 5 points (only if good_fit true)
- Output ONLY valid JSON, no other text"""


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_skill(q: dict) -> str:
    sg = q.get("skill_groups") or q.get("skill_tags") or ["unknown"]
    return sg[0]


def get_gemini_client():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        env_path = os.path.join(ROOT, ".env")
        if os.path.exists(env_path):
            for line in open(env_path, encoding="utf-8"):
                if "GEMINI_API_KEY" in line and "=" in line:
                    key = line.strip().split("=", 1)[1].strip().strip('"')
    if not key:
        raise ValueError("Chua set GEMINI_API_KEY trong .env")
    return genai.Client(api_key=key)


def parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```$',          '', raw, flags=re.MULTILINE)
    return json.loads(raw)


def call_gemini(client, prompt: str, max_retries: int = 5) -> str:
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            return resp.text
        except Exception as e:
            err = str(e)
            if any(x in err for x in ["429", "503", "quota", "rate", "unavailable"]):
                wait = 30 * (attempt + 1) + random.randint(0, 10)
                print(f"\n    Retry {attempt+1}/{max_retries}, waiting {wait}s...", end=" ", flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Max retries exceeded")


def normalize_answers(answers: dict, target_type: str) -> dict:
    """Đổi tên field cho đúng schema mà app đọc."""
    if target_type == "MC_SINGLE":
        if "correct_option" in answers and "correct_option_id" not in answers:
            answers["correct_option_id"] = answers.pop("correct_option")
        if "explanation" not in answers:
            answers["explanation"] = answers.get("detailed", "")
    elif target_type == "TRUE_FALSE":
        if "is_true" in answers and "correct_answer" not in answers:
            answers["correct_answer"] = answers.pop("is_true")
        if "explanation" not in answers:
            answers["explanation"] = answers.get("detailed", "")
    return answers


def stratified_sample(pool: list, n: int) -> list:
    """Sample n câu, giữ tỷ lệ EASY/MEDIUM/HARD của pool gốc."""
    by_diff = {"EASY": [], "MEDIUM": [], "HARD": []}
    for q in pool:
        d = q.get("difficulty_label", "MEDIUM")
        by_diff[d if d in by_diff else "MEDIUM"].append(q)
    total = len(pool)
    if total == 0:
        return []
    result = []
    for qs in by_diff.values():
        quota = round(n * len(qs) / total)
        random.shuffle(qs)
        result.extend(qs[:quota])
    used = {id(q) for q in result}
    leftover = [q for q in pool if id(q) not in used]
    random.shuffle(leftover)
    result.extend(leftover[:max(0, n - len(result))])
    random.shuffle(result)
    return result[:n]


def load_file_data(generated_dir: str):
    """Load tất cả generated files, trả về (file_map, file_data).
    file_map: question_id → fpath
    file_data: fpath → {question_id → question_dict}
    """
    file_map, file_data = {}, {}
    for fname in os.listdir(generated_dir):
        if not fname.startswith("generated_") or not fname.endswith(".json"):
            continue
        fpath = os.path.join(generated_dir, fname)
        qs = json.load(open(fpath, encoding="utf-8"))
        file_data[fpath] = {q["question_id"]: q for q in qs}
        for q in qs:
            file_map[q["question_id"]] = fpath
    return file_map, file_data


def save_all(file_data: dict):
    for fpath, qs_map in file_data.items():
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(list(qs_map.values()), f, ensure_ascii=False, indent=2)


def get_converted_ids(generated_dir: str) -> set:
    done = set()
    for fname in sorted(os.listdir(generated_dir)):
        if not fname.startswith("generated_") or not fname.endswith(".json"):
            continue
        qs = json.load(open(os.path.join(generated_dir, fname), encoding="utf-8"))
        for q in qs:
            if q.get("type_converted"):
                done.add(q.get("question_id", ""))
    return done


# ── Build data structures ─────────────────────────────────────────────────────
def build_skill_index(bank: list, file_data: dict, converted_ids: set):
    """
    Trả về:
      skill_current_types : skill → Counter(type → count)   — số câu hiện có mỗi type
      skill_pool          : skill → {source_type → [question]} — GEN_ chưa convert, có thể dùng làm nguồn
      skill_role          : skill → role
    """
    # Merge bank với file_data để có type mới nhất
    all_qs = []
    gen_data = {}
    for qs_map in file_data.values():
        for q in qs_map.values():
            gen_data[q["question_id"]] = q
    for q in bank:
        all_qs.append(gen_data.get(q["question_id"], q))

    skill_current = defaultdict(Counter)
    skill_pool    = defaultdict(lambda: defaultdict(list))
    skill_role    = {}

    for q in all_qs:
        skill = get_skill(q)
        role  = q.get("roles", {}).get("primary", "?")
        qtype = q.get("question_type", "?")
        qid   = q.get("question_id", "")

        skill_current[skill][qtype] += 1
        skill_role[skill] = role

        # Pool: chỉ GEN_, chưa convert, type là THEORY hoặc PRACTICE
        if (qid.startswith("GEN_")
                and qtype in ("THEORY", "PRACTICE")
                and not q.get("type_converted")
                and qid not in converted_ids):
            skill_pool[skill][qtype].append(q)

    return skill_current, skill_pool, skill_role


def compute_skill_plan(skill_current, skill_pool, skill_role, only_role=None):
    """
    Tính plan convert cho từng skill:
    plan = list of (skill, role, target_type, source_type, pool_questions, need)
    """
    plan = []
    for skill, current_types in skill_current.items():
        role = skill_role.get(skill, "?")
        if only_role and role != only_role:
            continue

        total = sum(current_types.values())
        if total < MIN_SKILL_SIZE:
            continue  # skill quá nhỏ

        for target_type in ["TRUE_FALSE", "CODING", "MC_SINGLE"]:
            current = current_types.get(target_type, 0)
            need = max(0, MIN_PER_TYPE - current)
            if need == 0:
                continue

            # Tìm source pool phù hợp (theo ưu tiên)
            chosen_pool = []
            chosen_src  = None
            for src_type in SOURCE_PRIORITY[target_type]:
                src_pool = skill_pool[skill].get(src_type, [])
                if src_pool:
                    chosen_pool = src_pool
                    chosen_src  = src_type
                    break

            if not chosen_pool:
                continue  # không có GEN_ pool cho skill này

            plan.append({
                "skill":       skill,
                "role":        role,
                "target_type": target_type,
                "source_type": chosen_src,
                "pool":        chosen_pool,
                "need":        need,
            })

    return plan


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Xem plan, không gọi Gemini")
    parser.add_argument("--role",    type=str, default=None, help="Chỉ chạy 1 role (DA/DS/DE)")
    args = parser.parse_args()

    bank = json.load(open(BANK_PATH, encoding="utf-8"))
    converted_ids = get_converted_ids(GENERATED_DIR)
    if converted_ids:
        print(f"Restart detected: {len(converted_ids)} questions already converted, skipping.")

    file_map, file_data = load_file_data(GENERATED_DIR)

    skill_current, skill_pool, skill_role = build_skill_index(bank, file_data, converted_ids)
    plan = compute_skill_plan(skill_current, skill_pool, skill_role, only_role=args.role)

    # ── Dry run ───────────────────────────────────────────────────────────────
    if args.dry_run:
        print(f"\n=== Convert Plan (min {MIN_PER_TYPE} per type per skill) ===\n")
        total_calls = 0
        cur_role = None
        for p in sorted(plan, key=lambda x: (x["role"], x["skill"], x["target_type"])):
            if p["role"] != cur_role:
                cur_role = p["role"]
                print(f"\nROLE {cur_role}:")
            avail = len(p["pool"])
            can   = min(p["need"], avail)
            warn  = f" ⚠ pool chỉ có {avail}" if avail < p["need"] else ""
            print(f"  {p['skill']:35s} {p['target_type']:12s} need={p['need']} pool={avail} src={p['source_type']}{warn}")
            total_calls += can
        print(f"\nTong Gemini calls: {total_calls} (~${total_calls*0.001:.2f})")
        return

    # ── Full run ──────────────────────────────────────────────────────────────
    client = get_gemini_client()
    total_ok = total_skip = total_err = 0

    # Group plan theo skill để save sau mỗi skill
    from itertools import groupby
    plan_by_skill = defaultdict(list)
    for p in plan:
        plan_by_skill[p["skill"]].append(p)

    for skill, skill_plan in plan_by_skill.items():
        role = skill_plan[0]["role"]
        print(f"\n{'='*60}")
        print(f"SKILL: {skill} | role={role}")

        # Track used_ids trong skill này (tránh dùng 1 câu cho 2 type)
        used_in_skill = set()

        for p in skill_plan:
            target_type = p["target_type"]
            need        = p["need"]
            src_pool    = [q for q in p["pool"] if q.get("question_id") not in used_in_skill]

            # 3x buffer, stratified by difficulty
            buffer = stratified_sample(src_pool, need * 3)
            filled = 0

            print(f"\n  -- {target_type} (need={need}, buffer={len(buffer)}, src={p['source_type']}) --")

            for q in buffer:
                if filled >= need:
                    break

                qid   = q.get("question_id", "?")
                fpath = file_map.get(qid)
                if not fpath or qid not in file_data.get(fpath, {}):
                    used_in_skill.add(qid)
                    continue

                print(f"    [{filled}/{need}] {qid}", end=" ", flush=True)

                prompt = PROMPT_TEMPLATE.format(
                    skill=skill,
                    difficulty=q.get("difficulty_label", q.get("difficulty", "MEDIUM")),
                    question_text=q.get("question_text", ""),
                    answer=q.get("answers", {}).get("detailed", "")[:800],
                    target_type=target_type,
                    type_guideline=TYPE_GUIDELINES[target_type],
                )

                try:
                    raw    = call_gemini(client, prompt)
                    result = parse_json(raw)

                    if not result.get("good_fit") or not result.get("question_text", "").strip():
                        total_skip += 1
                        used_in_skill.add(qid)
                        print("→ SKIP")
                        time.sleep(1.0)
                        continue

                    entry = file_data[fpath][qid]
                    entry["question_type"]  = target_type
                    entry["question_text"]  = result["question_text"]
                    entry["answers"]        = normalize_answers(
                        result.get("answers", q.get("answers", {})), target_type
                    )
                    entry["type_converted"] = True
                    entry["original_type"]  = p["source_type"]

                    used_in_skill.add(qid)
                    filled += 1
                    total_ok += 1
                    print(f"→ {target_type} OK")

                except Exception as e:
                    total_err += 1
                    used_in_skill.add(qid)
                    print(f"→ ERROR: {e}")
                    time.sleep(5)

                time.sleep(1.0 + random.uniform(0, 0.5))

            print(f"  {target_type} done: {filled}/{need}")

        # Save sau mỗi skill (crash-safe)
        save_all(file_data)
        print(f"  Saved skill {skill} to disk.")

    print(f"\n{'='*60}")
    print(f"DONE — OK={total_ok} SKIP={total_skip} ERR={total_err}")
    print(f"\nBuoc tiep theo:")
    print(f"  python utils/data/processing/merge_to_question_bank.py")


if __name__ == "__main__":
    main()
