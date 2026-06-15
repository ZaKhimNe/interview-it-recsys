"""
mark_old_as_reviewed.py — Đánh dấu câu hỏi CŨ là qc_reviewed=True dựa trên mock_question_data.json.

Logic:
  - mock_question_data.json chứa snapshot TRƯỚC khi generate thêm → "old IDs"
  - Generated files chứa old + new
  - Câu nào có ID trong old set → mark qc_reviewed=True (skip khi --only-new)
  - Câu mới (không có trong old set) → giữ nguyên → sẽ được review bởi --only-new

Sau khi chạy script này:
  python utils/data/qc/qc_rag.py --all --only-new   ← chỉ review câu mới

Chạy: python utils/data/qc/mark_old_as_reviewed.py
       python utils/data/qc/mark_old_as_reviewed.py --dry-run   # xem số liệu trước
       python utils/data/qc/mark_old_as_reviewed.py --undo      # bỏ qc_reviewed khỏi TẤT CẢ
"""

import os, sys, json, argparse
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def load_old_ids() -> set:
    """Lấy tập ID từ mock_question_data.json (snapshot cũ)."""
    path = os.path.join(ROOT, "data", "raw", "question_bank", "question_bank.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Không tìm thấy {path} — cần file này làm mốc cũ.")
    data = json.load(open(path, encoding="utf-8"))
    qs = data if isinstance(data, list) else data.get("questions", [])
    ids = {str(q.get("question_id", "")) for q in qs if q.get("question_id")}
    print(f"Old snapshot: {len(ids)} IDs từ mock_question_data.json")
    return ids


def process_generated_files(old_ids: set, dry_run: bool = False, undo: bool = False):
    gen_dir = os.path.join(ROOT, "data", "raw", "question_bank", "generated")
    total_old = total_new = total_marked = 0

    for fname in sorted(os.listdir(gen_dir)):
        if not (fname.startswith("generated_") and fname.endswith(".json")):
            continue
        path = os.path.join(gen_dir, fname)
        qs = json.load(open(path, encoding="utf-8"))
        if not isinstance(qs, list):
            continue

        file_old = file_new = file_marked = 0
        updated = []
        for q in qs:
            qid = str(q.get("question_id", ""))
            if undo:
                # Xóa qc_reviewed khỏi tất cả
                if "qc_reviewed" in q:
                    q.pop("qc_reviewed")
                    file_marked += 1
                updated.append(q)
            elif qid in old_ids:
                file_old += 1
                if not q.get("qc_reviewed"):
                    q["qc_reviewed"] = True
                    file_marked += 1
                updated.append(q)
            else:
                file_new += 1
                updated.append(q)

        total_old += file_old
        total_new += file_new
        total_marked += file_marked

        if undo:
            label = f"cleared {file_marked} qc_reviewed"
        else:
            label = f"old={file_old} new={file_new} marked={file_marked}"
        print(f"  {fname}: {label}")

        if not dry_run and (file_marked > 0):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(updated, f, ensure_ascii=False, indent=2)

    if undo:
        print(f"\n{'[DRY-RUN] ' if dry_run else ''}Undo xong: đã xóa qc_reviewed khỏi {total_marked} câu.")
    else:
        print(f"\n{'[DRY-RUN] ' if dry_run else ''}Kết quả:")
        print(f"  Câu cũ (đã mark):  {total_old}  (sẽ bị skip bởi --only-new)")
        print(f"  Câu mới (để nguyên): {total_new}  (sẽ được review)")
        print(f"  Tổng đã mark:      {total_marked}")
        if not dry_run:
            print(f"\nBước tiếp theo:")
            print(f"  python utils/data/qc/qc_rag.py --all --only-new --dry-run  # xác nhận số câu review")
            print(f"  python utils/data/qc/qc_rag.py --all --only-new             # chạy thật")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Xem số liệu, không ghi file")
    parser.add_argument("--undo", action="store_true", help="Xóa qc_reviewed khỏi tất cả câu (reset)")
    args = parser.parse_args()

    if args.undo:
        print("=== UNDO: Xóa qc_reviewed khỏi toàn bộ generated files ===")
        process_generated_files(set(), dry_run=args.dry_run, undo=True)
    else:
        print("=== Mark câu CŨ là qc_reviewed=True ===")
        old_ids = load_old_ids()
        process_generated_files(old_ids, dry_run=args.dry_run, undo=False)


if __name__ == "__main__":
    main()
