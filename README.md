# 🎯 InternHub — AI Tech Interview Prep

> Hệ thống đánh giá năng lực và luyện phỏng vấn IT, cá nhân hoá lộ trình ôn tập bằng **Knowledge Tracing** và chấm điểm tự động bằng **LLM**.

InternHub đánh giá năng lực ứng viên theo 3 vai trò dữ liệu (Data Analyst / Data Engineer / Data Scientist), đưa ra một bài kiểm tra thích ứng (adaptive), dựng **vector năng lực** theo từng kỹ năng và đề xuất câu hỏi tiếp theo dựa trên mức độ thành thạo ước lượng được.

---

## ✨ Tính năng chính

- **Đánh giá thích ứng (Multi-Stage Testing)** — bài test 2 giai đoạn: định vị trình độ → chọn câu hỏi tiếp theo theo điểm mạnh/yếu.
- **Vector năng lực theo từng trục kỹ năng** — radar chart so sánh trình độ hiện tại với mục tiêu của vai trò (lấy từ JD requirements).
- **Knowledge Tracing** — 3 mô hình (BKT, DKT, SAKT) ước lượng mức thành thạo từng Knowledge Component theo chuỗi tương tác.
- **Chấm điểm tự động** — câu tự luận/code chấm bằng Gemini, có cơ chế dự phòng bằng rubric cục bộ; câu trắc nghiệm chấm tức thời phía client.
- **Lộ trình & gợi ý câu hỏi** — đề xuất ôn tập ưu tiên các KC yếu, hoặc thử thách KC mạnh.
- **7 loại câu hỏi** — `THEORY`, `CODING`, `PRACTICE`, `MC_SINGLE`, `TRUE_FALSE`, `FILL_BLANK`, `CODING_EXERCISE`.
- **Ngân hàng ~2122 câu hỏi** song ngữ Việt–Anh, gắn tag kỹ năng chi tiết.

---

## 🧰 Công nghệ

| Lớp | Công nghệ |
|-----|-----------|
| Backend / Serving | Python, FastAPI (uvicorn), Streamlit (shell) |
| Frontend | React 18 + Babel standalone (in-browser, **không bundler**) |
| AI / Grading | Google Gemini (`google-genai`) |
| Knowledge Tracing | PyTorch (DKT/SAKT), NumPy/SciPy (BKT) |
| Data / Validation | pandas, jsonschema, pydantic |

---

## 🚀 Cài đặt & chạy

```bash
# 1. Clone
git clone https://github.com/ZaKhimNe/interview-it-recsys.git
cd interview-it-recsys

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Cấu hình môi trường — tạo file .env ở thư mục gốc:
#    GOOGLE_API_KEY=<your_gemini_api_key>
#    API_PORT=8000            (tuỳ chọn)
#    APP_DEBUG=true           (tuỳ chọn)

# 5. Chạy app
streamlit run app.py
```

Sau khi chạy, mở trình duyệt tại địa chỉ Streamlit in ra (mặc định `http://localhost:8501`). Giao diện React thực tế được phục vụ qua FastAPI ở `http://localhost:8000/ui` và nhúng vào Streamlit bằng iframe.

> **Lưu ý:** frontend không có bước build JS — các file `app/frontend/*.jsx` được Babel biên dịch ngay trên trình duyệt. Sửa file JSX chỉ cần rerun Streamlit là có hiệu lực.

---

## 🏗️ Kiến trúc

