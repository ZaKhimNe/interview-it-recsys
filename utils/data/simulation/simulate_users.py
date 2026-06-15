"""
simulate_users.py — Tao 500 virtual users cho KT model training.

Output: data/raw/simulation/virtual_users.json

Schema mỗi user:
{
  "user_id": "u_001",
  "role": "DA",
  "user_type": "intermediate",   # beginner / intermediate / advanced
  "experience_years": 2.1,
  "skill_vector": {
    "sql": 0.62,
    "statistics": 0.45,
    ...
  }
}

Chạy: python utils/data/simulation/simulate_users.py
"""

import json, os, random
import numpy as np
from simulation_config import (
    N_USERS, ROLE_DIST, ROLE_COMPETENCIES, SEED
)

random.seed(SEED)
np.random.seed(SEED)

# ── Correlation giữa các competency cùng role ────────────────────────────
# Giá trị 0–1: càng cao càng tương quan dương mạnh
# Dựa trên thực tế: người giỏi 1 skill thường kéo theo các skill liên quan
COMPETENCY_CORRELATION = {
    # DA: SQL và analytics liên quan chặt; BI ít hơn
    "DA": {
        ("SQL_DATABASE",              "ANALYTICS_BUSINESS"):        0.55,
        ("SQL_DATABASE",              "STATISTICS_EXPERIMENTATION"): 0.45,
        ("ANALYTICS_BUSINESS",        "STATISTICS_EXPERIMENTATION"): 0.50,
        ("SQL_DATABASE",              "PYTHON_ANALYTICS"):           0.40,
        ("ANALYTICS_BUSINESS",        "PYTHON_ANALYTICS"):           0.35,
        ("BI_VISUALIZATION",          "ANALYTICS_BUSINESS"):         0.45,
        ("BI_VISUALIZATION",          "SQL_DATABASE"):               0.30,
    },
    # DS: algorithm và evaluation gần như đi đôi
    "DS": {
        ("ALGORITHM_THEORY",  "EVALUATION_METRICS"):  0.70,
        ("ALGORITHM_THEORY",  "DATA_PREPROCESSING"):  0.55,
        ("ALGORITHM_THEORY",  "DEEP_LEARNING"):        0.60,
        ("DEEP_LEARNING",     "NLP"):                  0.55,
        ("ALGORITHM_THEORY",  "MLOPS"):                0.45,
        ("PYTHON_ANALYTICS",  "DATA_PREPROCESSING"):   0.60,
        ("PYTHON_ANALYTICS",  "ALGORITHM_THEORY"):     0.50,
    },
    # DE: pipeline và data_architecture cực kỳ liên quan
    "DE": {
        ("DATA_PIPELINE",            "DATA_ARCHITECTURE_MODELING"): 0.70,
        ("DATA_PIPELINE",            "DATABASE_INTERNALS"):          0.60,
        ("DATA_ARCHITECTURE_MODELING","DATABASE_INTERNALS"):         0.65,
        ("BIG_DATA_CLOUD_TOOLS",     "DATA_PIPELINE"):               0.55,
        ("BIG_DATA_CLOUD_TOOLS",     "DATA_ARCHITECTURE_MODELING"):  0.50,
        ("SYSTEM_ARCHITECTURE",      "DATA_ARCHITECTURE_MODELING"):  0.50,
    },
}

# Skill gap đặc trưng mỗi role: competency nào thường yếu hơn các cái còn lại
# (penalty trừ vào mean khi sample — người DA thường yếu statistics hơn sql)
WEAK_COMPETENCY_PENALTY = {
    "DA": {
        "STATISTICS_EXPERIMENTATION": -0.08,
        "PYTHON_ANALYTICS":           -0.05,
        "BI_VISUALIZATION":           -0.06,
    },
    "DS": {
        "DEEP_LEARNING": -0.07,
        "NLP":           -0.06,
        "MLOPS":         -0.05,
        "TIME_SERIES":   -0.04,
    },
    "DE": {
        "SYSTEM_ARCHITECTURE": -0.05,
    },
}


def sample_skill_vector_correlated(competencies: list, role: str, base_skill: float) -> dict:
    """
    Sample skill vector có tương quan giữa các competency.

    Cách làm:
    1. Lấy base_skill (từ tier) làm điểm xuất phát cho tất cả
    2. Sample noise độc lập cho từng comp từ Beta
    3. Thêm correlation: nếu 2 comp có corr cao, noise của chúng kéo nhau
    4. Áp dụng weak penalty cho các comp đặc trưng yếu của role
    """
    n = len(competencies)
    corr_map = COMPETENCY_CORRELATION.get(role, {})
    penalty_map = WEAK_COMPETENCY_PENALTY.get(role, {})

    # Step 1: sample noise độc lập ~ N(0, 0.15) cho mỗi comp
    raw_noise = {c: np.random.normal(0, 0.15) for c in competencies}

    # Step 2: lan truyền correlation — blend noise của các cặp có corr cao
    blended_noise = {c: raw_noise[c] for c in competencies}
    for (c1, c2), corr in corr_map.items():
        if c1 in blended_noise and c2 in blended_noise:
            shared = (raw_noise[c1] + raw_noise[c2]) / 2
            blended_noise[c1] = blended_noise[c1] * (1 - corr) + shared * corr
            blended_noise[c2] = blended_noise[c2] * (1 - corr) + shared * corr

    # Step 3: tính skill = base ± noise ± penalty, clip về [0.05, 0.99]
    skill_vec = {}
    for c in competencies:
        penalty = penalty_map.get(c, 0.0)
        val = base_skill + blended_noise[c] + penalty
        skill_vec[c] = round(float(np.clip(val, 0.05, 0.99)), 3)

    return skill_vec


