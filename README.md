# 🎯 AI Tech Interview Prep - InternHub

> Hệ thống đánh giá năng lực và mô phỏng phỏng vấn bằng AI

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/your-org/InternHub.git
cd InternHub

# 2. Tạo virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Cài đặt dependencies
pip install -r requirements.txt

# 4. Cấu hình môi trường
copy .env.example .env
# Mở .env và điền API Key

# 5. Chạy ứng dụng
streamlit run app.py
```

## 📁 Cấu trúc dự án

Xem chi tiết trong file `PROJECT_STRUCTURE.md`

## 👥 Phân công team

| Vai trò | Phạm vi | Thư mục chính |
|---------|---------|---------------|
| **Data & Backend Lead** | Data Contract, Vector năng lực, Test Generator | `data/`, `core/` |
| **AI & RecSys Lead** | Recommender, Auto-Grading, LLM Prompts | `ai_core/` |
| **App Lead** | Streamlit UI, Charts, Session State | `ui/`, `app.py` |

## 🧪 Chạy test

```bash
pytest tests/ -v
```

## 📄 License

MIT License © 2026 InternHub Team
