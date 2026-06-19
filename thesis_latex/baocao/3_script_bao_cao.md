# Script Báo Cáo (lời thoại) — InternHub

> Lời thoại theo từng slide, gán cho người trình bày. Đọc tự nhiên, không học thuộc máy móc. Thời lượng mục tiêu ~20 phút.

---

## [Hải Đăng] Slide 1 — Bìa (20 giây)
"Kính chào thầy cô trong hội đồng. Nhóm em gồm bốn thành viên, thực hiện khóa luận *Hệ thống phân loại và gợi ý phỏng vấn IT dựa trên Knowledge Tracing*, dưới sự hướng dẫn của thầy Nguyễn Văn Kiệt. Em là Hải Đăng, sẽ trình bày phần mở đầu."

## [Hải Đăng] Slide 2 — Đặt vấn đề (50 giây)
"Thị trường tuyển dụng IT hiện rất cạnh tranh. Theo khảo sát TopDev 2024, hơn 70% ứng viên thừa nhận chưa chuẩn bị đủ kỹ năng trước phỏng vấn. Các nền tảng luyện tập phổ biến như LeetCode hay HackerRank tập trung vào thuật toán, thiếu nội dung cho ba vai trò dữ liệu là Data Analyst, Data Scientist và Data Engineer. Nhóm em xác định hai hạn chế cốt lõi: thứ nhất, hệ thống cấp câu hỏi tĩnh, không cá nhân hóa theo năng lực; thứ hai, không theo dõi được quỹ đạo kiến thức của người học theo thời gian."

## [Hải Đăng] Slide 3 — Mục tiêu (50 giây)
"Từ đó nhóm đặt bốn mục tiêu. Một, xây dựng bộ dữ liệu Knowledge Tracing cho bài toán phỏng vấn IT. Hai, huấn luyện và so sánh ba họ mô hình KT là BKT, DKT và SAKT, kèm biến thể dùng quality label. Ba, xây engine gợi ý dựa trên KT, kết hợp dự đoán KT 70% với EMA 30%, và bài kiểm tra thích nghi hai giai đoạn. Bốn, tích hợp tất cả thành một ứng dụng web hoàn chỉnh với chấm điểm tự động bằng mô hình ngôn ngữ lớn."

## [Hải Đăng] Slide 4 — Phạm vi (40 giây)
"Phạm vi gồm ba vai trò DA, DS, DE, với 17 Knowledge Component chia theo vai trò, và năm loại câu hỏi từ trắc nghiệm đến tự luận và coding. Dữ liệu huấn luyện KT là dữ liệu mô phỏng, gồm 1.000 người dùng ảo và khoảng 40.000 tương tác. Nhóm không sử dụng dữ liệu người dùng thật và không triển khai ở quy mô production trong phạm vi khóa luận này."

## [Hải Đăng] Slide 5 — Cơ sở lý thuyết KT (60 giây)
"Về lý thuyết, Knowledge Tracing là bài toán dự đoán xác suất trả lời đúng câu kế tiếp dựa trên lịch sử tương tác. Nhóm dùng ba mô hình. BKT mô hình mỗi KC bằng một chuỗi Markov ẩn hai trạng thái với bốn tham số, ưu điểm là dễ diễn giải. DKT thay bằng mạng LSTM để học biểu diễn ẩn phong phú hơn. SAKT dùng cơ chế self-attention, cho phép song song hóa và diễn giải được trọng số attention."

## [Hải Đăng] Slide 6 — IRT & cập nhật realtime (50 giây)
"Để mô phỏng hành vi người dùng, nhóm dùng Item Response Theory: xác suất trả lời đúng phụ thuộc năng lực và độ khó câu hỏi. Để cập nhật năng lực thời gian thực, nhóm dùng EMA chạy ngay từ câu đầu, rồi kết hợp với dự đoán KT theo tỷ lệ 70-30 khi đã có ít nhất 3 tương tác. Cách này xử lý được cold-start và giữ ổn định. Tiếp theo, bạn Gia Khiêm trình bày phần dữ liệu."

---

## [Gia Khiêm] Slide 7 — Pipeline dữ liệu (45 giây)
"Em là Gia Khiêm. Do thiếu dữ liệu thật, nhóm xây pipeline ba bước. Bước một xây question bank. Bước hai sinh 1.000 người dùng ảo với vector năng lực phân phối Gaussian có tương quan, phản ánh việc các kỹ năng liên quan thường đi cùng nhau. Bước ba mô phỏng chuỗi tương tác bằng IRT kết hợp mô hình chấm điểm theo bậc."