def classify_user_type(skill_vector: dict) -> str:
    mean_skill = np.mean(list(skill_vector.values()))
    if mean_skill < 0.40:
        return "beginner"
    elif mean_skill < 0.70:
        return "intermediate"
    else:
        return "advanced"


def sample_experience(user_type: str) -> float:
    """
    Kinh nghiệm năm — dùng log-normal thay vì uniform.
    Log-normal phản ánh thực tế: nhiều người 1-2 năm, ít người > 6 năm.
    """
    params = {
        # (mean_log, sigma_log) → exp(mean_log) = median
        "beginner":     (0.1,  0.35),   # median ~1.1 năm
        "intermediate": (0.85, 0.35),   # median ~2.3 năm
        "advanced":     (1.65, 0.30),   # median ~5.2 năm
    }
    mu, sigma = params[user_type]
    years = np.random.lognormal(mu, sigma)
    # Clamp theo thực tế
    clamp = {
        "beginner":     (0.3, 2.0),
        "intermediate": (1.0, 5.0),
        "advanced":     (3.5, 10.0),
    }
    lo, hi = clamp[user_type]
    return round(float(np.clip(years, lo, hi)), 1)


def generate_users() -> list:
    """
    Phân bổ thực tế hơn: ~35% beginner, ~50% intermediate, ~15% advanced.
    (Platform học thực tế có nhiều beginner hơn so với 10% cũ)
    """
    users = []
    uid = 1

    for role, total in ROLE_DIST.items():
        comps = ROLE_COMPETENCIES[role]

        n_advanced  = max(1, round(total * 0.15))   # 15%
        n_beginner  = max(1, round(total * 0.35))   # 35% (tăng từ 10%)
        n_normal    = total - n_advanced - n_beginner  # 50%

        # base_skill tương ứng mỗi tier: mean của Beta phân bố tương đương
        tier_plan = [
            ("advanced", n_advanced, 0.72),   # ~Beta(5,2) mean
            ("beginner", n_beginner, 0.28),   # ~Beta(2,5) mean
            ("normal",   n_normal,   0.50),   # ~Beta(2,2) mean
        ]

        for tier, count, base_skill in tier_plan:
            for _ in range(count):
                skill_vec = sample_skill_vector_correlated(comps, role, base_skill)
                user_type = classify_user_type(skill_vec)
                exp_years = sample_experience(user_type)

                users.append({
                    "user_id":          f"u_{uid:04d}",
                    "role":             role,
                    "user_type":        user_type,
                    "experience_years": exp_years,
                    "skill_vector":     skill_vec,
                })
                uid += 1

    random.shuffle(users)
    return users


if __name__ == "__main__":
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    os.makedirs(os.path.join(ROOT_DIR, "data/raw/simulation"), exist_ok=True)

    users = generate_users()

    from collections import Counter
    roles      = Counter(u["role"] for u in users)
    user_types = Counter(u["user_type"] for u in users)

    print(f"Total users: {len(users)}")
    print(f"Roles:       {dict(roles)}")
    print(f"User types:  {dict(user_types)}")
    total = len(users)
    for ut in ["beginner", "intermediate", "advanced"]:
        n = user_types[ut]
        print(f"  {ut}: {n} ({n/total*100:.1f}%)")

    print()
    for role in ["DA", "DS", "DE"]:
        role_users = [u for u in users if u["role"] == role]
        print(f"\n-- {role} (n={len(role_users)}) --")
        comps = ROLE_COMPETENCIES[role]
        for comp in comps:
            vals = [u["skill_vector"].get(comp, 0) for u in role_users]
            arr = np.array(vals)
            print(f"  {comp:25s}  mean={arr.mean():.3f}  std={arr.std():.3f}  min={arr.min():.2f}  max={arr.max():.2f}")

    print("\n-- Sample users (1 moi type) --")
    shown = set()
    for u in users:
        if u["user_type"] not in shown:
            print(json.dumps(u, indent=2, ensure_ascii=False))
            shown.add(u["user_type"])
        if len(shown) == 3:
            break

    # Kiểm tra correlation thực tế giữa 2 competency mẫu
    print("\n-- Correlation check --")
    da_users = [u for u in users if u["role"] == "DA"]
    sql_vals = [u["skill_vector"].get("SQL_DATABASE", 0) for u in da_users]
    ana_vals = [u["skill_vector"].get("ANALYTICS_BUSINESS", 0) for u in da_users]
    r = np.corrcoef(sql_vals, ana_vals)[0, 1]
    print(f"  r(SQL_DATABASE, ANALYTICS_BUSINESS) = {r:.3f}  (target ~0.55)")

    ds_users = [u for u in users if u["role"] == "DS"]
    ml_vals  = [u["skill_vector"].get("ALGORITHM_THEORY", 0) for u in ds_users]
    ev_vals  = [u["skill_vector"].get("EVALUATION_METRICS", 0) for u in ds_users]
    r2 = np.corrcoef(ml_vals, ev_vals)[0, 1]
    print(f"  r(ALGORITHM_THEORY, EVALUATION_METRICS) = {r2:.3f}  (target ~0.70)")

    out = os.path.join(ROOT_DIR, "data/raw/simulation/virtual_users.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    print(f"\nSaved -> {out}  ({len(users)} users)")
