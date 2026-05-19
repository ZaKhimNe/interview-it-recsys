import json
from pathlib import Path


QUESTION_DATA_PATH = Path("data/mock/mock_question_data.json")


def load_json(path: Path):
    """
    Đọc file JSON và trả về dữ liệu Python.
    """
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_question(raw_q: dict) -> dict:
    """
    Chuẩn hóa data câu hỏi từ file mock mới về format UI hiện tại đang dùng.
    """

    question_id = (
        raw_q.get("question_id")
        or raw_q.get("id")
        or raw_q.get("qid")
        or "UNKNOWN_ID"
    )

    question_text = (
        raw_q.get("question_text")
        or raw_q.get("question")
        or raw_q.get("prompt")
        or raw_q.get("content")
        or raw_q.get("scenario")
        or "Không tìm thấy nội dung câu hỏi."
    )

    # Chuẩn hóa role
    role = None

    if isinstance(raw_q.get("roles"), dict):
        role = raw_q.get("roles", {}).get("primary")

    elif isinstance(raw_q.get("roles"), list) and raw_q.get("roles"):
        role = raw_q.get("roles")[0]

    role = (
        role
        or raw_q.get("role")
        or raw_q.get("target_role")
        or raw_q.get("primary_role")
        or "DA"
    )

    # Chuẩn hóa skill tags
    skill_tags = (
        raw_q.get("skill_tags")
        or raw_q.get("skills")
        or raw_q.get("competency_tags")
        or raw_q.get("skill_ids")
        or []
    )

    if isinstance(skill_tags, str):
        skill_tags = [skill_tags]

    # Chuẩn hóa đáp án
    raw_answers = raw_q.get("answers", {})

    if isinstance(raw_answers, dict):
        detailed_answer = (
            raw_answers.get("detailed")
            or raw_answers.get("sample_answer")
            or raw_answers.get("expert_answer")
            or raw_answers.get("reference_answer")
            or raw_q.get("answer")
            or raw_q.get("sample_answer")
            or raw_q.get("expert_answer")
            or "Chưa có đáp án mẫu."
        )

        evaluation_points = (
            raw_answers.get("evaluation_points")
            or raw_answers.get("rubric")
            or raw_answers.get("criteria")
            or raw_q.get("evaluation_points")
            or raw_q.get("rubric")
            or raw_q.get("criteria")
            or []
        )

    else:
        detailed_answer = str(raw_answers)
        evaluation_points = raw_q.get("evaluation_points", [])

    if isinstance(evaluation_points, str):
        evaluation_points = [evaluation_points]

    return {
        "question_id": question_id,
        "question_text": question_text,
        "roles": {
            "primary": role
        },
        "skill_tags": skill_tags,
        "answers": {
            "detailed": detailed_answer,
            "evaluation_points": evaluation_points
        }
    }


def load_question_bank():
    """
    Load question bank từ data mới của partner:
    data/mock/mock_question_data.json

    Hàm này trả về format cũ để ui/screens.py vẫn dùng được.
    """
    raw_data = load_json(QUESTION_DATA_PATH)

    if isinstance(raw_data, list):
        questions = raw_data

    elif isinstance(raw_data, dict):
        questions = (
            raw_data.get("questions")
            or raw_data.get("question_bank")
            or raw_data.get("data")
            or raw_data.get("items")
            or []
        )

    else:
        questions = []

    return [
        normalize_question(question)
        for question in questions
        if isinstance(question, dict)
    ]