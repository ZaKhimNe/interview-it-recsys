"""
normalize_skill_groups.py — Thêm parent taxonomy key vào skill_groups của câu hỏi.

Vấn đề: App dùng exact match skill_groups vs taxonomy key.
  - Câu có ["ANALYTICS_FUNNEL"] sẽ không được serve cho ANALYTICS_BUSINESS
  - Câu có ["DATABASE_INDEXING"] sẽ không được serve cho DATABASE_INTERNALS

Fix: Với mỗi câu, lookup granular tag trong SKILL_GROUP_TO_COMPETENCY,
thêm parent key vào skill_groups nếu chưa có.

Chạy: python utils/data/processing/normalize_skill_groups.py
"""

import os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "utils", "data", "simulation"))
from simulation_config import SKILL_GROUP_TO_COMPETENCY


def normalize_question(q: dict) -> tuple[dict, bool]:
    """Thêm parent taxonomy key vào skill_groups. Trả về (q, changed)."""
    groups = q.get("skill_groups") or q.get("skill_tags") or []
    original = set(groups)
    enriched = set(groups)

    for tag in groups:
        parent = SKILL_GROUP_TO_COMPETENCY.get(tag)
        if parent:
            enriched.add(parent)

    if enriched != original:
        q["skill_groups"] = sorted(enriched)
        return q, True
    return q, False


def process_file(path: str) -> tuple[int, int]:
    """Returns (total, changed)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Support both list and dict format (scraped files use {"questions": [...]})
    is_list = isinstance(data, list)
    qs = data if is_list else data.get("questions", [])

    if not qs:
        return 0, 0

    changed_count = 0
    normalized = []
    for q in qs:
        q_norm, changed = normalize_question(q)
        normalized.append(q_norm)
        if changed:
            changed_count += 1

    if changed_count > 0:
        if is_list:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(normalized, f, ensure_ascii=False, indent=2)
        else:
            data["questions"] = normalized
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    return len(qs), changed_count


def main():
    gen_dir     = os.path.join(ROOT, "data/raw/question_bank/generated")
    scraped_dir = os.path.join(ROOT, "data/raw/question_bank/scraped")

    files = []
    for fname in os.listdir(gen_dir):
        if fname.endswith(".json"):
            files.append(os.path.join(gen_dir, fname))
    for fname in ["scraped_github.json", "scraped_youssef.json",
                  "scraped_sql.json", "converted_tf_fb.json"]:
        p = os.path.join(scraped_dir, fname)
        if os.path.exists(p):
            files.append(p)

    total_qs = total_changed = 0
    for path in sorted(files):
        fname = os.path.basename(path)
        n, c = process_file(path)
        total_qs += n
        total_changed += c
        print(f"  {fname}: {n} questions, {c} normalized")

    print(f"\nTotal: {total_changed}/{total_qs} questions updated")

    # Verify sau khi normalize
    print("\n=== Verify coverage after normalize ===")
    jd = json.load(open(os.path.join(ROOT, "data/schemas/jd_requirements.schema.json"), encoding="utf-8"))
    all_comp = [g for role in ["DA","DS","DE"] for g in jd[role]["skill_groups"]]

    all_qs = []
    for path in files:
        data = json.load(open(path, encoding="utf-8"))
        qs = data if isinstance(data, list) else data.get("questions", [])
        all_qs.extend(qs)

    for comp in sorted(all_comp):
        matched = [q for q in all_qs if comp in q.get("skill_groups", [])]
        status = "OK" if len(matched) >= 5 else "LOW"
        print(f"  {status} {comp}: {len(matched)} questions")

    unmatched = [q for q in all_qs if not any(
        comp in q.get("skill_groups", []) for comp in all_comp)]
    print(f"\nStill unmatched: {len(unmatched)} questions")
    if unmatched[:3]:
        for q in unmatched[:3]:
            print(f"  {q.get('question_id','?')} -> {q.get('skill_groups', [])}")


if __name__ == "__main__":
    main()