## [Gia Khiêm] Slide 8 — Question bank & QC (70 giây)
"Question bank được xây bằng quy trình lai. Nhóm thu thập câu hỏi từ các kho công khai như Obenner cho Data Engineer, LearningZone cho SQL, và các bộ DS/DA cộng đồng, đều có trích dẫn nguồn. Sau đó dùng pipeline đa mô hình LLM để sinh thêm câu hỏi cho các KC còn thiếu, kèm đáp án tham chiếu và các ý chính cần có. Mỗi câu đi qua bốn bước kiểm định: kiểm tra schema, đối chiếu nội dung bằng RAG để bắt câu sai, review thủ công trên mẫu, và chuẩn hóa nhãn kỹ năng về 17 KC qua bảng tra 82 ánh xạ. Snapshot dùng để train KT gồm 1.578 câu; bản triển khai trên ứng dụng đã mở rộng lên 2.122 câu."

## [Gia Khiêm] Slide 9 — Thống kê dữ liệu (40 giây)
"Bộ dữ liệu mô phỏng gồm 1.000 người dùng chia đều ba vai trò, khoảng 40.000 tương tác, chia train-validation-test theo tỷ lệ 700-150-150 ở mức người dùng để tránh rò rỉ dữ liệu. Tỷ lệ pass khoảng 82,5%, nên ở phần đánh giá nhóm ưu tiên PR-AUC thay vì chỉ dùng accuracy."

## [Gia Khiêm] Slide 10 — EDA (55 giây)
"Phân tích khám phá xác nhận dữ liệu hợp lý. Phân bố câu hỏi đều theo ba vai trò, câu mức trung bình chiếm đa số. Điểm chất lượng phân bố nhất quán với thiết kế IRT. Learning curve tăng đơn điệu theo thứ tự câu hỏi, cho thấy mô phỏng có động lực học đúng. Ngoài ra, tương quan giữa tự đánh giá và năng lực thật khoảng 0,72, và nhóm beginner có xu hướng tự tin thái quá. Tiếp theo, bạn Sỹ Huỳnh trình bày phần mô hình."

---

## [Sỹ Huỳnh] Slide 11 — Thiết kế thực nghiệm (45 giây)
"Em là Sỹ Huỳnh. Thực nghiệm chạy trên Kaggle với GPU Tesla T4, PyTorch 2.6, cố định seed 42. Nhóm thiết kế ablation study với 8 cấu hình, từ baseline đa số, BKT, các biến thể DKT và SAKT, đến phiên bản binary, quality và deep. Độ đo gồm ROC-AUC, PR-AUC, RMSE và accuracy; do dữ liệu mất cân bằng, nhóm dùng PR-AUC Gain làm chỉ số so sánh chính."

## [Sỹ Huỳnh] Slide 12 — Kết quả (50 giây)
"Bảng kết quả trên tập test cho thấy mọi mô hình KT đều vượt baseline: ROC-AUC tăng từ 0,5 lên khoảng 0,67–0,68. DKT-Quality đạt PR-AUC cao nhất là 0,907 và RMSE thấp nhất là 0,355, với thời gian huấn luyện chỉ khoảng 21 giây. SAKT-Binary nhanh nhất, chỉ 11 giây."

## [Sỹ Huỳnh] Slide 13 — Phân tích (70 giây)
"Có bốn nhận xét chính. Một, KT thực sự có giá trị: tất cả mô hình vượt baseline rõ rệt. Hai, quality label, tức dùng điểm liên tục thay nhãn nhị phân, cải thiện DKT về cả RMSE và PR-AUC. Ba, điểm cần lưu ý: BKT đạt ROC-AUC cao nhất, nhưng đây là do simulation bias — dữ liệu sinh bằng IRT có cùng dạng tham số với BKT, tạo lợi thế không công bằng, nên không phản ánh hiệu năng trên dữ liệu thật. Bốn, mô hình sâu hơn không cải thiện đáng kể, vì nút thắt là kích thước dữ liệu chứ không phải kiến trúc."

## [Sỹ Huỳnh] Slide 14 — Chọn mô hình (40 giây)
"Vì vậy nhóm chọn DKT-Quality làm mô hình chính cho ứng dụng. Lý do quan trọng là output của DKT có dạng cho phép dự đoán cả 17 KC trong một lần forward, rất phù hợp cho gợi ý thời gian thực; đồng thời nó có PR-AUC và RMSE tốt nhất nhóm neural và huấn luyện nhanh. Tiếp theo, bạn Ngọc Nam trình bày hệ thống và demo."

