"""
📝 Auto Grader - LLM-based Answer Evaluation
==============================================
Người phụ trách: AI & RecSys Lead
Mục đích: Sử dụng Google Gemini API để chấm điểm câu trả lời
          của ứng viên một cách tự động. Trả về điểm số và feedback.
"""

from typing import Optional
from config import GOOGLE_API_KEY, LLM_MODEL_NAME, LLM_TEMPERATURE


def grade_answer(
    question: str,
    expected_answer: str,
    candidate_answer: str,
    scoring_rubric: Optional[str] = None,
) -> dict:
    """
    Chấm điểm câu trả lời bằng LLM.

    Args:
        question: Nội dung câu hỏi
        expected_answer: Đáp án tham khảo
        candidate_answer: Câu trả lời của ứng viên
        scoring_rubric: Tiêu chí chấm điểm (tuỳ chọn)

    Returns:
        {
            "score": float (0-10),
            "feedback": str,
            "strengths": list[str],
            "improvements": list[str]
        }
    """
    # TODO: AI Lead implement LLM grading logic ở đây
    # Gợi ý: Dùng google.generativeai với structured prompt
    pass


def generate_follow_up(
    question: str,
    candidate_answer: str,
    difficulty: str = "medium",
) -> str:
    """
    Sinh câu hỏi follow-up dựa trên câu trả lời của ứng viên.
    Mô phỏng hành vi phỏng vấn viên thực tế.

    Args:
        question: Câu hỏi gốc
        candidate_answer: Câu trả lời của ứng viên
        difficulty: Độ khó mong muốn

    Returns:
        Câu hỏi follow-up
    """
    # TODO: AI Lead implement follow-up generation
    pass
