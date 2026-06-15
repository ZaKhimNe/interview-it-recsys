"""
_schema_check.py - Kiem tra toan bo schema consistency
"""
import json, os, re, sys, csv
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)

taxonomy = load("data/schemas/skill_taxonomy.schema.json")
jd       = load("data/schemas/jd_requirements.schema.json")

EXPECTED = {role: set(jd[role]["skill_groups"]) for role in ["DA","DS","DE"]}
ALL_TAGS  = {tag for comp in taxonomy.values() for tag in comp.get("tags", [])}

print("=" * 60)
print("GROUND TRUTH (jd_requirements.schema.json)")
print("=" * 60)
for role, comps in EXPECTED.items():
    print(f"  {role}: {sorted(comps)}")

# ─── 1. virtual_users.json ────────────────────────────────────────
print()
print("=" * 60)
print("1. virtual_users.json")
print("=" * 60)
try:
    users = load("data/raw/simulation/virtual_users.json")
    errors = []
    for role in ["DA","DS","DE"]:
        sample = next((u for u in users if u["role"] == role), None)
        if not sample:
            errors.append(f"  {role}: khong co user")
            continue
        actual   = set(sample["skill_vector"].keys())
        expected = EXPECTED[role]
        if actual == expected:
            print(f"  {role}: OK  keys={sorted(actual)}")
        else:
            missing = expected - actual
            extra   = actual - expected
            print(f"  {role}: MISMATCH")
            if missing: print(f"    Missing : {missing}")
            if extra:   print(f"    Extra   : {extra}")
            errors.append(role)

    # Check key format UPPERCASE
    bad_keys = []
    for u in users[:20]:
        for k in u["skill_vector"]:
            if k != k.upper() or not re.match(r"^[A-Z][A-Z0-9_]*$", k):
                bad_keys.append(k)
    if bad_keys:
        print(f"  FORMAT ERROR: keys khong uppercase: {set(bad_keys)}")
    else:
        print(f"  Key format (UPPERCASE): OK")
    print(f"  Total users: {len(users)}")
except Exception as e:
    print(f"  ERROR: {e}")

# ─── 2. interaction_log.csv ───────────────────────────────────────
print()
print("=" * 60)
print("2. interaction_log.csv")
print("=" * 60)
try:
    rows = []
    with open(os.path.join(ROOT, "data/raw/simulation/interaction_log.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f): rows.append(r)

    from collections import Counter
    import numpy as np

    comp_in_log = set(r["competency"] for r in rows)
    all_expected = set(c for comps in EXPECTED.values() for c in comps)

    ok_comps   = comp_in_log & all_expected
    bad_comps  = comp_in_log - all_expected
    miss_comps = all_expected - comp_in_log

    print(f"  Total rows: {len(rows):,}")
    print(f"  Competency keys in log: {sorted(comp_in_log)}")

    if bad_comps:
        print(f"  BAD (khong co trong taxonomy): {bad_comps}")
    else:
        print(f"  Bad keys: NONE")

    if miss_comps:
        print(f"  MISSING (co trong taxonomy nhung khong co trong log): {miss_comps}")
    else:
        print(f"  Missing competencies: NONE")

    # Quality distribution
    qc = Counter(r["quality_score"] for r in rows)
    total = len(rows)
    print(f"  Quality 0={qc['0']} ({qc['0']/total*100:.1f}%)  "
          f"1={qc['1']} ({qc['1']/total*100:.1f}%)  "
          f"2={qc['2']} ({qc['2']/total*100:.1f}%)")
    q1_ok = 20 <= qc["1"]/total*100 <= 25
    print(f"  Quality 1 target 20-25%: {'OK' if q1_ok else 'FAIL (can re-simulate)'}")

    # Learning curve
    early = [float(r["skill_after"]) for r in rows if int(r["session_order"]) <= 5]
    late  = [float(r["skill_after"]) for r in rows if int(r["session_order"]) >= 36]
    delta = float(np.mean(late)) - float(np.mean(early))
    print(f"  Learning curve delta: {delta:+.4f} ({'OK' if delta > 0 else 'FAIL - skill giam'})")

except Exception as e:
    print(f"  ERROR: {e}")

# ─── 3. self_rating_log.csv ──────────────────────────────────────
print()
print("=" * 60)
print("3. self_rating_log.csv")
print("=" * 60)
try:
    rows = []
    with open(os.path.join(ROOT, "data/raw/simulation/self_rating_log.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f): rows.append(r)

    comp_in_rating = set(r["competency"] for r in rows)
    bad  = comp_in_rating - all_expected
    miss = all_expected - comp_in_rating

    print(f"  Total rows: {len(rows):,}")
    print(f"  Bad competency keys: {bad if bad else 'NONE'}")
    print(f"  Missing competencies: {miss if miss else 'NONE'}")
except Exception as e:
    print(f"  ERROR: {e}")

# ─── 4. Question bank skill_groups ───────────────────────────────
print()
print("=" * 60)
print("4. Question bank skill_groups vs taxonomy tags")
print("=" * 60)
try:
    import re as _re
    all_qs = []
    gen_dir = os.path.join(ROOT, "data/raw/question_bank/generated")
    sources = [
        "data/raw/question_bank/question_bank.json",
        "data/raw/question_bank/scraped/scraped_github.json",
        "data/raw/question_bank/scraped/scraped_youssef.json",
        "data/raw/question_bank/scraped/scraped_sql.json",
        "data/raw/question_bank/scraped/converted_tf_fb.json",
    ]
    for path in sources:
        fp = os.path.join(ROOT, path)
        if not os.path.exists(fp): continue
        with open(fp, "rb") as f: raw = f.read()
        try:
            data = json.loads(raw.rstrip(b"\x00").decode("utf-8"))
            all_qs.extend(data if isinstance(data, list) else data.get("questions", []))
        except: pass

    for fname in sorted(os.listdir(gen_dir)):
        if fname.startswith("generated_") and fname.endswith(".json"):
            with open(os.path.join(gen_dir, fname), encoding="utf-8") as f:
                all_qs.extend(json.load(f))

    skill_groups_in_bank = set()
    for q in all_qs:
        for sg in (q.get("skill_groups") or q.get("skill_tags") or []):
            skill_groups_in_bank.add(sg)

    import importlib.util, sys as _sys
    spec = importlib.util.spec_from_file_location("simulation_config",
        os.path.join(ROOT, "utils", "data", "simulation", "simulation_config.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    SKILL_GROUP_TO_COMPETENCY = mod.SKILL_GROUP_TO_COMPETENCY
    unmapped = skill_groups_in_bank - set(SKILL_GROUP_TO_COMPETENCY.keys())
    mapped   = skill_groups_in_bank & set(SKILL_GROUP_TO_COMPETENCY.keys())

    print(f"  Total unique skill_groups in bank: {len(skill_groups_in_bank)}")
    print(f"  Mapped to competency: {len(mapped)}")
    if unmapped:
        print(f"  UNMAPPED (fallback to default): {sorted(unmapped)}")
    else:
        print(f"  Unmapped groups: NONE - tat ca da co trong mapping")

except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=" * 60)
print("DONE")
print("=" * 60)
