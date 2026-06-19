# Nội Dung Slide — InternHub (KT Recommendation System)

> 20 slide. Mỗi slide ghi: tiêu đề, nội dung bullet, gợi ý hình/bảng. Giữ tối đa ~6 dòng/slide.

---

## Slide 1 — Bìa
- **HỆ THỐNG PHÂN LOẠI VÀ GỢI Ý PHỎNG VẤN IT DỰA TRÊN KNOWLEDGE TRACING**
- InternHub KT Recommendation System
- Nhóm: Mai Dương Hải Đăng (24520253), Tạ Gia Khiêm (24520805), Nguyễn Sỹ Huỳnh (24520716), Nguyễn Ngọc Nam (24521114)
- GVHD: TS. Nguyễn Văn Kiệt — Trường ĐH Công nghệ Thông tin, ĐHQG-HCM, 2026
- *Hình: logo UIT.*

---

## Slide 2 — Đặt vấn đề
- Thị trường tuyển dụng IT cạnh tranh; >70% ứng viên IT chưa chuẩn bị đủ kỹ năng (TopDev 2024).
- Nền tảng hiện có (LeetCode, HackerRank, Pramp) tập trung thuật toán, thiếu nội dung cho DA/DS/DE.
- **Hai hạn chế cốt lõi:**
  1. Thiếu cá nhân hóa theo năng lực (câu hỏi tĩnh).
  2. Không theo dõi quỹ đạo kiến thức của người học.
- *Hình: so sánh nền tảng hiện có vs nhu cầu.*

---

## Slide 3 — Mục tiêu nghiên cứu
1. Xây dựng bộ dữ liệu KT cho bài toán phỏng vấn IT (question bank + mô phỏng).
2. Huấn luyện & so sánh 3 họ mô hình KT: BKT, DKT, SAKT (+ biến thể quality label).
3. Xây engine gợi ý dựa trên KT (blend KT 70% + EMA 30%, CAT 2 giai đoạn).
4. Tích hợp thành ứng dụng web hoàn chỉnh (React + FastAPI + Streamlit, chấm điểm LLM).

---

## Slide 4 — Phạm vi
- **3 vai trò:** Data Analyst, Data Scientist, Data Engineer.
- **17 Knowledge Components:** DA 5, DS 7, DE 5.
- **5 loại câu hỏi:** MC_SINGLE, TRUE_FALSE, FILL_BLANK, THEORY, CODING.
- **Dữ liệu KT:** 1.000 user mô phỏng, ~40.000 tương tác.
- **Ngoài phạm vi:** dữ liệu người dùng thật, A/B testing, deploy production scale.

---

## Slide 5 — Cơ sở lý thuyết: Knowledge Tracing
- KT: dự đoán xác suất trả lời đúng câu kế tiếp từ lịch sử tương tác.
- **BKT:** HMM 2 trạng thái/KC, 4 tham số (L0, T, S, G) — dễ diễn giải.
- **DKT:** LSTM học biểu diễn ẩn của trạng thái kiến thức.
- **SAKT:** self-attention, song song hóa, diễn giải attention.
- *Hình: sơ đồ 3 mô hình cạnh nhau.*

---

## Slide 6 — IRT & Cơ chế cập nhật realtime
- **IRT (3PL):** dùng để mô phỏng hành vi người dùng: P(đúng) phụ thuộc năng lực θ và độ khó b.
- **EMA:** θ_EMA = 0.35·s + 0.65·θ_EMA (chạy ngay từ câu đầu).
- **Blend KT–EMA:** θ = 0.7·θ_KT + 0.3·θ_EMA, kích hoạt khi ≥3 tương tác.
- Giải quyết cold-start + giữ ổn định. Hằng số đồng nhất backend/frontend.

---

## Slide 7 — Pipeline xây dựng dữ liệu (tổng quan)
- **Bước 1 — Question bank:** scrape nguồn công khai + sinh bằng LLM + QC.
- **Bước 2 — Virtual users:** 1.000 user, skill vector Gaussian có tương quan.
- **Bước 3 — Mô phỏng tương tác:** IRT + power-based graded response + cập nhật skill.
- *Hình: sơ đồ pipeline 3 bước.*

---

## Slide 8 — Xây dựng & kiểm định Question Bank
- Thu thập: Obenner (DE), LearningZone (SQL), Youssef/Alexey (DS/DA) — có trích dẫn.
- Sinh LLM đa mô hình: Gemini sinh câu, mô hình mạnh tạo đáp án + evaluation_points, judge chấm chất lượng.
- QC: kiểm tra schema → QC bằng RAG → human review → chuẩn hóa skill_groups (82 ánh xạ → 17 KC).
- **Kết quả:** snapshot train KT = 1.578 câu; bản triển khai = 2.122 câu.

---

## Slide 9 — Thống kê bộ dữ liệu mô phỏng
| Thuộc tính | Giá trị |
|---|---|
| Người dùng | 1.000 (DA 334 / DS 333 / DE 333) |
| Câu hỏi (snapshot KT) | 1.578 |
| KC | 17 |
| Tương tác | ~40.140 (TB 40,1/user) |
| Split | 700 / 150 / 150 (train/val/test) |
| Pass rate (Q≥1) | 82,5% |
- Tham số: noise 0.30, η=0.08, γ=0.002, seed 42.

---

