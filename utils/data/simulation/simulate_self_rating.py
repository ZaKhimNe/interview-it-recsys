"""
simulate_self_rating.py — Sinh self-rating log (user tự đánh giá skill).

Dùng để so sánh với knowledge_state từ KT model → đo "self-awareness accuracy".

Input:  data/raw/simulation/virtual_users.json
Output: data/raw/simulation/self_rating_log.csv

Schema:
  user_id, role, competency, true_skill, self_rating_raw,
  self_rating_likert, confidence_bias, timestamp

Chạy: python utils/data/simulation/simulate_self_rating.py
"""

import json, os, csv, random
import numpy as np
from datetime import datetime, timedelta
from simulation_config import SEED

random.seed(SEED)
np.random.seed(SEED)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def sample_self_rating(true_skill: float, user_type: str) -> dict:
    """
    User tự đánh giá không hoàn toàn chính xác.
    - beginner:     xu hướng over-confident (+0.05 bias)
    - intermediate: khá chính xác (0 bias)
    - advanced:     xu hướng under-confident (–0.05 bias)
    Noise: N(0, 0.12) cho tất cả
    """
    bias_map = {
        "beginner":     +0.08,
        "intermediate":  0.00,
        "advanced":     -0.05,
    }
    bias  = bias_map.get(user_type, 0.0)
    noise = np.random.normal(0, 0.12)
    raw   = float(np.clip(true_skill + bias + noise, 0.0, 1.0))

    # Map sang Likert 1–5
    # 0.0–0.20 → 1, 0.20–0.40 → 2, 0.40–0.60 → 3, 0.60–0.80 → 4, 0.80–1.0 → 5
    likert = min(5, int(raw * 5) + 1)

    return {
        "self_rating_raw":    round(raw, 3),
        "self_rating_likert": likert,
        "confidence_bias":    round(raw - true_skill, 3),
    }


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT_DIR, "data/raw/simulation"), exist_ok=True)

    print("Loading virtual users...")
    with open(os.path.join(ROOT_DIR, "data/raw/simulation/virtual_users.json"), encoding="utf-8") as f:
        users = json.load(f)
    print(f"Users loaded: {len(users)}")

    rows = []
    # Self-rating xảy ra trước khi user bắt đầu luyện tập
    # Timestamp: 1–3 ngày trước start của interaction session
    base_date = datetime(2024, 1, 1)

    for user in users:
        ts = base_date + timedelta(
            days=random.randint(0, 728),
            hours=random.randint(18, 23),  # buổi tối tự đánh giá
            minutes=random.randint(0, 59),
        )

        for comp, true_skill in user["skill_vector"].items():
            rating = sample_self_rating(true_skill, user["user_type"])
            rows.append({
                "user_id":            user["user_id"],
                "role":               user["role"],
                "competency":         comp,
                "user_type":          user["user_type"],
                "true_skill":         round(true_skill, 3),
                "self_rating_raw":    rating["self_rating_raw"],
                "self_rating_likert": rating["self_rating_likert"],
                "confidence_bias":    rating["confidence_bias"],
                "timestamp":          ts.strftime("%Y-%m-%d %H:%M:%S"),
            })

    print(f"Total self-rating rows: {len(rows)}")

    # ── Stats ────────────────────────────────────────────────────────────
    import numpy as _np
    true_skills = [r["true_skill"] for r in rows]
    raw_ratings = [r["self_rating_raw"] for r in rows]
    biases      = [r["confidence_bias"] for r in rows]

    corr = _np.corrcoef(true_skills, raw_ratings)[0, 1]
    print(f"\nCorrelation (true_skill vs self_rating): r = {corr:.3f}")
    print(f"Mean bias: {_np.mean(biases):+.3f}  (+ = over-confident, - = under)")

    from collections import Counter
    likert_dist = Counter(r["self_rating_likert"] for r in rows)
    print(f"Likert distribution: {dict(sorted(likert_dist.items()))}")

    # Bias per user_type
    for utype in ["beginner", "intermediate", "advanced"]:
        b = [r["confidence_bias"] for r in rows if r["user_type"] == utype]
        print(f"  {utype}: mean_bias = {_np.mean(b):+.3f}")

    # Save
    out = os.path.join(ROOT_DIR, "data/raw/simulation/self_rating_log.csv")
    fieldnames = [
        "user_id", "role", "competency", "user_type",
        "true_skill", "self_rating_raw", "self_rating_likert",
        "confidence_bias", "timestamp",
    ]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved -> {out}  ({len(rows):,} rows)")
