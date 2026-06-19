"""
simulate_interaction.py — Sinh interaction log 20,000 rows dùng IRT + learning curve.

Đây là training data chính cho BKT / DKT / SAKT model.

Input:
  data/raw/simulation/virtual_users.json
  data/raw/question_bank_v1.json (đọc từng source để tránh truncate)

Output:
  data/raw/simulation/interaction_log.csv

Schema:
  user_id, question_id, role, competency, skill_group,
  difficulty_label, difficulty, quality_score,
  skill_before, skill_after, timestamp, session_order

quality_score:
  0 = Fail  (user không trả lời được)
  1 = Pass HR  (trả lời được nhưng chưa sâu)
  2 = Pass Tech (trả lời tốt, đúng kỹ thuật)

Chạy: python utils/data/simulation/simulate_interaction.py
"""

import json, os, re, csv, random
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from simulation_config import (
    QUESTIONS_PER_USER_MIN, QUESTIONS_PER_USER_MAX,
    NOISE, LEARNING_RATE, FORGETTING_RATE,
    DIFFICULTY_MAP, SKILL_GROUP_TO_COMPETENCY, ROLE_DEFAULT_COMPETENCY,
    normalize_competency, SEED
)

random.seed(SEED)
np.random.seed(SEED)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ── Load question bank từ sources (tránh truncate) ──────────────────────
def load_json_safe(path: str) -> list:
    """Đọc JSON file, dùng regex fallback nếu file bị truncate."""
    with open(path, 'rb') as f:
        raw_bytes = f.read()
    try:
        data = json.loads(raw_bytes.rstrip(b'\x00').decode('utf-8'))
        return data if isinstance(data, list) else data.get("questions", [])
    except json.JSONDecodeError:
        # Fallback: extract bằng regex
        raw = raw_bytes.decode('utf-8', errors='replace')
        return _extract_qs_regex(raw)


def _extract_qs_regex(raw: str) -> list:
    """Extract question objects từ raw string dùng regex."""
    ids    = re.findall(r'"question_id":\s*"([^"]+)"', raw)
    texts  = re.findall(r'"question_text":\s*"([^"]*)"', raw)
    roles  = re.findall(r'"primary":\s*"(\w+)"', raw)
    diffs  = re.findall(r'"difficulty_label":\s*"(\w+)"', raw)
    qtypes = re.findall(r'"question_type":\s*"(\w+)"', raw)
    groups = re.findall(r'"skill_groups":\s*\[\s*"(\w+)"', raw)
    n = min(len(ids), len(roles), len(diffs), len(qtypes), len(groups))
    qs = []
    for i in range(n):
        diff = diffs[i] if diffs[i] != "EXPERT" else "HARD"
        qs.append({
            "question_id":     ids[i] if i < len(ids) else f"R_{i}",
            "question_text":   texts[i] if i < len(texts) else "",
            "roles":           {"primary": roles[i], "secondary": []},
            "difficulty_label": diff,
            "question_type":   qtypes[i],
            "skill_groups":    [groups[i]],
            "answers":         {"detailed": "..."},
        })
    return qs


def load_question_bank():
    """Đọc từ question_bank.json (đã merge + QC đầy đủ)."""
    bank_path = os.path.join(ROOT_DIR, "data/raw/question_bank/question_bank.json")
    all_qs = load_json_safe(bank_path)

    # Normalize + dedup
    seen, unique = set(), []
    for q in all_qs:
        if q.get("difficulty_label") == "EXPERT":
            q["difficulty_label"] = "HARD"
        key = re.sub(r'\s+', ' ', q.get("question_text", "").lower().strip())
        if key and key not in seen:
            seen.add(key)
            unique.append(q)

    print(f"Question bank loaded: {len(unique)} unique questions")
    return unique


