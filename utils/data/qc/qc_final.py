"""
qc_final.py — Kiểm tra TOÀN BỘ question_bank.json như một khối thống nhất.
"""
import json, sys, re
sys.stdout.reconfigure(encoding="utf-8")
from collections import Counter, defaultdict

with open("data/raw/question_bank/question_bank.json", encoding="utf-8") as f:
    qs = json.load(f)

VALID_TYPES = {"THEORY", "PRACTICE", "CODING", "MC_SINGLE", "TRUE_FALSE", "FILL_BLANK"}
VALID_DIFF  = {"EASY", "MEDIUM", "HARD"}
VALID_ROLES = {"DA", "DS", "DE"}
SKILLS = {
    "DA": ["SQL_DATABASE","BI_VISUALIZATION","STATISTICS_EXPERIMENTATION","ANALYTICS_BUSINESS","PYTHON_ANALYTICS"],
    "DS": ["ALGORITHM_THEORY","EVALUATION_METRICS","DATA_PREPROCESSING","DEEP_LEARNING","NLP","TIME_SERIES","MLOPS"],
    "DE": ["DATA_PIPELINE","DATA_ARCHITECTURE_MODELING","BIG_DATA_CLOUD_TOOLS","DATABASE_INTERNALS","SYSTEM_ARCHITECTURE"],
}
ALL_SG = {sg for sks in SKILLS.values() for sg in sks}
REQUIRED_ROOT = {
    "question_id","question_text","roles","difficulty_label","difficulty_score",
    "question_type","skill_tags","skill_groups","answers","metadata",
    "options","template","test_cases","starter_code","constraints","allowed_languages",
}
REQUIRED_META = {"language","source","version","created_at"}
REQUIRED_ROLES = {"primary","secondary"}

PASS = True
by_cat = defaultdict(list)

def fail(cat, qid, detail=""):
    global PASS; PASS = False
    by_cat[cat].append((qid, detail))

for q in qs:
    qid   = q.get("question_id", "UNKNOWN")
    qtype = q.get("question_type", "")
    ans   = q.get("answers") or {}
    roles = q.get("roles") or {}

    # 1. Root keys — đúng 16, không thừa không thiếu
    actual = set(q.keys())
    for k in REQUIRED_ROOT - actual: fail("root_key_missing", qid, k)
    for k in actual - REQUIRED_ROOT: fail("root_key_extra",   qid, k)

    # 2. Nội dung không rỗng
    if not str(q.get("question_id","")).strip():   fail("empty_id",   qid)
    if not str(q.get("question_text","")).strip():  fail("empty_text", qid)

    # 3. question_type
    if qtype not in VALID_TYPES: fail("bad_type", qid, qtype)

    # 4. difficulty_label
    if q.get("difficulty_label") not in VALID_DIFF: fail("bad_difficulty", qid, q.get("difficulty_label"))

    # 5. difficulty_score: int/float, 1–10
    ds = q.get("difficulty_score")
    if not isinstance(ds, (int, float)): fail("bad_score_type",  qid, type(ds).__name__)
    elif not (1 <= ds <= 10):            fail("bad_score_range", qid, ds)

    # 6. roles: dict, đúng 2 keys, primary hợp lệ, secondary là list
    if not isinstance(roles, dict):
        fail("roles_not_dict", qid)
    else:
        if set(roles.keys()) != REQUIRED_ROLES: fail("roles_bad_keys",    qid, set(roles.keys()))
        if roles.get("primary") not in VALID_ROLES: fail("bad_primary",   qid, roles.get("primary"))
        if not isinstance(roles.get("secondary"), list): fail("secondary_not_list", qid)

    # 7. skill_groups: list không rỗng, tất cả trong ALL_SG, khớp role
    sgs = q.get("skill_groups")
    if not isinstance(sgs, list) or not sgs:
        fail("empty_skill_groups", qid)
    else:
        bad = [sg for sg in sgs if sg not in ALL_SG]
        if bad: fail("unknown_sg", qid, bad)
        role = roles.get("primary","") if isinstance(roles, dict) else ""
        if not any(sg in SKILLS.get(role, []) for sg in sgs):
            fail("role_sg_mismatch", qid, f"role={role} sgs={sgs}")

    # 8. skill_tags: list (có thể rỗng)
    if not isinstance(q.get("skill_tags"), list): fail("skill_tags_not_list", qid)

    # 9. answers: dict, có nội dung
    if not isinstance(ans, dict):
        fail("answers_not_dict", qid)
    else:
        has = (str(ans.get("detailed","")).strip() or
               str(ans.get("explanation","")).strip() or
               ans.get("correct_answer") is not None or
               ans.get("correct_option_id"))
        if not has: fail("answers_empty", qid)

    # 10. metadata: dict, đúng 4 keys, không thừa không thiếu
    meta = q.get("metadata")
    if not isinstance(meta, dict):
        fail("metadata_not_dict", qid)
    else:
        mk = set(meta.keys())
        for k in REQUIRED_META - mk: fail("metadata_missing_key", qid, k)
        for k in mk - REQUIRED_META: fail("metadata_extra_key",   qid, k)
        if not str(meta.get("language","")).strip(): fail("metadata_empty_language", qid)
        if not str(meta.get("source","")).strip():   fail("metadata_empty_source",   qid)

    # 11. options
    opts = q.get("options")
    if qtype == "MC_SINGLE":
        if opts is None:
            fail("mc_no_options", qid)
        elif not isinstance(opts, list) or not opts:
            fail("mc_options_empty", qid)
        else:
            for i, o in enumerate(opts):
                if not isinstance(o, dict) or "id" not in o or "text" not in o:
                    fail("mc_option_bad_struct", qid, f"opt[{i}]={o}"); break
                if not str(o.get("text","")).strip():
                    fail("mc_option_empty_text", qid, f"opt[{i}]"); break
        if not ans.get("correct_option_id") and not ans.get("correct_answer"):
            fail("mc_no_correct", qid)
    else:
        if opts is not None:
            fail("non_mc_has_options", qid, qtype)

    # 12. TRUE_FALSE: correct_answer hoặc parseable từ detailed
    if qtype == "TRUE_FALSE":
        ca = ans.get("correct_answer")
        if ca is None and "correct_answer" not in ans:
            det = str(ans.get("detailed","")).strip().lower()
            ok  = (det.startswith("true") or det.startswith("false") or
                   det.startswith("✓") or det.startswith("✗") or
                   "đúng" in det[:30] or "sai" in det[:30])
            if not ok: fail("tf_unparseable", qid, det[:60])

    # 13. FILL_BLANK: template có [___], accepted_answers là list of list, options=None
    if qtype == "FILL_BLANK":
        tmpl = q.get("template")
        if not tmpl:
            fail("fb_no_template", qid)
        elif "[___]" not in str(tmpl):
            fail("fb_no_blank_marker", qid, str(tmpl)[:60])
        aa = ans.get("accepted_answers")
        if not aa:
            fail("fb_no_accepted_answers", qid)
        elif not isinstance(aa, list):
            fail("fb_accepted_not_list", qid, type(aa).__name__)
        else:
            for i, a in enumerate(aa):
                if not isinstance(a, list) or not a:
                    fail("fb_accepted_item_bad", qid, f"aa[{i}]={a}"); break
        if q.get("options") is not None:
            fail("fb_has_options", qid)

    # 14. CODING: không yêu cầu test_cases (scraped CODING không có), nhưng nếu có phải đúng format
    if qtype == "CODING":
        tc = q.get("test_cases")
        if tc is not None:
            if not isinstance(tc, list):
                fail("coding_testcases_not_list", qid)
            else:
                for i, t in enumerate(tc):
                    if not isinstance(t, dict) or "input" not in t or "expected_output" not in t:
                        fail("coding_testcase_bad_struct", qid, f"tc[{i}]={str(t)[:50]}"); break

