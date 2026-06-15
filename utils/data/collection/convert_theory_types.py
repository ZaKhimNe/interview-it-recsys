"""
Convert THEORY questions → TRUE_FALSE và FILL_BLANK (rule-based, không cần LLM)

Logic:
  TRUE_FALSE : lấy câu statement đầu tiên từ answer → True version
               negate bằng antonym rules → False version
  FILL_BLANK : extract key term từ question ("What is X?") → blank X trong answer

Input:  data/raw/question_bank_v1.json
Output: data/raw/converted_tf_fb.json

Chạy: python utils/data/collection/convert_theory_types.py
"""

import json, re, random
from datetime import date
from collections import Counter

SEED = 42
random.seed(SEED)

TARGET_TF = 100   # 50 True + 50 False
TARGET_FB = 80

# ── Antonym rules cho TRUE_FALSE negation ───────────────────────────────
# (pattern, replacement) — áp dụng pattern đầu tiên match
ANTONYM_RULES = [
    (r'\bis not\b',           'is'),           # tránh double-negate
    (r'\bare not\b',          'are'),
    (r'\bis\b',               'is not'),
    (r'\bare\b',              'are not'),
    (r'\bcan\b',              'cannot'),
    (r'\bcannot\b',           'can'),
    (r'\bincreases?\b',       'decreases'),
    (r'\bdecreases?\b',       'increases'),
    (r'\breduces?\b',         'increases'),
    (r'\bimproves?\b',        'worsens'),
    (r'\balways\b',           'never'),
    (r'\bnever\b',            'always'),
    (r'\bhigher\b',           'lower'),
    (r'\blower\b',            'higher'),
    (r'\bfaster\b',           'slower'),
    (r'\bslower\b',           'faster'),
    (r'\bmore\b',             'less'),
    (r'\bless\b',             'more'),
    (r'\bparallel\b',         'sequential'),
    (r'\bsequential\b',       'parallel'),
    (r'\bsupervised\b',       'unsupervised'),
    (r'\bunsupervised\b',     'supervised'),
    (r'\bvariance\b',         'bias'),
    (r'\bbias\b',             'variance'),
    (r'\bdistributed\b',      'centralized'),
    (r'\bcentralized\b',      'distributed'),
    (r'\bsynchronous\b',      'asynchronous'),
    (r'\basynchronous\b',     'synchronous'),
    (r'\brelational\b',       'non-relational'),
    (r'\bstateful\b',         'stateless'),
    (r'\bstateless\b',        'stateful'),
    (r'\bscalable\b',         'not scalable'),
    (r'\bfault.tolerant\b',   'not fault-tolerant'),
    (r'\blossless\b',         'lossy'),
    (r'\blossy\b',            'lossless'),
]


def negate_sentence(sentence: str):
    """Áp dụng antonym rule đầu tiên match. Trả về None nếu không negate được."""
    for pattern, replacement in ANTONYM_RULES:
        if re.search(pattern, sentence, re.IGNORECASE):
            negated = re.sub(pattern, replacement, sentence, count=1, flags=re.IGNORECASE)
            if negated.lower() != sentence.lower():
                return negated
    return None


def extract_clean_sentences(text: str) -> list:
    """Bỏ code block + markdown, trả về list câu có ý nghĩa."""
    # Bỏ code blocks
    text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', ' ', text)
    # Bỏ markdown formatting
    text = re.sub(r'\*{1,2}|_{1,2}|#{1,6}\s?', '', text)
    # Bỏ bullet points
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    # Bỏ image/link markdown
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)

    # Tách câu
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    good = []
    for s in sentences:
        s = s.strip()
        if (len(s) > 40                          # đủ dài
                and s[0].isupper()               # bắt đầu bằng hoa
                and not s.startswith(('http', 'Note', 'Example', 'E.g'))
                and sum(c.isalpha() for c in s) > 20):  # chủ yếu chữ
            good.append(s)
    return good


# ── TRUE_FALSE ────────────────────────────────────────────────────────────

