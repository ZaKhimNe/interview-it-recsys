# Kịch Bản Báo Cáo Khóa Luận — InternHub (KT Recommendation System)

## Thông tin chung
- **Đề tài:** Hệ thống phân loại và gợi ý phỏng vấn IT dựa trên Knowledge Tracing.
- **GVHD:** TS. Nguyễn Văn Kiệt.
- **Nhóm:** Mai Dương Hải Đăng (24520253), Tạ Gia Khiêm (24520805), Nguyễn Sỹ Huỳnh (24520716), Nguyễn Ngọc Nam (24521114).
- **Thời lượng đề xuất:** 20–22 phút trình bày + 8–10 phút phản biện.
- **Số slide:** 20 slide (kể cả bìa và slide kết).

## Phân công trình bày
| Phần | Người trình bày | Slide | Thời lượng |
|------|-----------------|-------|------------|
| Mở đầu, vấn đề, mục tiêu, phạm vi | Hải Đăng | 1–4 | 4 phút |
| Cơ sở lý thuyết (KT, IRT, EMA/blend) | Hải Đăng | 5–6 | 2 phút |
| Dataset: thu thập, QC, mô phỏng, EDA | Gia Khiêm | 7–10 | 5 phút |
| Mô hình & kết quả thực nghiệm | Sỹ Huỳnh | 11–14 | 5 phút |
| Hệ thống & Demo web | Ngọc Nam | 15–18 | 5 phút |
| Kết luận & hướng phát triển | Ngọc Nam | 19–20 | 1 phút |
| Phản biện (Q&A) | Cả nhóm | — | 8–10 phút |

*(Phân công có thể đổi; mỗi người nên nắm được toàn bộ để trả lời phản biện chéo.)*

## Mạch trình bày (đầu → dataset → model → web demo)
1. **Mở đầu (Slide 1–4):** giới thiệu đề tài → nêu 2 vấn đề (thiếu cá nhân hóa, không theo dõi quỹ đạo kiến thức) → 4 mục tiêu → phạm vi (3 vai trò DA/DS/DE, 17 KC, 5 loại câu hỏi).
2. **Lý thuyết (Slide 5–6):** KT là gì, 3 họ mô hình BKT/DKT/SAKT, IRT cho mô phỏng, công thức blend KT 70% + EMA 30%.
3. **Dataset (Slide 7–10):** pipeline xây question bank (scrape + LLM + QC) → mô phỏng người dùng bằng IRT → thống kê dữ liệu → 2–3 biểu đồ EDA chính.
4. **Model (Slide 11–14):** thiết kế thực nghiệm (8 cấu hình ablation) → bảng kết quả → phân tích (quality label, simulation bias, deep model bottleneck) → chọn DKT‑Quality cho production.
5. **Hệ thống + Demo (Slide 15–18):** kiến trúc 3 tầng → cơ chế cập nhật năng lực realtime + recommender ZPD + MST 2 giai đoạn → grader → **demo trực tiếp web**.
6. **Kết luận (Slide 19–20):** tóm tắt đóng góp + hạn chế + hướng phát triển.

## Kịch bản DEMO web (mục quan trọng nhất — chuẩn bị kỹ)
Thứ tự thao tác đề xuất khi demo (khoảng 2–3 phút):
1. Mở app (`streamlit run app.py`) — đã chạy sẵn trước khi lên, KHÔNG khởi động lúc báo cáo.
2. Onboarding: chọn vai trò (ví dụ Data Scientist).
3. Vào **Interview → Diagnostic (MST)**: làm 2–3 câu (1 trắc nghiệm chấm tất định, 1 câu tự luận để cho thấy Gemini chấm).
4. Hoàn tất phiên → màn kết quả: cho thấy routing (WEAK/MID/STRONG) + vector cập nhật.
5. Mở **Dashboard**: radar năng lực current vs target + Top Gaps.
6. Mở **KT Model**: chỉ ra pipeline EMA→DKT→Blend và nhấn mạnh **con số radar khớp với Dashboard** (tính đồng bộ).
7. (Tùy chọn) mở Roadmap/History.

**Phương án dự phòng demo:** quay sẵn 1 video screen-record 2 phút + bộ screenshot. Nếu mạng lỗi (Gemini), nhấn mạnh hệ thống tự fallback local rubric — đây là tính năng, không phải lỗi.

## Checklist chuẩn bị
- [ ] Laptop đã cài đủ môi trường, app chạy được offline (trừ Gemini cần mạng).
- [ ] API key Gemini còn hạn; test trước 1 câu chấm tự luận.
- [ ] Video demo + screenshot dự phòng.
- [ ] File slide (PDF) backup trong USB + email.
- [ ] Đồng hồ bấm giờ, phân vai chuyển slide rõ ràng.
- [ ] Mỗi thành viên thuộc phần của mình + đọc trước mục Phản biện.

## Câu hỏi phản biện dự kiến & hướng trả lời
1. **Vì sao không dùng dữ liệu thật?** → Thiếu dữ liệu tương tác công khai cho phỏng vấn IT; dùng mô phỏng IRT có learning dynamics hợp lý. Đã nêu rõ là hạn chế và hướng thu thập dữ liệu thật.
2. **Vì sao BKT cao nhất mà lại chọn DKT‑Quality?** → BKT cao do *simulation bias* (dữ liệu sinh bằng IRT cùng dạng tham số với BKT), không phản ánh dữ liệu thật. DKT‑Quality tổng quát hơn, output dự đoán cả 17 KC trong 1 lần forward (phù hợp realtime), PR‑AUC và RMSE tốt nhất nhóm neural.
3. **Quality label là gì, vì sao tốt hơn?** → Điểm liên tục (0, 0.5, 1) thay nhãn nhị phân; cung cấp tín hiệu gradient phong phú hơn → RMSE giảm ~0.02, PR‑AUC tăng nhẹ.
4. **Vì sao blend 70/30?** → KT nắm động lực chuỗi nên cho trọng số trội; EMA giữ 30% để ổn định, chống dao động và xử lý cold‑start (chỉ bật KT sau ≥3 tương tác).
5. **Độ tin cậy của chấm điểm LLM?** → Câu khách quan chấm tất định, không cần LLM. Câu tự luận chấm bằng Gemini theo rubric + evaluation_points; có fallback local rubric khi LLM lỗi. Hạn chế: chưa calibrate với human annotation (đã nêu hướng tương lai).
6. **Sequence length đều bằng 40 — vấn đề gì?** → Pool câu mỗi role sau lọc chỉ ~40 câu nên bị cap; là hạn chế đã ghi nhận, giải pháp là mở rộng question bank (đã lên 2.122 câu).
7. **Hệ thống có scale được không?** → Bản hiện tại là demo local (FastAPI chạy thread nền của Streamlit). Hướng production: tách microservice, thêm DB, auth, autoscaling (đã nêu).