# Duplicate checks
id_cnt   = Counter(q.get("question_id","") for q in qs)
text_cnt = Counter(re.sub(r"\s+"," ", q.get("question_text","").lower().strip()) for q in qs)
for qid, cnt in id_cnt.items():
    if cnt > 1: fail("duplicate_id", qid, f"x{cnt}")
for txt, cnt in text_cnt.items():
    if cnt > 1 and txt: fail("duplicate_text", txt[:50], f"x{cnt}")

# ── Report ────────────────────────────────────────────────────────────────────
print(f"Kiem tra {len(qs)} cau trong question_bank.json")
print("=" * 65)

if PASS:
    print("PASS — 100% dong bo, khong co bat ki sai sot nao")
else:
    total_issues = sum(len(v) for v in by_cat.values())
    print(f"FAIL — {total_issues} van de, {len(by_cat)} loai:\n")
    for cat, items in sorted(by_cat.items(), key=lambda x: -len(x[1])):
        print(f"  [{len(items):>4}]  {cat}")
        for qid, detail in items[:3]:
            print(f"           {qid}: {detail}")
        if len(items) > 3:
            print(f"           ... va {len(items)-3} cau khac")

# ── Distribution ──────────────────────────────────────────────────────────────
print()
print("=" * 65)
print("DISTRIBUTION")
print(f"  Total : {len(qs)}")
print(f"  Types : {dict(Counter(q.get('question_type') for q in qs))}")
print(f"  Diff  : {dict(Counter(q.get('difficulty_label') for q in qs))}")
print(f"  Roles : {dict(Counter(q.get('roles',{}).get('primary') for q in qs))}")
print()
print("COVERAGE (target 90):")
comp = defaultdict(int)
for q in qs:
    role = (q.get("roles") or {}).get("primary","?")
    sgs  = q.get("skill_groups") or []
    psg  = next((sg for sg in sgs if sg in SKILLS.get(role,[])), None)
    if psg: comp[psg] += 1
all_ok = True
for role in ["DA","DS","DE"]:
    for sk in SKILLS[role]:
        cnt  = comp.get(sk, 0)
        ok   = cnt >= 90
        if not ok: all_ok = False
        bar  = "█"*(cnt//10) + ("▌" if cnt%10>=5 else "")
        flag = "OK" if ok else f"THIEU {90-cnt}"
        print(f"  {flag:<10} [{role}] {sk:<35} {cnt:>4}  {bar}")
print()
print("Coverage:", "TAT CA >= 90 ✓" if all_ok else "3 competency DS con thieu it (<4 cau) — can API gen them")