Hệ thống gồm **3 lớp**, giao tiếp qua 2 quy ước đặt tên (Python `snake_case` ↔ React `camelCase`):

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (app/frontend/*.jsx)  — React + Babel, no bundler  │
│  MST diagnostic · radar · roadmap · grading UI               │
└───────────────▲───────────────────────────┬─────────────────┘
        iframe  │  /ui (static)      fetch   │  /api/*
┌───────────────┴───────────────────────────▼─────────────────┐
│  Serving (app.py + src/api/serving.py)                        │
│  Streamlit shell + FastAPI background server (uvicorn)        │
└───────────────▲───────────────────────────┬─────────────────┘
                │                            │
┌───────────────┴────────────┐  ┌────────────▼─────────────────┐
│  Data (src/data, data/)     │  │  KT / Scoring (src/kt,       │
│  question bank + schemas    │  │  kt_models/) · grading        │
└─────────────────────────────┘  └──────────────────────────────┘
```

**Vì sao cần FastAPI?** Streamlit trả `Content-Type: text/plain` cho file `.html` (trình duyệt từ chối render), nên UI thật **không** do Streamlit phục vụ. `app.py` chạy một FastAPI server ở luồng nền (port `API_PORT`, mặc định 8000), mount thư mục `static/` tại `/ui` (uvicorn set đúng MIME type), rồi Streamlit chỉ nhúng iframe trỏ tới đó. Frontend gọi ngược lại `/api/*` để chấm điểm, lưu hồ sơ, finalize bài đánh giá.

### Luồng đánh giá thích ứng (MST)

`screens-diagnostic.jsx`: **Stage 1** (câu định vị) → quyết định routing (WEAK / MID / STRONG theo điểm trung bình) → **Stage 2** (câu thích ứng, ưu tiên nhóm kỹ năng yếu ở Stage 1) → cập nhật vector năng lực theo **từng trục**. Lần đánh giá đầu tiên ánh xạ trực tiếp `điểm × mục tiêu` cho mỗi trục; các lần sau cộng dồn delta. Trục nào không được test thì giữ nguyên.

### Knowledge Tracing

3 mô hình chuỗi tương tác được train offline qua pipeline notebook `01_eda → 02_feature_engineering → 03_train_models → 04_evaluation`, lưu trọng số ở `results/models/`:

| Mô hình | Loại | Ghi chú |
|---------|------|---------|
| **BKT** | Bayesian, 4 tham số / KC | L-BFGS-B trên log-likelihood |
| **DKT** | LSTM | mô hình mặc định khi serving (`dkt_quality`) |
| **SAKT** | Self-attention | causal mask |

Khi serving, `src/kt/kt_predictor.py` nạp mô hình tốt nhất, ước lượng mức thành thạo 0.05–0.99 cho từng KC. Pipeline cập nhật năng lực luôn chạy **EMA trước**, rồi trộn dự đoán KT khi đủ lịch sử (≥ 3 tương tác): **KT 70% + EMA 30%**.

### Knowledge Component (KC) taxonomy

17 KC trải trên 3 vai trò (DA: 5, DS: 7, DE: 5), định nghĩa ở `config.py:KC_BY_ROLE`. Câu hỏi gắn tag `skill_groups` ở mức chi tiết (vd `SQL_WINDOW_FUNCTION`), rồi `SKILL_GROUP_TO_KC` gộp về 17 KC chuẩn để chấm điểm / KT.

### Chấm điểm

`src/ai/grader.py`: câu tự luận/code chấm bằng Gemini (`config.LLM_MODEL_NAME`), có rubric cục bộ (`_local_grade`) làm dự phòng khi gọi LLM lỗi. Câu trắc nghiệm (MC / True-False / Fill-blank) chấm trực tiếp không cần LLM.

---

## 📁 Cấu trúc dự án

```
.
├── app.py                  # Entry point: Streamlit shell + FastAPI bridge
├── config.py               # Hằng số, paths, KC taxonomy, API keys
├── app/frontend/           # React JSX (no bundler) — state, screens, widgets, router
├── src/
│   ├── data/               # data_loader, question_manager, schema_validator
│   ├── api/                # serving (FastAPI), user_manager, helpers, logger
│   ├── ai/                 # grader (Gemini + rubric), prompts
│   └── kt/                 # competency_engine, kt_predictor, recommender, scoring
├── kt_models/              # BKT / DKT / SAKT (kiến trúc + train logic)
├── data/
│   ├── raw/question_bank/  # ngân hàng câu hỏi (~2122 câu)
│   ├── reference/          # văn bản tham chiếu cho 17 KC
│   └── schemas/            # JSON Schema: question bank, taxonomy, JD, user profile
├── notebooks/              # 01_eda → 04_evaluation (pipeline train KT)
├── results/                # model weights + plots + metrics
└── utils/data/             # script thu thập / sinh / QC / mô phỏng dữ liệu
```

---

## 📄 License

MIT License © 2026 InternHub