---

## [Ngọc Nam] Slide 15 — Kiến trúc (55 giây)
"Em là Ngọc Nam. Hệ thống gồm ba tầng. Tầng dữ liệu chứa question bank, schema và taxonomy 17 KC. Tầng KT và scoring gồm bộ dự đoán KT, recommender và competency engine. Tầng phục vụ gồm FastAPI với 9 endpoint, Streamlit làm host và giao diện React. Một điểm kỹ thuật: backend dùng snake_case còn frontend dùng camelCase, nên nhóm chuẩn hóa tập trung tại ranh giới giữa hai phía."

## [Ngọc Nam] Slide 16 — Gợi ý & MST (55 giây)
"Engine gợi ý xếp hạng câu hỏi theo công thức 65% ưu tiên KC yếu, 30% độ phù hợp độ khó, 5% độ phủ, theo chiến lược chọn câu hơi khó hơn năng lực hiện tại. Bài đánh giá dùng kiểm tra thích nghi hai giai đoạn: giai đoạn một định vị năng lực và phân nhánh yếu, trung bình hoặc mạnh; giai đoạn hai chọn câu chuyên sâu, ưu tiên các KC yếu. Vector năng lực được cập nhật theo từng trục KC."

## [Ngọc Nam] Slide 17 — Chấm điểm (40 giây)
"Về chấm điểm, câu trắc nghiệm và đúng-sai được chấm tất định, không cần gọi LLM. Câu tự luận và coding được chấm bằng Gemini theo rubric và các ý chính. Khi LLM gặp lỗi, hệ thống tự động lui về bộ chấm cục bộ, đánh giá dựa trên mức độ phủ từ khóa của các ý chính. Đây là cơ chế dự phòng, không phải lỗi."

## [Ngọc Nam] Slide 18 — DEMO (120–150 giây)
"Bây giờ em demo nhanh hệ thống. (Chọn vai trò Data Scientist.) Em vào phiên Diagnostic và làm vài câu — một câu trắc nghiệm được chấm tất định ngay, và một câu tự luận được Gemini chấm. (Hoàn tất phiên.) Đây là kết quả: hệ thống phân loại routing và cập nhật vector năng lực. Sang Dashboard, ta thấy radar năng lực hiện tại so với mục tiêu cùng bảng các kỹ năng còn yếu. Sang màn KT Model, đây là pipeline EMA, DKT rồi Blend chạy trên chính câu trả lời vừa rồi; xin lưu ý các con số ở radar này khớp hoàn toàn với Dashboard, đảm bảo tính nhất quán."
*(Nếu lỗi mạng/Gemini: chuyển sang video dự phòng và giải thích cơ chế fallback.)*

## [Ngọc Nam] Slide 19 — Đóng góp & hạn chế (40 giây)
"Tóm lại, khóa luận có bốn đóng góp: pipeline xây dữ liệu phỏng vấn IT tổng hợp, biến thể DKT-Quality, cơ chế blend KT-EMA cho cập nhật realtime, và hệ thống end-to-end chạy được. Hạn chế lớn nhất là simulation bias và thiếu dữ liệu thật; ngoài ra còn sequence length bị cap, mất cân bằng lớp, và nhóm advanced ít."

## [Ngọc Nam] Slide 20 — Kết luận (35 giây)
"Kết quả cho thấy KT mang lại giá trị thực cho bài toán này, DKT-Quality phù hợp cho gợi ý thời gian thực, và cơ chế blend KT-EMA xử lý được cold-start. Hướng phát triển tiếp theo là thu thập dữ liệu thật để kiểm chứng và A/B test, thử các mô hình Transformer như AKT, SAINT, mở rộng question bank, và triển khai production. Nhóm em xin cảm ơn thầy cô và sẵn sàng nhận câu hỏi."

---

## Ghi chú khi nói
- Mỗi người mở đầu phần của mình bằng một câu chuyển tiếp ngắn (đã có trong script).
- Nói số liệu chậm và rõ; chỉ tay vào bảng/biểu đồ.
- Phần demo là trọng tâm — luyện trước ít nhất 2 lần, canh đúng 2 phút.
- Khi bị hỏi mà chưa chắc, trả lời phần mình nắm rõ trước, rồi mời thành viên phụ trách bổ sung.