def make_true_false(q: dict) -> list:
    """Tạo 1 True + 1 False từ 1 THEORY question. Trả về list 1-2 items."""
    answer = q["answers"]["detailed"]
    sentences = extract_clean_sentences(answer)
    if not sentences:
        return []

    # Chọn câu statement đầu tiên có độ dài hợp lý
    true_stmt = None
    for s in sentences[:4]:
        if 40 < len(s) < 150:
            true_stmt = s
            break
    if not true_stmt:
        true_stmt = sentences[0][:130].rsplit(' ', 1)[0]

    results = []

    # TRUE version
    results.append({
        "question_text": f"True or False: {true_stmt}",
        "answer": (
            f"✓ True.\n\n"
            f"Explanation: {answer[:450].strip()}"
        ),
        "is_correct": True,
    })

    # FALSE version — negate
    false_stmt = negate_sentence(true_stmt)
    if false_stmt:
        results.append({
            "question_text": f"True or False: {false_stmt}",
            "answer": (
                f"✗ False.\n\n"
                f"Correction: {true_stmt}\n\n"
                f"Explanation: {answer[:350].strip()}"
            ),
            "is_correct": False,
        })

    return results


# ── FILL_BLANK ────────────────────────────────────────────────────────────

# Pattern extract key term từ question text
QUESTION_PATTERNS = [
    r'[Ww]hat (?:is|are) (?:the |a |an )?(.+?)(?:\?|$|\s+in\s|\s+and\s)',
    r'[Dd]efine (?:the |a |an )?(.+?)(?:\?|$)',
    r'[Ee]xplain (?:what |the |how )?(.+?)(?:\?|$)',
    r'[Dd]escribe (?:the |a |an )?(.+?)(?:\?|$)',
    r'[Ww]hat do you (?:understand|mean) by (.+?)(?:\?|$)',
]


def extract_key_term(question_text: str):
    """Extract key term từ câu hỏi dạng 'What is X?'"""
    for pattern in QUESTION_PATTERNS:
        m = re.search(pattern, question_text)
        if m:
            term = m.group(1).strip().rstrip('?.,').strip()
            # Bỏ sub-clause dài
            term = re.split(r'\s+(?:in|and|or|with|for|of)\s+', term)[0].strip()
            if 3 < len(term) < 60:
                return term
    return None


def make_fill_blank(q: dict):
    """Tạo FILL_BLANK từ THEORY question. Trả về dict hoặc None."""
    question_text = q["question_text"]
    answer        = q["answers"]["detailed"]

    key_term = extract_key_term(question_text)
    if not key_term:
        return None

    # Tìm key term trong answer → blank nó
    sentences = extract_clean_sentences(answer)
    for sent in sentences[:6]:
        if key_term.lower() in sent.lower():
            blanked = re.sub(
                re.escape(key_term), '_____',
                sent, count=1, flags=re.IGNORECASE
            )
            if '_____' in blanked:
                return {
                    "question_text": f"Fill in the blank: {blanked}",
                    "answer": (
                        f"Answer: {key_term.title()}\n\n"
                        f"Full explanation: {answer[:400].strip()}"
                    ),
                    "keyword": key_term,
                }

    # Fallback: tạo câu fill blank từ question text
    blanked_q = re.sub(
        re.escape(key_term), '_____',
        question_text, count=1, flags=re.IGNORECASE
    )
    if '_____' in blanked_q:
        return {
            "question_text": f"Fill in the blank: {blanked_q}",
            "answer": (
                f"Answer: {key_term.title()}\n\n"
                f"Explanation: {answer[:400].strip()}"
            ),
            "keyword": key_term,
        }
    return None


# ── Schema converter ────────────────────────────────────────────────────

DIFF_SCORE_MAP = {"EASY": 2, "MEDIUM": 5, "HARD": 8}

