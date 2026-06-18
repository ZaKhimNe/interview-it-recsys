"""
Merge tất cả scraped data + mock data → question_bank_v1.json
Kiểm tra schema, loại duplicate, in báo cáo.

Chạy SAU KHI đã chạy đủ 3 script scrape:
  python utils/data/collection/scrape_alexey_ds_da.py
  python utils/data/collection/scrape_obenner_de.py
  python utils/data/collection/scrape_youssef_ds_da.py
  python utils/data/collection/merge_validate.py
"""
import json, os, re, math
from collections import Counter
from datetime import date

SOURCES = [
    "data/raw/question_bank/question_bank.json",   # 171 câu gốc
    "data/raw/question_bank/scraped_github.json",        # DS + DA từ alexeygrigorev
    "data/raw/question_bank/scraped_de.json",            # DE từ OBenner
    "data/raw/question_bank/scraped_youssef.json",       # DS + DA từ youssefHosni (bổ sung)
    "data/raw/question_bank/scraped_sql.json",           # DA SQL từ learning-zone (bổ sung)
    "data/raw/converted_tf_fb.json",       # TRUE_FALSE + FILL_BLANK (converted)
]

REQUIRED_FIELDS = [
    "question_id", "question_text", "roles",
    "difficulty_label", "difficulty_score",
    "question_type", "skill_groups", "skill_tags", "answers",
]

VALID_ROLES      = {"DA", "DE", "DS", "MLE", "BE", "FE"}
VALID_DIFF       = {"EASY", "MEDIUM", "HARD"}   # normalize EXPERT → HARD
VALID_TYPES      = {"THEORY", "PRACTICE", "CODING", "MC_SINGLE",
                    "TRUE_FALSE", "FILL_BLANK", "CODING_EXERCISE"}

# Giữ hết tất cả câu hỏi hợp lệ — càng nhiều data càng tốt
ROLE_CAPS = {
    "DA": 9999,
    "DS": 9999,
    "DE": 9999,
}

# ── Normalize answer schema ─────────────────────────────────────────────
def normalize_answer_schema(q: dict) -> dict:
    """
    Mock data dùng schema riêng theo question type thay vì answers.detailed.
    Convert về dạng chuẩn có answers.detailed để validator không bị fail.

    MC_SINGLE : options[] + correct_option_id + explanation → detailed
    TRUE_FALSE : correct_answer (bool) + explanation        → detailed
    FILL_BLANK : accepted_answers[] + explanation           → detailed
    """
    ans = q.get("answers", {})
    if ans.get("detailed", "").strip():
        return q   # đã có detailed → không cần convert

    q_type = q.get("question_type", "")
    detailed = ""

    if q_type == "MC_SINGLE":
        options   = q.get("options", [])
        correct   = ans.get("correct_option_id", "")
        expl      = ans.get("explanation", "")
        opts_text = "\n".join(f"{o['id']}) {o['text']}" for o in options)
        detailed  = f"Correct: {correct}\n{opts_text}\n\nExplanation: {expl}"

    elif q_type == "TRUE_FALSE":
        correct  = ans.get("correct_answer", None)
        expl     = ans.get("explanation", "")
        label    = "True" if correct is True else ("False" if correct is False else "")
        detailed = f"{label}.\n\nExplanation: {expl}" if label else expl

    elif q_type == "FILL_BLANK":
        accepted = ans.get("accepted_answers", [])
        expl     = ans.get("explanation", "")
        # accepted_answers có thể là [[a1, a2], [b1]] hoặc ["a", "b"]
        flat = []
        for a in accepted:
            flat.append(a[0] if isinstance(a, list) else a)
        answers_str = " / ".join(flat)
        detailed = f"Answer: {answers_str}\n\nExplanation: {expl}"

    if detailed.strip():
        q = dict(q)
        q["answers"] = dict(ans)
        q["answers"]["detailed"] = detailed
        if "evaluation_points" not in q["answers"]:
            q["answers"]["evaluation_points"] = []

    return q


# ── Normalize difficulty ────────────────────────────────────────────────
DIFF_SCORE_MAP = {"EASY": 2, "MEDIUM": 5, "HARD": 8}

def normalize_difficulty(q: dict) -> dict:
    """EXPERT → HARD để nhất quán với mock data."""
    if q.get("difficulty_label") == "EXPERT":
        q = dict(q)
        q["difficulty_label"] = "HARD"
        q["difficulty_score"] = 8
    return q


# ── Load ────────────────────────────────────────────────────────────────
def load_source(path: str) -> list:
    if not os.path.exists(path):
        print(f"  [SKIP] {path} not found")
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("questions", [])

# ── Validate 1 câu ──────────────────────────────────────────────────────
def validate(q: dict) -> list:
    """Trả về list lỗi. Rỗng = hợp lệ."""
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in q:
            errors.append(f"missing field: {field}")

    role = q.get("roles", {}).get("primary", "")
    if role not in VALID_ROLES:
        errors.append(f"invalid role: {role!r}")

    diff = q.get("difficulty_label", "")
    if diff not in VALID_DIFF:
        errors.append(f"invalid difficulty: {diff!r}")

    qtype = q.get("question_type", "")
    if qtype not in VALID_TYPES:
        errors.append(f"invalid type: {qtype!r}")

    if not q.get("question_text", "").strip():
        errors.append("empty question_text")

    if not q.get("answers", {}).get("detailed", "").strip():
        errors.append("empty answers.detailed")

    return errors

