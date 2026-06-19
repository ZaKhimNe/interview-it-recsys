"""
Prompt Templates
Mục đích: Tập trung quản lý tất cả prompt template cho LLM.
"""

# ── Grading ────────────────────────────────────────────────────────────────────
GRADING_PROMPT = """
Bạn là chuyên gia chấm điểm phỏng vấn kỹ thuật. Hãy chấm điểm khách quan và nhất quán.

**Câu hỏi:** {question}

**Đáp án tham khảo:**
{expected_answer}

**Các ý chính cần có:**
{evaluation_points}

**Câu trả lời ứng viên:**
{candidate_answer}

**Rubric:** {scoring_rubric}

Thang điểm:
- 0–3 : Sai hoặc hoàn toàn không liên quan
- 4–5 : Đúng một phần, thiếu ý chính
- 6–7 : Đủ ý chính, thiếu chiều sâu / ví dụ
- 8–9 : Đầy đủ, có ví dụ cụ thể, giải thích rõ
- 10  : Xuất sắc — đề cập trade-off và edge case

Trả về JSON hợp lệ (score là số thực, không có markdown):
{{"score": <0-10>, "feedback": "<nhận xét ngắn gọn>", "strengths": ["<điểm mạnh>"], "improvements": ["<điểm cần cải thiện>"]}}
""".strip()


# ── Follow-up ──────────────────────────────────────────────────────────────────
# Biến cần format:
#   {question}         — câu hỏi gốc
#   {candidate_answer} — câu trả lời ứng viên
#   {difficulty}       — easy / medium / hard
#   {weak_points}      — điểm cần cải thiện từ grade_result
FOLLOW_UP_PROMPT = """
Bạn là người phỏng vấn kỹ thuật. Dựa trên câu trả lời dưới đây, hãy đặt 1 câu hỏi follow-up
ngắn gọn, sắc bén ở mức độ {difficulty}.

**Câu hỏi gốc:** {question}

**Câu trả lời ứng viên:** {candidate_answer}

**Điểm cần cải thiện:** {weak_points}

Yêu cầu:
- Chỉ trả về 1 câu hỏi, không giải thích thêm.
- Câu hỏi phải liên quan trực tiếp đến nội dung ứng viên vừa trình bày.
- Nếu câu trả lời tốt, hãy đào sâu vào trade-off hoặc edge case.
- Nếu câu trả lời yếu, hãy hỏi lại phần bị thiếu.
""".strip()