def get_competency(q: dict, role: str) -> str:
    # Ưu tiên skill_groups (scraped), fallback sang skill_tags (mock)
    grp = q.get("skill_groups", ["?"])[0]
    if grp == "?":
        grp = q.get("skill_tags", ["?"])[0]
    raw = SKILL_GROUP_TO_COMPETENCY.get(grp, ROLE_DEFAULT_COMPETENCY.get(role, "general"))
    return normalize_competency(raw)  # luôn trả về lowercase canonical


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def sample_quality(p_correct: float, noise: float = NOISE) -> int:
    """
    Power-based graded response model:
      P(Q=2) = p_correct^alpha         — cần skill cao mới đạt full marks
      P(Q=0) = (1-p_correct)^alpha     — cần skill thấp rõ mới fail hoàn toàn
      P(Q=1) = 1 - P(Q=2) - P(Q=0)    — partial credit, cao nhất ở vùng borderline

    alpha=1.35 → Q1 đạt ~20-22% ở mức skill trung bình
    """
    alpha = 2.0   # alpha cao → bucket quality=1 rộng hơn ở vùng p_correct trung bình
    p_q2 = p_correct ** alpha
    p_q0 = (1 - p_correct) ** alpha
    p_q1 = max(0.0, 1.0 - p_q2 - p_q0)

    r = random.random()
    if r < p_q2:
        return 2
    elif r < p_q2 + p_q1:
        return 1
    else:
        return 0


def update_skill(skill: float, quality: int) -> float:
    """Learning curve: skill tăng khi đúng, giảm khi sai."""
    if quality >= 1:
        skill += LEARNING_RATE * (1.0 - skill)
    else:
        skill -= FORGETTING_RATE * skill
    return float(np.clip(skill, 0.05, 0.99))


def weighted_sample_questions(pool: list, n: int, session_idx: int) -> list:
    """
    Sample n câu từ pool, không lặp lại.
    Đầu session ưu tiên EASY-MEDIUM, cuối session mix HARD.
    """
    if len(pool) <= n:
        return pool[:]

    # Tính weight theo difficulty và vị trí session
    progress = session_idx / max(n - 1, 1)  # 0 → 1 theo tiến trình session
    weights = []
    for q in pool:
        diff = q.get("difficulty_label", "MEDIUM")
        d = DIFFICULTY_MAP.get(diff, 0.55)
        # Đầu session: ưu tiên dễ (weight cao khi d thấp)
        # Cuối session: cân bằng hơn
        w = 1.0 - d * progress * 0.5
        weights.append(max(w, 0.05))

    total_w = sum(weights)
    probs = [w / total_w for w in weights]
    indices = np.random.choice(len(pool), size=n, replace=False, p=probs)
    return [pool[i] for i in indices]