## Slide 10 — EDA: phát hiện chính
- Phân bố câu hỏi đều theo 3 role; MEDIUM chiếm đa số.
- Quality score: Q=2 ~62%, Q=1 ~20%, Q=0 ~18% (nhất quán IRT).
- Learning curve tăng đơn điệu theo thứ tự câu → mô phỏng có động lực học hợp lý.
- Confidence bias: r(self-rating, skill) ≈ 0.72; beginner overconfident.
- *Hình: 2 biểu đồ — quality distribution + learning curve.*

---

## Slide 11 — Thiết kế thực nghiệm
- Môi trường: Kaggle, GPU Tesla T4, PyTorch 2.6, seed 42.
- **8 cấu hình ablation:** Baseline, BKT, DKT-Binary, DKT-Quality★, SAKT-Binary, SAKT-Quality★, DKT-Deep, SAKT-Deep.
- Độ đo: ROC-AUC, PR-AUC, PR-AUC Gain, RMSE, Accuracy.
- Lưu ý: class imbalance 82,5% → ưu tiên PR-AUC Gain.

---

## Slide 12 — Kết quả ablation (tập test)
| Model | ROC-AUC | PR-AUC | RMSE | Time(s) |
|---|---|---|---|---|
| Baseline | 0.500 | 0.820 | 0.384 | 0 |
| BKT | **0.677** | 0.905 | 0.374 | 61.9 |
| DKT-Binary | 0.666 | 0.905 | 0.375 | 30.8 |
| **DKT-Quality★** | 0.672 | **0.907** | **0.355** | 20.9 |
| SAKT-Binary | 0.668 | 0.903 | 0.373 | **11.3** |
| DKT-Deep | 0.669 | 0.906 | 0.375 | 116.4 |
- *Hình: biểu đồ cột ROC-AUC & PR-AUC.*

---

## Slide 13 — Phân tích kết quả
- Mọi mô hình KT vượt baseline (ROC-AUC ≈0.68 vs 0.50; PR-AUC Gain ≈0.085).
- **Quality label** cải thiện DKT: RMSE thấp nhất, PR-AUC cao nhất nhóm neural.
- **BKT cao nhất do simulation bias** (dữ liệu IRT cùng dạng với BKT) — không phản ánh dữ liệu thật.
- **Deep model chưa hiệu quả:** bottleneck là kích thước dữ liệu, không phải kiến trúc.

---

## Slide 14 — Chọn mô hình cho production
- **DKT-Quality★** làm mô hình chính:
  - Output (B, T, 17) → dự đoán cả 17 KC trong 1 forward (phù hợp realtime).
  - PR-AUC & RMSE tốt nhất nhóm neural, train nhanh (~21s).
- SAKT-Binary cho online update nhanh (11s) khi cần.
- *Hình: per-KC AUC hoặc position AUC.*

---

## Slide 15 — Kiến trúc hệ thống (3 tầng)
- **Tầng dữ liệu:** question bank + schema + taxonomy 17 KC.
- **Tầng KT/scoring:** kt_predictor (DKT-Quality) + recommender + competency_engine.
- **Tầng phục vụ:** FastAPI (9 endpoint) + Streamlit (host iframe) + React SPA.
- Chuẩn hóa snake_case ↔ camelCase tại boundary.
- *Hình: sơ đồ kiến trúc 3 tầng.*

---

## Slide 16 — Engine gợi ý & MST
- **Recommender (ZPD):** score = 0.65·weakness + 0.30·diff_fit + 0.05·coverage.
- Ngưỡng KC yếu/mạnh: 0.40 / 0.70.
- **MST 2 giai đoạn:** Stage 1 định vị → routing WEAK/MID/STRONG → Stage 2 thích nghi (ưu tiên KC yếu).
- Cập nhật vector theo từng trục KC; điểm cuối dùng pipeline KT-EMA chung.
- *Hình: sơ đồ luồng MST.*

---

## Slide 17 — Hệ thống chấm điểm
- Câu khách quan (MC/TF/Fill): chấm **tất định**, không cần LLM.
- Câu tự luận/coding: **Gemini 3.5 Flash** chấm theo rubric + evaluation_points.
- Fallback **local rubric** khi LLM lỗi: eval_point "đạt" khi ≥50% từ khóa xuất hiện.
- Lỗi LLM trả kèm `gemini_error` để chẩn đoán.

---

## Slide 18 — DEMO WEB (trình bày trực tiếp)
- Onboarding chọn vai trò → Diagnostic (MST) → chấm điểm → cập nhật vector.
- Dashboard: radar current vs target + Top Gaps.
- KT Model: pipeline EMA→DKT→Blend, **radar đồng bộ với Dashboard**.
- *(Có video + screenshot dự phòng.)*

---

## Slide 19 — Đóng góp & Hạn chế
- **Đóng góp:** (1) pipeline dữ liệu phỏng vấn IT tổng hợp; (2) biến thể DKT-Quality; (3) cơ chế blend KT-EMA cho realtime; (4) hệ thống end-to-end.
- **Hạn chế:** simulation bias (nặng nhất), thiếu dữ liệu thật, sequence length cap=40, class imbalance, advanced thấp 5,9%.

---

## Slide 20 — Kết luận & Hướng phát triển
- KT mang lại giá trị thực; DKT-Quality phù hợp realtime; blend KT-EMA xử lý cold-start.
- **Hướng phát triển:** thu thập dữ liệu thật + A/B test; forgetting curve; AKT/SAINT; mở rộng question bank; fine-tune grader; deploy production.
- **Cảm ơn — Q&A.**
