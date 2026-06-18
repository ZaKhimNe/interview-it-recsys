## Sơ đồ kiến trúc

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit UI (ui/)                │
│  ┌────────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ onboarding │  │ sidebar  │  │ pages/         │  │
│  │ .py        │  │ .py      │  │ ├ assessment   │  │
│  └────────────┘  └──────────┘  │ ├ interview    │  │
│  ┌─────────────────────────┐   │ └ dashboard    │  │
│  │   session_manager.py    │   └────────────────┘  │
│  └─────────────────────────┘                        │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────▼────────────┐
        │   core/ (Business)     │
        │  ┌──────────────────┐  │
        │  │competency_engine │  │
        │  │test_generator    │  │
        │  │data_loader       │  │
        │  │schema_validator  │  │
        │  └──────────────────┘  │
        └───────┬────────┬───────┘
                │        │
    ┌───────────▼──┐  ┌──▼──────────────────┐
    │   data/      │  │   ai_core/           │
    │  questions/  │  │  ┌────────────────┐  │
    │  schemas/    │  │  │ grader.py      │  │
    │  vector_store│  │  │ recommender.py │  │
    └──────────────┘  │  │ prompts.py     │  │
                      │  └────────────────┘  │
                      │         │            │
                      │  Google Gemini API   │
                      └─────────────────────┘
```

---

## Cây thư mục

```
it-interview-recsys/
│
├── app.py                      # Điểm vào chính, cấu hình Streamlit và routing
├── config.py                   # Hằng số toàn cục, API key, cấu hình LLM
├── requirements.txt            # Danh sách dependency Python
├── .env                        # Biến môi trường bí mật (không commit)
├── .gitignore                  # Loại trừ .env, venv/, __pycache__, v.v.
├── README.md                   # Hướng dẫn cài đặt và chạy nhanh
│
├── ai_core/                    # Lớp xử lý AI & LLM
│   ├── __init__.py
│   ├── grader.py               # Chấm điểm câu trả lời bằng Gemini
│   ├── prompts.py              # Kho prompt tập trung (system & user)
│   └── recommender.py          # Gợi ý câu hỏi & điều chỉnh độ khó thích nghi
│
├── core/                       # Lớp nghiệp vụ (Business Logic)
│   ├── __init__.py
│   ├── competency_engine.py    # Tính toán vector năng lực 6 chiều (EMA)
│   ├── data_loader.py          # Đọc/parse file JSON, load ngân hàng câu hỏi
│   ├── schema_validator.py     # Kiểm tra tính hợp lệ của dữ liệu (Pydantic)
│   └── test_generator.py       # Tạo bộ đề đánh giá ban đầu theo role & độ khó
│
├── ui/                         # Lớp giao diện (Streamlit)
│   ├── __init__.py
│   ├── session_manager.py      # Quản lý tập trung st.session_state
│   ├── onboarding.py           # Màn hình chọn role ban đầu (hero screen)
│   ├── screens.py              # Điều hướng đa bước, switch giữa các trang
│   ├── sidebar.py              # Thanh điều hướng bên trái
│   ├── styles.py               # CSS tùy chỉnh inject vào Streamlit
│   ├── components/
│   │   ├── __init__.py
│   │   ├── charts.py           # Biểu đồ Plotly tái sử dụng (radar, bar)
│   │   └── shared.py           # Widget UI dùng chung (card, badge, alert)
│   └── pages/
│       ├── __init__.py
│       ├── assessment.py       # Trang đánh giá năng lực ban đầu
│       ├── dashboard.py        # Trang tổng quan điểm số & tiến trình
│       └── interview.py        # Trang mô phỏng buổi phỏng vấn
│
├── data/
│   ├── mock/
│   │   └── mockdata.json       # Ngân hàng 1700+ câu hỏi (DA/DE/DS, đã kiểm duyệt)
│   ├── raw/                    # Dữ liệu thô chưa qua xử lý (dùng cho tương lai)
│   ├── schemas/
│   │   ├── question_bank.schema.json   # Contract cấu trúc câu hỏi
│   │   └── user_profile.schema.json    # Contract cấu trúc hồ sơ người dùng
│   └── vector_store/           # ChromaDB embedding store (cho tính năng RAG)
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py              # Hàm tiện ích: xử lý chuỗi, định dạng thời gian
│   └── logger.py               # Cấu hình Loguru: rotation, format, level
│
├── tests/
│   ├── __init__.py
│   ├── test_ai_core.py         # Test cho module ai_core (grader, recommender)
│   └── test_core.py            # Test cho module core (engine, loader, validator)
│
└── assets/
    ├── onboarding_bg.png       # Ảnh nền màn hình chọn role
    ├── role_da_bg.png          # Ảnh nền role Data Analyst
    ├── role_de_bg.png          # Ảnh nền role Data Engineer
    └── role_ds_bg.png          # Ảnh nền role Data Scientist