def stratified_sample_questions(pool: list, n: int, role: str) -> list:
    """
    Sample n câu với stratification theo competency:
    Đảm bảo mỗi competency của role đều xuất hiện tối thiểu,
    tránh 1 competency chiếm quá nhiều (vd DA sql=78%).
    """
    from simulation_config import ROLE_COMPETENCIES, ROLE_DEFAULT_COMPETENCY

    comps = ROLE_COMPETENCIES.get(role, [])
    n_comps = len(comps)
    if n_comps == 0 or len(pool) <= n:
        return pool[:]

    # Nhóm questions theo competency
    by_comp = defaultdict(list)
    for q in pool:
        comp = get_competency(q, role)
        by_comp[comp].append(q)

    # Quota tối thiểu mỗi competency: floor(n / n_comps) nhưng ≥1
    base_quota = max(1, n // n_comps)
    selected = []

    # Pass 1: lấy base_quota từ mỗi competency có sẵn
    remaining_per_comp = {}
    for comp in comps:
        qs = by_comp.get(comp, [])
        take = min(base_quota, len(qs))
        chosen = list(np.random.choice(qs, size=take, replace=False)) if take > 0 else []
        selected.extend(chosen)
        remaining_per_comp[comp] = [q for q in qs if q not in chosen]

    # Pass 2: fill còn lại ngẫu nhiên từ pool chưa dùng
    used_ids = {id(q) for q in selected}
    leftover = [q for q in pool if id(q) not in used_ids]
    still_need = n - len(selected)
    if still_need > 0 and leftover:
        extra = list(np.random.choice(leftover,
                                      size=min(still_need, len(leftover)),
                                      replace=False))
        selected.extend(extra)

    # Shuffle ngẫu nhiên — không sort cứng EASY→HARD để tránh skill regression
    random.shuffle(selected)
    return selected[:n]


def simulate_user_session(user: dict, questions_by_role: dict) -> list:
    """Simulate một session 40 câu cho 1 user. Trả về list of log rows."""
    role        = user["role"]
    skill_vec   = {k: v for k, v in user["skill_vector"].items()}  # copy
    pool        = questions_by_role.get(role, [])

    if len(pool) < 5:
        return []  # không đủ câu

    # Randomize số câu hỏi per user (tránh uniform 40)
    n_questions = random.randint(QUESTIONS_PER_USER_MIN, QUESTIONS_PER_USER_MAX)
    # Stratified sample theo competency
    selected = stratified_sample_questions(pool, n_questions, role)

    # Random start time: trong khoảng 2024-01-01 → 2025-12-31
    start_dt = datetime(2024, 1, 1) + timedelta(
        days=random.randint(0, 730),
        hours=random.randint(8, 22),
        minutes=random.randint(0, 59),
    )

    rows = []
    current_dt = start_dt

    for order, q in enumerate(selected, start=1):
        comp      = get_competency(q, role)
        diff_label = q.get("difficulty_label", "MEDIUM")
        diff_num   = DIFFICULTY_MAP.get(diff_label, 0.55)
        skill_now  = skill_vec.get(comp, 0.5)

        # IRT: P = sigmoid(skill - difficulty) — scale về [-3, 3]
        p_correct  = sigmoid((skill_now - diff_num) * 6)
        quality    = sample_quality(p_correct)
        skill_after = update_skill(skill_now, quality)

        # Cập nhật skill vector
        skill_vec[comp] = skill_after

        # Timestamp: mỗi câu mất 3–8 phút
        current_dt += timedelta(minutes=random.randint(3, 8))

        rows.append({
            "user_id":        user["user_id"],
            "question_id":    q.get("question_id", "?"),
            "role":           role,
            "competency":     comp,
            "skill_group":    q.get("skill_groups", ["?"])[0],
            "question_type":  q.get("question_type", "?"),
            "difficulty_label": diff_label,
            "difficulty":     round(diff_num, 2),
            "quality_score":  quality,
            "skill_before":   round(skill_now, 4),
            "skill_after":    round(skill_after, 4),
            "timestamp":      current_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "session_order":  order,
        })

    return rows


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT_DIR, "data/raw/simulation"), exist_ok=True)

    # Load data
    print("Loading question bank...")
    all_qs = load_question_bank()

    print("Loading virtual users...")
    with open(os.path.join(ROOT_DIR, "data/raw/simulation/virtual_users.json"), encoding="utf-8") as f:
        users = json.load(f)
    print(f"Users loaded: {len(users)}")

    # Group questions by role
    questions_by_role = defaultdict(list)
    for q in all_qs:
        role = q.get("roles", {}).get("primary", "?")
        questions_by_role[role].append(q)

    print(f"Questions by role: " +
          ", ".join(f"{r}={len(qs)}" for r, qs in questions_by_role.items()))

    # Simulate
    print("\nSimulating interactions...")
    all_rows = []
    for i, user in enumerate(users):
        rows = simulate_user_session(user, questions_by_role)
        all_rows.extend(rows)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(users)} users done — {len(all_rows)} rows so far")

    print(f"\nTotal interactions: {len(all_rows)}")

    from collections import Counter as _Counter
    qc = _Counter(r["quality_score"] for r in all_rows)
    total = len(all_rows)
    print(f"Quality: 0={qc[0]} ({qc[0]/total*100:.1f}%)  1={qc[1]} ({qc[1]/total*100:.1f}%)  2={qc[2]} ({qc[2]/total*100:.1f}%)")

    da_rows = [r for r in all_rows if r["role"]=="DA"]
    da_comps = _Counter(r["competency"] for r in da_rows)
    print(f"DA competency spread: {dict(sorted(da_comps.items(), key=lambda x:-x[1]))}")

    import csv as _csv
    out = os.path.join(ROOT_DIR, "data/raw/simulation/interaction_log.csv")
    fieldnames = ["user_id","question_id","role","competency","skill_group",
        "question_type","difficulty_label","difficulty","quality_score",
        "skill_before","skill_after","timestamp","session_order"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nSaved -> {out}  ({len(all_rows):,} rows)")

    # Learning curve đúng: skill_after tăng theo session_order
    import numpy as _np2
    skill_early = [float(r["skill_after"]) for r in all_rows if int(r["session_order"]) <= 10]
    skill_late  = [float(r["skill_after"]) for r in all_rows if int(r["session_order"]) >= 31]
    print(f"Skill learning curve: order1-10 avg={_np2.mean(skill_early):.4f}  order31-40 avg={_np2.mean(skill_late):.4f}  delta={_np2.mean(skill_late)-_np2.mean(skill_early):+.4f}")
    print("  " + ("OK skill tang" if _np2.mean(skill_late) > _np2.mean(skill_early) else "WARN skill khong tang"))