# ── Re-assign ID để tránh trùng ─────────────────────────────────────────
def reassign_ids(questions: list) -> list:
    counters = Counter()
    result = []
    for q in questions:
        role = q.get("roles", {}).get("primary", "XX")
        counters[role] += 1
        q = dict(q)
        q["question_id"] = f"{role}_{counters[role]:04d}"
        result.append(q)
    return result

# ── Dedup theo question_text (lowercase, stripped) ──────────────────────
def dedup(questions: list) -> tuple:
    seen = set()
    unique, dupes = [], 0
    for q in questions:
        key = re.sub(r'\s+', ' ', q.get("question_text", "").lower().strip())
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        unique.append(q)
    return unique, dupes

# ── Balanced role cap ────────────────────────────────────────────────────
MIN_PER_GROUP = 8   # tối thiểu mỗi skill_group sau khi cắt

def apply_role_caps_balanced(questions: list, role_caps: dict) -> list:
    """
    Áp dụng role cap với cắt proportional theo skill_group:
      - Nhóm câu theo skill_group trong mỗi role
      - Tính quota = floor(group_size * ratio), tối thiểu MIN_PER_GROUP
      - Nếu tổng quota > cap, giảm dần từ group nhiều nhất
      - Giữ nguyên thứ tự gốc (mock trước, scrape sau)
    """
    # Tách theo role
    by_role: dict[str, list] = {}
    for q in questions:
        role = q.get("roles", {}).get("primary", "XX")
        by_role.setdefault(role, []).append(q)

    kept_ids: set[int] = set()

    for role, qs in by_role.items():
        cap = role_caps.get(role, 9999)
        if len(qs) <= cap:
            kept_ids.update(id(q) for q in qs)
            continue

        # Nhóm theo skill_group
        by_group: dict[str, list] = {}
        for q in qs:
            grp = q.get("skill_groups", ["UNKNOWN"])[0]
            by_group.setdefault(grp, []).append(q)

        ratio = cap / len(qs)

        # Pass 1: tính quota ban đầu
        quotas: dict[str, int] = {}
        for grp, grp_qs in by_group.items():
            quota = max(MIN_PER_GROUP, math.floor(len(grp_qs) * ratio))
            quotas[grp] = min(quota, len(grp_qs))

        total = sum(quotas.values())

        # Pass 2: nếu total > cap, cắt dần từ group có quota lớn nhất
        while total > cap:
            biggest = max(
                (grp for grp in quotas if quotas[grp] > MIN_PER_GROUP),
                key=lambda g: quotas[g],
                default=None,
            )
            if biggest is None:
                break
            quotas[biggest] -= 1
            total -= 1

        # Collect
        for grp, quota in quotas.items():
            kept_ids.update(id(q) for q in by_group[grp][:quota])

        # Báo cáo
        print(f"  Role {role} cap={cap}: "
              + ", ".join(f"{g}={quotas[g]}" for g in sorted(quotas)))

    # Trả về danh sách giữ nguyên thứ tự gốc
    return [q for q in questions if id(q) in kept_ids]


# ── Main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    all_questions = []
    for path in SOURCES:
        print(f"Loading {path} ...")
        qs = load_source(path)
        print(f"  -> {len(qs)} questions loaded")
        all_questions.extend(qs)

    # Normalize EXPERT → HARD
    all_questions = [normalize_difficulty(q) for q in all_questions]
    # Normalize answer schema (mock MC_SINGLE/TRUE_FALSE/FILL_BLANK → detailed)
    all_questions = [normalize_answer_schema(q) for q in all_questions]

    print(f"\nTotal before dedup: {len(all_questions)}")

    # Dedup
    all_questions, n_dupes = dedup(all_questions)
    print(f"Duplicates removed: {n_dupes}")
    print(f"Total after dedup:  {len(all_questions)}")

    # Validate
    invalid = []
    valid = []
    for q in all_questions:
        errs = validate(q)
        if errs:
            invalid.append((q.get("question_id", "?"), errs))
        else:
            valid.append(q)

    print(f"\nValid:   {len(valid)}")
    print(f"Invalid: {len(invalid)}")
    if invalid:
        print("\nSample invalid (first 5):")
        for qid, errs in invalid[:5]:
            print(f"  [{qid}] {errs}")

    # Áp dụng role cap với phân phối cân bằng theo skill_group
    valid = apply_role_caps_balanced(valid, ROLE_CAPS)
    print(f"\nAfter role cap: {len(valid)} (DE capped at {ROLE_CAPS['DE']})")

    # Reassign IDs
    valid = reassign_ids(valid)

    # Stats
    print("\n── Final Stats ────────────────────────")
    print("Total:", len(valid))
    print("Roles:", dict(Counter(q["roles"]["primary"] for q in valid)))
    print("Types:", dict(Counter(q["question_type"] for q in valid)))
    print("Diff: ", dict(Counter(q["difficulty_label"] for q in valid)))
    print("Groups (top 10):",
          dict(Counter(q["skill_groups"][0] for q in valid).most_common(10)))

    # Save
    os.makedirs("data/raw", exist_ok=True)
    out = "data/raw/question_bank_v1.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "version":    "v1.0",
            "created_at": str(date.today()),
            "total":      len(valid),
            "questions":  valid,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nSaved -> {out}")
    print("Done! Kiểm tra data/raw/question_bank_v1.json trước khi dùng.")