```

---

## Mô tả chi tiết từng module

### `app.py` — Điểm vào chính
- Cấu hình Streamlit: `page_title`, `layout="wide"`, `page_icon`
- Gọi `init_session_state()` để khởi tạo state toàn cục
- Routing: nếu `user_role` chưa chọn → `show_onboarding()`, ngược lại → `show_main_app()`
- **Không chứa logic nghiệp vụ hay tính toán**

---

### `config.py` — Cấu hình toàn cục
- Đọc biến môi trường từ `.env` qua `python-dotenv`
- Khai báo: `GOOGLE_API_KEY`, `LLM_MODEL_NAME` (`gemini-2.0-flash`), `LLM_TEMPERATURE` (0.3)
- `COMPETENCY_DOMAINS`: danh sách 6 lĩnh vực năng lực
- `DATA_DIR`, `VECTOR_STORE_PATH`: đường dẫn dữ liệu
- **Quy tắc: mọi hằng số phải khai báo ở đây, không hardcode trong code**

---

### `ai_core/prompts.py` — Kho prompt tập trung
- `GRADING_PROMPT`: hướng dẫn Gemini chấm điểm (0–10), trả về JSON với `score`, `feedback`, `strengths`, `improvements`
- `FOLLOW_UP_PROMPT`: yêu cầu Gemini tạo câu hỏi khai thác sâu hơn
- `INTERVIEW_SYSTEM_PROMPT`: thiết lập persona "người phỏng vấn kỹ thuật chuyên nghiệp"
- **Quy tắc: App Lead không được viết prompt trực tiếp trong file UI**

### `ai_core/grader.py` — Chấm điểm tự động
- `grade_answer(question, user_answer, reference_answer)` → `dict`
  - Gọi Gemini API với `GRADING_PROMPT`
  - Trả về: `{score: 0-10, feedback: str, strengths: [], improvements: []}`
- `generate_follow_up(question, answer)` → `str`
  - Sinh câu hỏi tiếp theo dựa trên câu trả lời hiện tại
- **Trạng thái: TODO — chờ AI Lead triển khai**

### `ai_core/recommender.py` — Gợi ý thích nghi
- `recommend_questions(competency_vector, question_bank)` → `list[dict]`
  - Phân tích vector năng lực, ưu tiên domain yếu nhất
  - Trả về 5 câu hỏi phù hợp nhất
- `adaptive_difficulty(history)` → `"easy" | "medium" | "hard"`
  - Điều chỉnh độ khó dựa trên lịch sử trả lời gần nhất
- **Trạng thái: TODO — chờ AI Lead triển khai**

---

### `core/competency_engine.py` — Vector năng lực
- `create_competency_vector(scores_dict)` → `ndarray shape (6,)`
  - Chuyển dict điểm theo skill → vector numpy 6 chiều theo `COMPETENCY_DOMAINS`
- `update_competency(old_vector, new_scores, alpha=0.3)` → `ndarray`
  - Cập nhật bằng Exponential Moving Average: `new = (1-α)*old + α*new_scores`
- `identify_weak_domains(vector, threshold=5.0)` → `list[str]`
  - Trả về tên các domain có điểm < ngưỡng

### `core/test_generator.py` — Tạo đề đánh giá
- `generate_entry_test(question_bank, role, n=10)` → `list[dict]`
  - Lọc câu hỏi theo role (DA/DE/DS)
  - Phân bổ mặc định: 4 dễ + 4 trung bình + 2 khó
  - Trộn ngẫu nhiên trước khi trả về

### `core/data_loader.py` — Đọc dữ liệu
- `load_json(filepath)` → `Any` — đọc file JSON bất kỳ với encoding UTF-8
- `load_question_bank(data_dir)` → `list[dict]` — load `mockdata.json` từ thư mục data
- `load_user_profiles(data_dir)` → `list[dict]` — load hồ sơ người dùng mẫu

### `core/schema_validator.py` — Kiểm tra dữ liệu
- `validate_question(question_dict)` → `(bool, str)` — kiểm tra theo `question_bank.schema.json`
- `validate_user_profile(profile_dict)` → `(bool, str)` — kiểm tra theo `user_profile.schema.json`
- **Quy tắc: luôn validate trước khi lưu vào data/ hoặc gửi cho AI**

---

### `ui/session_manager.py` — Quản lý trạng thái
- `init_session_state()` — khởi tạo tất cả biến `st.session_state` với giá trị mặc định
- `get_state(key)` / `set_state(key, value)` — accessor an toàn tránh KeyError
- `reset_session()` — xóa toàn bộ state (dùng khi đổi role hoặc bắt đầu lại)
- **Biến quan trọng:** `user_role`, `competency_vector`, `current_question`, `answer_history`, `demo_step`

### `ui/onboarding.py` — Màn hình chọn role
- `show_onboarding()` — hiển thị hero screen với 3 lựa chọn: DA, DE, DS
- Khi chọn xong: ghi `st.session_state.user_role` và rerun

### `ui/screens.py` — Điều hướng đa bước
- `show_main_app()` — switch giữa các trang dựa trên `active_page` trong session

### `ui/sidebar.py` — Thanh bên
- `show_sidebar()` — hiển thị navigation menu với `streamlit-option-menu`
- Cho phép chuyển giữa Assessment / Interview / Dashboard

### `ui/styles.py` — CSS tùy chỉnh
- `inject_custom_css()` — inject CSS qua `st.markdown(unsafe_allow_html=True)`
- Ghi đè giao diện mặc định của Streamlit (font, màu, border-radius, v.v.)

### `ui/components/charts.py` — Biểu đồ
- `render_radar_chart(competency_vector, domains)` — radar chart năng lực 6 chiều bằng Plotly
- `render_score_bar(scores)` — bar chart so sánh điểm theo domain

### `ui/components/shared.py` — Widget dùng chung
- Các hàm render tái sử dụng: info card, warning badge, loading spinner, kết quả câu hỏi

### `ui/pages/assessment.py` — Trang đánh giá
- Hiển thị bộ 10 câu hỏi từ `test_generator`
- Nhận câu trả lời người dùng và gửi sang `grader.py`
- **Trạng thái: cần hoàn thiện**

### `ui/pages/interview.py` — Trang phỏng vấn
- Mô phỏng buổi phỏng vấn tuần tự với câu hỏi từ `recommender`
- Hiển thị phản hồi AI sau mỗi câu trả lời
- **Trạng thái: cần hoàn thiện**

### `ui/pages/dashboard.py` — Trang tổng quan
- Hiển thị radar chart năng lực hiện tại
- Liệt kê lịch sử trả lời và điểm từng domain
- **Trạng thái: cần hoàn thiện**

---

### `data/mock/mockdata.json` — Ngân hàng câu hỏi
- **1,700+ câu hỏi** đã kiểm duyệt bởi chuyên gia, bằng tiếng Việt
- Cấu trúc mỗi câu: `question_id`, `question_text`, `roles`, `difficulty_label`, `difficulty_score` (1–10), `question_type` (THEORY/CODING/CASE_STUDY), `skill_tags`, `answers.detailed`, `answers.evaluation_points`, `metadata`
- Phân loại role: **DA** (SQL, Pandas, Statistics, Viz) · **DE** (Big Data, Cloud, Kafka, Airflow) · **DS** (ML, Deep Learning, NLP, Time Series)

### `data/schemas/question_bank.schema.json`
- JSON Schema định nghĩa contract cho từng câu hỏi
- Bắt buộc: `question_id`, `question_text`, `roles.primary`, `difficulty_label`, `answers.detailed`

### `data/schemas/user_profile.schema.json`
- JSON Schema định nghĩa hồ sơ người dùng
- Bắt buộc: `user_id`, `role`, `skill_scores` (dict mapping skill → điểm 0–10)

### `data/vector_store/`
- Thư mục lưu ChromaDB database cho tính năng RAG
- **Hiện tại trống** — chờ AI Lead tích hợp embedding pipeline

---

### `utils/logger.py` — Hệ thống log
- Cấu hình Loguru: output ra console + file `logs/app.log` với rotation 10 MB
- Export `logger` để import dùng trong toàn dự án: `from utils.logger import logger`

### `utils/helpers.py` — Hàm tiện ích
- Hàm xử lý chuỗi, định dạng thời gian, parse kết quả JSON từ LLM response

---

##  Luồng dữ liệu

```
Người dùng chọn role (onboarding)
        │
        ▼
session_manager.init_session_state()
        │
        ▼
test_generator.generate_entry_test()  ←── data_loader.load_question_bank()
        │                                         │
        │                              schema_validator.validate_question()
        ▼
Người dùng trả lời câu hỏi (ui/pages/assessment)
        │
        ▼
grader.grade_answer()  ──────────────────────────── Google Gemini API
        │
        ▼
competency_engine.update_competency()  →  vector năng lực mới
        │
        ▼
recommender.recommend_questions()  →  câu hỏi tiếp theo
        │
        ▼
dashboard.py  →  render radar chart + lịch sử
```

---