def to_schema(item: dict, q_type: str, source_q: dict, idx: int) -> dict:
    prefix = "TF" if q_type == "TRUE_FALSE" else "FB"
    diff_label = source_q["difficulty_label"]
    return {
        "question_id":      f"CONV_{prefix}_{idx:04d}",
        "question_text":    item["question_text"],
        "roles":            source_q["roles"],
        "difficulty_label": diff_label,
        "difficulty_score": source_q.get("difficulty_score",
                                         DIFF_SCORE_MAP.get(diff_label, 5)),
        "question_type":    q_type,
        "skill_groups":     source_q["skill_groups"],
        "skill_tags":       source_q["skill_tags"],
        "answers": {
            "detailed":          item["answer"],
            "evaluation_points": [],
        },
        "metadata": {
            "language":       "en",
            "source":         f"converted_from/{source_q['question_id']}",
            "converted_from": source_q["question_id"],
            "version":        "v1.0",
            "created_at":     str(date.today()),
        },
    }


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os

    # Load question bank
    with open("data/raw/question_bank_v1.json", "rb") as f:
        bank = json.loads(f.read().rstrip(b'\x00').decode("utf-8"))

    theory_qs = [q for q in bank["questions"] if q["question_type"] == "THEORY"]
    print(f"THEORY questions available: {len(theory_qs)}")

    # Shuffle để lấy đa dạng nguồn
    random.shuffle(theory_qs)

    # ── TRUE_FALSE ─────────────────────────────────────────────────────
    tf_results, tf_idx = [], 1
    true_count = false_count = 0
    tf_target_each = TARGET_TF // 2   # 50 True, 50 False

    for q in theory_qs:
        if true_count >= tf_target_each and false_count >= tf_target_each:
            break
        items = make_true_false(q)
        for item in items:
            if item["is_correct"] and true_count < tf_target_each:
                tf_results.append(to_schema(item, "TRUE_FALSE", q, tf_idx))
                tf_idx += 1
                true_count += 1
            elif not item["is_correct"] and false_count < tf_target_each:
                tf_results.append(to_schema(item, "TRUE_FALSE", q, tf_idx))
                tf_idx += 1
                false_count += 1

    print(f"\nTRUE_FALSE generated: {len(tf_results)}")
    print(f"  True:  {true_count}")
    print(f"  False: {false_count}")

    # ── FILL_BLANK ─────────────────────────────────────────────────────
    fb_results, fb_idx = [], 1
    # Dùng subset theory_qs khác để tránh dùng cùng câu
    used_ids = {r["metadata"]["converted_from"] for r in tf_results}
    fb_candidates = [q for q in theory_qs if q["question_id"] not in used_ids]

    for q in fb_candidates:
        if len(fb_results) >= TARGET_FB:
            break
        item = make_fill_blank(q)
        if item:
            fb_results.append(to_schema(item, "FILL_BLANK", q, fb_idx))
            fb_idx += 1

    print(f"\nFILL_BLANK generated: {len(fb_results)}")

    # ── Stats ──────────────────────────────────────────────────────────
    all_converted = tf_results + fb_results
    print(f"\n── Stats ──────────────────────────")
    print(f"Total:  {len(all_converted)}")
    print(f"Types:  {dict(Counter(q['question_type'] for q in all_converted))}")
    print(f"Roles:  {dict(Counter(q['roles']['primary'] for q in all_converted))}")
    print(f"Diff:   {dict(Counter(q['difficulty_label'] for q in all_converted))}")

    # Sample check
    print(f"\n── Sample TRUE_FALSE ──")
    if tf_results:
        s = tf_results[0]
        print(f"  Q: {s['question_text'][:100]}")
        print(f"  A: {s['answers']['detailed'][:80]}")

    print(f"\n── Sample FILL_BLANK ──")
    if fb_results:
        s = fb_results[0]
        print(f"  Q: {s['question_text'][:100]}")
        print(f"  A: {s['answers']['detailed'][:80]}")

    # ── Save ────────────────────────────────────────────────────────────
    os.makedirs("data/raw", exist_ok=True)
    out_path = "data/raw/converted_tf_fb.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"questions": all_converted}, f, ensure_ascii=False, indent=2)

    print(f"\nSaved → {out_path}")
    print("Tiếp theo: thêm file này vào SOURCES trong merge_validate.py rồi chạy lại merge.")
