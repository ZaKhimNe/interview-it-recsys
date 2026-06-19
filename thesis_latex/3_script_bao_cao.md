# Script Báo Cáo (lời thoại) — InternHub

> Lời thoại theo từng slide, gán cho người trình bày. Mỗi slide gồm: **Lời thoại** (đọc tự nhiên, không học thuộc) và **Số liệu để nắm** (dự phòng khi bị hỏi, không bắt buộc nói hết). Thời lượng mục tiêu ~22 phút + Q&A. Phần demo (slide 18) là trọng tâm.

---

## [Sỹ Huỳnh] Slide 1 — Bìa (20 giây)

**Lời thoại:**
"Kính chào thầy cô trong hội đồng. Nhóm em gồm bốn thành viên, thực hiện khóa luận *Hệ thống phân loại và gợi ý phỏng vấn IT dựa trên Knowledge Tracing*, dưới sự hướng dẫn của thầy Nguyễn Văn Kiệt. Em là Sỹ Huỳnh, trình bày phần mở đầu và cơ sở lý thuyết."

---

## [Sỹ Huỳnh] Slide 2 — Đặt vấn đề (55 giây)

**Lời thoại:**
"Thị trường tuyển dụng IT hiện rất cạnh tranh. Theo khảo sát TopDev 2024, hơn 70% ứng viên IT thừa nhận chưa chuẩn bị đủ kỹ năng trước phỏng vấn. Các nền tảng luyện tập phổ biến như LeetCode, HackerRank, Pramp tập trung vào lập trình thuật toán, gần như không có nội dung riêng cho ba vai trò ngành dữ liệu là Data Analyst, Data Scientist và Data Engineer.

Nhóm em xác định hai hạn chế cốt lõi. Thứ nhất, các hệ thống cấp câu hỏi tĩnh — cùng một bộ câu cho mọi người, không điều chỉnh theo năng lực, nên người giỏi phải làm lại câu quá dễ còn người mới thì gặp câu ngoài tầm. Thứ hai, chúng không theo dõi được quỹ đạo kiến thức của người học theo thời gian, tức là không biết người dùng đang mạnh hay yếu ở kỹ năng nào sau mỗi lần luyện."

**Số liệu để nắm:**
- Nguồn: TopDev Vietnam IT Market Report 2024.
- Khái niệm nền: *zone of proximal development* — câu hiệu quả nhất là câu hơi khó hơn năng lực hiện tại.

---

## [Sỹ Huỳnh] Slide 3 — Mục tiêu (55 giây)

**Lời thoại:**
"Từ hai hạn chế đó, nhóm đặt bốn mục tiêu. Một, xây dựng bộ dữ liệu Knowledge Tracing phù hợp cho bài toán phỏng vấn IT, gồm question bank và dữ liệu tương tác mô phỏng. Hai, huấn luyện và so sánh ba họ mô hình KT là BKT, DKT và SAKT, cùng biến thể dùng quality label thay cho nhãn đúng-sai. Ba, xây engine gợi ý dựa trên KT: kết hợp dự đoán KT 70% với EMA 30%, và bài kiểm tra thích nghi hai giai đoạn. Bốn, tích hợp toàn bộ thành ứng dụng web hoàn chỉnh, chấm điểm tự động bằng mô hình ngôn ngữ lớn có cơ chế dự phòng."

**Số liệu để nắm:**
- Bốn mục tiêu tương ứng bốn phần báo cáo: dữ liệu → mô hình → engine gợi ý → hệ thống.

---

## [Sỹ Huỳnh] Slide 4 — Phạm vi (45 giây)

**Lời thoại:**
"Phạm vi gồm ba vai trò DA, DS, DE, với tổng cộng 17 Knowledge Component — DA 5, DS 7, DE 5 — và năm loại câu hỏi: trắc nghiệm một đáp án, đúng-sai, điền chỗ trống, lý thuyết tự luận và coding. Dữ liệu huấn luyện KT là dữ liệu mô phỏng, gồm 1.000 người dùng ảo và khoảng 40.000 tương tác. Trong phạm vi khóa luận, nhóm chưa dùng dữ liệu người dùng thật, chưa làm A/B testing và chưa triển khai ở quy mô production — đây cũng là các hướng phát triển tiếp theo."

**Số liệu để nắm:**
- 17 KC: DA 5 / DS 7 / DE 5.
- 5 loại câu: MC_SINGLE, TRUE_FALSE, FILL_BLANK, THEORY, CODING.

---

## [Sỹ Huỳnh] Slide 5 — Cơ sở lý thuyết KT (65 giây)

**Lời thoại:**
"Knowledge Tracing là bài toán dự đoán xác suất người học trả lời đúng câu kế tiếp dựa trên lịch sử tương tác. Nhóm dùng ba mô hình.

BKT mô hình mỗi KC bằng một chuỗi Markov ẩn hai trạng thái — chưa thành thạo và đã thành thạo — với bốn tham số cho mỗi KC: xác suất thành thạo ban đầu, xác suất học được, xác suất nhầm và xác suất đoán trúng. Ưu điểm là dễ diễn giải.

DKT thay xác suất bằng mạng LSTM, học một biểu diễn ẩn phong phú hơn cho trạng thái kiến thức, và có thể nắm được quan hệ giữa nhiều KC.

SAKT thay LSTM bằng cơ chế self-attention: thay vì xử lý tuần tự, nó liên kết trực tiếp câu hiện tại với các câu liên quan trong quá khứ, cho phép song song hóa và diễn giải qua trọng số attention."

**Số liệu để nắm:**
- BKT 4 tham số/KC: P(L0), P(T), P(S), P(G); cập nhật theo Bayes.
- DKT: LSTM hidden=128, 1 lớp, dropout 0.2.
- SAKT: embedding=64, 4 attention heads, 1 lớp.

---

## [Sỹ Huỳnh] Slide 6 — IRT & cập nhật realtime (55 giây)

**Lời thoại:**
"Để mô phỏng hành vi người dùng, nhóm dùng Item Response Theory: xác suất trả lời đúng là hàm sigmoid của hiệu giữa năng lực người học và độ khó câu hỏi.

Để cập nhật năng lực thời gian thực, nhóm kết hợp hai cơ chế. EMA — trung bình trượt mũ — chạy ngay từ câu đầu tiên, ổn định và không cần lịch sử dài. Khi người dùng đã có ít nhất 3 tương tác, hệ thống blend dự đoán của mô hình KT với EMA theo tỷ lệ 70-30. KT giữ trọng số trội vì nắm được động lực chuỗi và quan hệ giữa các KC; EMA giữ 30% để ổn định, chống dao động khi gặp chuỗi nhiễu. Cách này xử lý được cold-start. Các hằng số này được giữ giống nhau giữa backend và frontend để con số hiển thị đồng bộ. Tiếp theo, bạn Hải Đăng trình bày phần dữ liệu."

**Số liệu để nắm:**
- IRT: P(đúng) = σ((θ − b) × 6).
- EMA: θ_EMA = 0.35·s + 0.65·θ_EMA (α = 0.35).
- Blend: θ = 0.7·θ_KT + 0.3·θ_EMA, kích hoạt khi lịch sử ≥ 3.
- Khoảng dự đoán KT giới hạn [0.05, 0.99].

---

## [Hải Đăng] Slide 7 — Pipeline dữ liệu (50 giây)

**Lời thoại:**
"Em là Hải Đăng. Do thiếu dữ liệu thật, nhóm xây pipeline mô phỏng ba bước. Bước một, xây question bank. Bước hai, sinh 1.000 người dùng ảo với vector năng lực theo phân phối Gaussian có tương quan giữa các KC liên quan — ví dụ với DA, SQL và Analytics có tương quan khoảng 0,55, với DS, Algorithm và Evaluation khoảng 0,70. Bước ba, mô phỏng chuỗi tương tác bằng IRT, kèm mô hình chấm điểm theo bậc và cập nhật năng lực sau mỗi câu: tăng khi đúng, giảm nhẹ khi sai."

**Số liệu để nắm:**
- Tham số mô phỏng: noise σ = 0.30, learning rate η = 0.08, forgetting γ = 0.002, seed 42.
- Graded response (power-based, α = 2.0): P(Q=2)=p^α, P(Q=0)=(1−p)^α.
- Cập nhật: θ += η(1−θ) khi đúng; θ −= γθ khi sai.

---

## [Hải Đăng] Slide 8 — Question bank & QC (70 giây)

**Lời thoại:**
"Question bank được xây bằng quy trình lai bốn giai đoạn. Thu thập: lấy câu hỏi từ các kho công khai như Obenner cho Data Engineer, LearningZone cho SQL, và các bộ DS/DA cộng đồng, đều có trích dẫn nguồn. Sinh tự động: dùng pipeline đa mô hình LLM để bổ sung câu cho các KC còn thiếu — một mô hình sinh câu theo KC và mức độ, mô hình mạnh hơn tạo đáp án tham chiếu và các ý chính cần có, một mô hình judge chấm chất lượng. Kiểm định: mỗi câu đi qua kiểm tra schema, đối chiếu nội dung bằng RAG để bắt câu sai sự thật, review thủ công trên mẫu. Chuẩn hóa: ánh xạ các tag kỹ năng chi tiết về 17 KC qua bảng tra 82 ánh xạ — ví dụ SQL_JOIN, SQL_WINDOW_FUNCTION đều quy về KC SQL_DATABASE.

Snapshot dùng để train KT gồm 1.578 câu; bản triển khai trên ứng dụng đã mở rộng lên 2.122 câu."

**Số liệu để nắm:**
- 82 ánh xạ skill_groups → 17 KC (bảng SKILL_GROUP_TO_KC).
- QC từng phát hiện lỗi scraping (tiêu đề tách khỏi nội dung), cho thấy bước kiểm định cần thiết.

---

## [Hải Đăng] Slide 9 — Thống kê dữ liệu (45 giây)

**Lời thoại:**
"Bộ dữ liệu mô phỏng gồm 1.000 người dùng chia đều ba vai trò 334-333-333, tổng khoảng 40.140 tương tác, trung bình 40 câu một người. Nhóm chia train-validation-test theo tỷ lệ 700-150-150 người dùng — tức chia ở mức người dùng, không chia theo từng tương tác, để tránh rò rỉ dữ liệu. Sau khi chia, train có khoảng 28.000 tương tác, validation và test mỗi tập khoảng 6.000. Tỷ lệ pass khoảng 82,5%, nên ở phần đánh giá nhóm ưu tiên PR-AUC thay vì chỉ dùng accuracy."

**Số liệu để nắm:**
- Tương tác: train 28.164 / val 5.911 / test 6.065.
- Lý do chia theo user: các tương tác của cùng một người phụ thuộc nhau (cùng quỹ đạo năng lực).

---

## [Hải Đăng] Slide 10 — EDA & kiểm định dữ liệu (60 giây)

**Lời thoại:**
"Phân tích khám phá xác nhận dữ liệu hợp lý trước khi huấn luyện. Phân bố câu hỏi đều theo ba vai trò, câu mức trung bình chiếm đa số. Điểm chất lượng phân bố khoảng 62% đạt mức cao nhất, 20% mức giữa, 18% trượt — nhất quán với thiết kế IRT. Learning curve tăng đơn điệu theo thứ tự câu hỏi, cho thấy mô phỏng có động lực học đúng. Tương quan giữa tự đánh giá và năng lực thật khoảng 0,72, và nhóm beginner có xu hướng tự tin thái quá.

Trước khi train, dữ liệu còn được kiểm tra qua bảy tiêu chí toàn vẹn, trong đó quan trọng nhất là không có người dùng nào xuất hiện ở cả train và test, và phân phối nhãn giữa train và test lệch dưới 1%. Tiếp theo, bạn Ngọc Nam trình bày phần mô hình."

**Số liệu để nắm:**
- Quality: Q=2 ≈ 62%, Q=1 ≈ 20%, Q=0 ≈ 18%.
- Confidence bias: r(self-rating, skill) ≈ 0.72.
- 7 tiêu chí: data leakage, label distribution, sequence length, KC frequency drift, class imbalance, quality distribution, cold-start coverage.

---

## [Ngọc Nam] Slide 11 — Thiết kế thực nghiệm (50 giây)

**Lời thoại:**
"Em là Ngọc Nam. Thực nghiệm chạy trên Kaggle với GPU Tesla T4, PyTorch 2.6, cố định seed 42 để tái lập. Quy trình KT gồm bốn notebook chạy tuần tự: EDA, feature engineering, huấn luyện, rồi đánh giá.

Nhóm thiết kế ablation study với 8 cấu hình để cô lập tác động của từng yếu tố: baseline đoán theo đa số, BKT, DKT và SAKT ở hai phiên bản binary và quality, cùng hai biến thể deep. Độ đo gồm ROC-AUC, PR-AUC, RMSE và accuracy. Vì dữ liệu mất cân bằng 82,5%, nhóm dùng PR-AUC Gain — tức phần PR-AUC vượt trên baseline — làm chỉ số so sánh chính, thay vì accuracy vốn dễ gây hiểu nhầm."

**Số liệu để nắm:**
- 8 cấu hình: Baseline, BKT, DKT-Binary, DKT-Quality★, SAKT-Binary, SAKT-Quality★, DKT-Deep, SAKT-Deep.
- Train: batch 64, 30 epoch, early stopping.

---

## [Ngọc Nam] Slide 12 — Kết quả (60 giây)

**Lời thoại:**
"Bảng kết quả trên tập test cho thấy cả 7 mô hình KT đều vượt baseline: ROC-AUC tăng từ 0,5 lên khoảng 0,67 đến 0,68, PR-AUC Gain đạt 0,083 đến 0,087.

Vài con số đáng chú ý. DKT-Quality đạt PR-AUC cao nhất 0,907 và RMSE thấp nhất 0,355, với thời gian huấn luyện chỉ khoảng 21 giây. BKT có ROC-AUC cao nhất 0,677 — em sẽ giải thích ở slide sau. SAKT-Binary nhanh nhất, chỉ 11 giây. Còn hai biến thể deep, DKT-Deep và SAKT-Deep, không cao hơn bản thường nhưng tốn thời gian gấp nhiều lần — DKT-Deep mất tới 116 giây."

**Số liệu để nắm (bảng đầy đủ 8 cấu hình):**

| Mô hình | ROC-AUC | PR-AUC | RMSE | Acc | Time(s) |
|---|---|---|---|---|---|
| Baseline | 0.500 | 0.820 | 0.384 | 0.820 | 0.0 |
| BKT | **0.677** | 0.905 | 0.374 | 0.820 | 61.9 |
| DKT-Binary | 0.666 | 0.905 | 0.375 | 0.822 | 30.8 |
| DKT-Quality★ | 0.672 | **0.907** | **0.355** | 0.796 | 20.9 |
| SAKT-Binary | 0.668 | 0.903 | 0.373 | 0.822 | **11.3** |
| SAKT-Quality★ | 0.667 | 0.904 | 0.356 | 0.776 | 12.0 |
| DKT-Deep | 0.669 | 0.906 | 0.375 | 0.822 | 116.4 |
| SAKT-Deep | 0.670 | 0.906 | 0.373 | 0.822 | 31.4 |

---

## [Ngọc Nam] Slide 13 — Phân tích (75 giây)

**Lời thoại:**
"Có bốn nhận xét chính.

Một, KT thực sự có giá trị: mọi mô hình vượt baseline rõ rệt, chứng tỏ dùng lịch sử tương tác để dự đoán câu kế tiếp là có ích, ngay cả trên dữ liệu mô phỏng.

Hai, quality label — dùng điểm liên tục thay nhãn đúng-sai — cải thiện DKT: PR-AUC cao nhất và RMSE thấp nhất nhóm neural. Lý do là điểm liên tục cung cấp tín hiệu gradient phong phú hơn. Đổi lại accuracy thấp hơn một chút vì mô hình tối ưu theo RMSE chứ không theo ngưỡng 0,5.

Ba, điểm cần phản biện: BKT đạt ROC-AUC cao nhất nhưng đây là do simulation bias — dữ liệu sinh bằng IRT có cùng dạng tham số theo từng KC như BKT, nên BKT có lợi thế không công bằng. Trên dữ liệu người dùng thật, nhóm kỳ vọng mô hình neural sẽ tốt hơn.

Bốn, mô hình sâu hơn không cải thiện đáng kể mà tốn thời gian gấp nhiều lần. Nút thắt ở đây là kích thước dữ liệu — chỉ 28.000 tương tác train — chứ không phải kiến trúc.

Phân tích sâu thêm cho thấy: AUC cao hơn ở các KC có nhiều dữ liệu; AUC tăng khi người dùng có nhiều lịch sử hơn; câu mức trung bình dễ dự đoán nhất; và mô hình thiên về dự đoán Pass do mất cân bằng lớp."

**Số liệu để nắm:**
- KC tần suất thấp (KC0 SQL_DATABASE drift 3,9%, KC3 drift 3,5%) có AUC thấp hơn.
- Theo vị trí chuỗi: early (0–25%) → late (75–100%) AUC tăng.
- Theo độ khó: MEDIUM cao nhất; theo loại user: intermediate cao nhất.
- Cold-start score tương quan dương yếu với per-user AUC.
- Lỗi: False Negative > False Positive.

---

## [Ngọc Nam] Slide 14 — Chọn mô hình (45 giây)

**Lời thoại:**
"Vì vậy nhóm chọn DKT-Quality làm mô hình chính cho ứng dụng. Lý do quan trọng nhất là dạng output: DKT cho ra dự đoán cho cả 17 KC chỉ trong một lần forward, rất phù hợp gợi ý thời gian thực, trong khi BKT phải xử lý từng KC riêng. Ngoài ra DKT-Quality có PR-AUC và RMSE tốt nhất nhóm neural, huấn luyện nhanh khoảng 21 giây. Nhóm giữ SAKT-Binary làm phương án online khi cần cập nhật mô hình liên tục, vì nó train nhanh nhất. Tiếp theo, bạn Gia Khiêm trình bày hệ thống và demo."

**Số liệu để nắm:**
- DKT-Quality output dạng (Batch, Time, 17 KC).
- Không chọn BKT dù ROC-AUC cao nhất vì simulation bias + không scale theo KC tốt.

---

## [Gia Khiêm] Slide 15 — Kiến trúc (60 giây)

**Lời thoại:**
"Em là Gia Khiêm. Hệ thống gồm ba tầng. Tầng dữ liệu chứa question bank, schema và taxonomy 17 KC, đồng thời chuẩn hóa câu hỏi và ánh xạ tag kỹ năng về KC qua Competency Engine. Tầng KT và scoring nạp mô hình tốt nhất lúc chạy, gồm bộ dự đoán KT, recommender và bộ chấm điểm. Tầng phục vụ gồm FastAPI với 9 endpoint, Streamlit làm host và giao diện React.

Một điểm kỹ thuật đáng nói: Streamlit không phục vụ được file tĩnh đúng kiểu MIME, nên nhóm tách riêng FastAPI để phục vụ giao diện và xử lý API độc lập. Ngoài ra backend dùng snake_case còn frontend dùng camelCase, nên nhóm chuẩn hóa tập trung tại ranh giới giữa hai phía để tránh sai lệch tên trường."

**Số liệu để nắm:**
- 9 endpoint FastAPI; ví dụ: /api/grade, /api/assessment/finalize.
- React SPA không dùng bundler — JSX transpile trực tiếp trên trình duyệt.

---

## [Gia Khiêm] Slide 16 — Gợi ý & MST (60 giây)

**Lời thoại:**
"Engine gợi ý xếp hạng câu hỏi theo một điểm tổng hợp: 65% ưu tiên mức yếu của KC, 30% độ phù hợp giữa độ khó câu và năng lực hiện tại, 5% độ phủ KC. Chiến lược là chọn câu hơi khó hơn năng lực hiện tại. Ngưỡng phân loại KC là dưới 0,40 coi là yếu, trên 0,70 coi là mạnh.

Bài đánh giá dùng kiểm tra thích nghi hai giai đoạn. Giai đoạn một chọn câu phủ đều các KC để định vị năng lực, rồi dựa trên điểm trung bình phân nhánh người dùng thành yếu, trung bình hoặc mạnh. Giai đoạn hai chọn câu chuyên sâu, ưu tiên các KC yếu nhất, độ khó điều chỉnh theo nhánh. Sau mỗi phiên, vector năng lực được cập nhật theo từng trục KC bằng chính pipeline EMA-Blend đã nói ở phần đầu."

**Số liệu để nắm:**
- score(q) = 0.65·weakness + 0.30·diff_fit + 0.05·coverage.
- weakness = max(0, 0.40 − θ_kc) / 0.40.
- Ngưỡng yếu/mạnh: 0.40 / 0.70.

---

## [Gia Khiêm] Slide 17 — Chấm điểm (45 giây)

**Lời thoại:**
"Về chấm điểm: câu trắc nghiệm, đúng-sai và điền chỗ trống được chấm tất định bằng so khớp đáp án, không cần gọi LLM, cho kết quả tức thì. Câu lý thuyết và coding được chấm bằng Gemini theo rubric và các ý chính cần có. Khi gọi LLM gặp lỗi, hệ thống tự động lui về bộ chấm cục bộ: một ý chính được coi là đạt khi tối thiểu 50% từ khóa của nó xuất hiện trong câu trả lời. Đây là cơ chế dự phòng thiết kế sẵn, không phải lỗi; lỗi LLM được trả kèm mã gemini_error để dễ chẩn đoán."

**Số liệu để nắm:**
- Local rubric: 4 lớp trọng số, lớp keyword/concept match chiếm 50%.
- Câu khách quan chấm client-side, không tốn chi phí LLM.

---

## [Gia Khiêm] Slide 18 — DEMO (120–150 giây)

**Lời thoại:**
"Bây giờ em demo nhanh hệ thống.

(Chọn vai trò Data Scientist.) Em vào phiên Diagnostic. Đây là một câu trắc nghiệm — chấm tất định ngay khi chọn. Và đây là một câu tự luận — được Gemini chấm theo rubric, trả về điểm cùng nhận xét.

(Hoàn tất phiên.) Đây là kết quả: hệ thống phân nhánh routing theo năng lực và cập nhật vector kỹ năng.

Sang Dashboard: biểu đồ radar so sánh năng lực hiện tại với mục tiêu của vai trò, kèm bảng các KC còn yếu — chính là gợi ý ưu tiên luyện.

Sang màn KT Model: đây là pipeline EMA, DKT rồi Blend chạy trên đúng các câu vừa trả lời. Xin lưu ý các con số ở radar này khớp hoàn toàn với Dashboard — vì cả hai dùng chung một pipeline cập nhật, đảm bảo nhất quán giữa frontend và backend."

*(Phương án dự phòng nếu lỗi mạng hoặc Gemini: chuyển sang video quay sẵn, và giải thích cơ chế fallback local rubric ở slide 17.)*

**Checklist trước demo:**
- Mở sẵn tab ứng dụng, đăng nhập/onboarding xong trước.
- Chuẩn bị 1 câu trắc nghiệm + 1 câu tự luận đã biết kết quả.
- Có sẵn video dự phòng và ảnh chụp Dashboard/KT Model.

---

## [Gia Khiêm] Slide 19 — Đóng góp & hạn chế (50 giây)

**Lời thoại:**
"Tóm lại, khóa luận có bốn đóng góp: một pipeline xây dữ liệu phỏng vấn IT tổng hợp; biến thể DKT-Quality dùng quality label; cơ chế blend KT-EMA cho cập nhật năng lực thời gian thực; và một hệ thống end-to-end chạy được từ onboarding đến dashboard.

Về hạn chế, nhóm nêu thẳng thắn. Nghiêm trọng nhất là simulation bias và việc thiếu dữ liệu người dùng thật — kết quả cần được kiểm chứng lại trên dữ liệu thực. Các hạn chế nhẹ hơn: sequence length bị cap ở 40 do giới hạn pool câu hỏi mỗi vai trò; mất cân bằng lớp 82,5% làm PR-AUC bị thổi phồng; hai KC lệch tần suất train-test trên 3%; và nhóm advanced chỉ chiếm 5,9% nên ít dữ liệu."

**Số liệu để nắm:**
- Hạn chế xếp theo mức: simulation bias (nặng) → class imbalance (trung bình) → KC drift, data scale, sequence length, phân phối trình độ lệch (nhẹ).

---

## [Gia Khiêm] Slide 20 — Kết luận (40 giây)

**Lời thoại:**
"Kết quả cho thấy KT mang lại giá trị thực cho bài toán này — ROC-AUC khoảng 0,68 so với 0,5 của baseline. DKT-Quality phù hợp cho gợi ý thời gian thực, và cơ chế blend KT-EMA xử lý được cold-start.

Hướng phát triển: thu thập dữ liệu thật để kiểm chứng và A/B test; tích hợp forgetting curve và spaced repetition; thử các mô hình Transformer như AKT, SAINT khi có đủ dữ liệu; mở rộng question bank; và triển khai production. Nhóm em xin cảm ơn thầy cô và sẵn sàng nhận câu hỏi."

---

## Dự kiến câu hỏi & trả lời (Q&A)

**1. Dữ liệu mô phỏng có đáng tin không khi không có người dùng thật?**
Nhóm thừa nhận đây là hạn chế lớn nhất. Tuy vậy dữ liệu được sinh theo IRT — mô hình chuẩn trong tâm trắc học — và đã được EDA + kiểm định 7 tiêu chí để đảm bảo tính hợp lý (learning curve tăng, phân phối quality nhất quán, không rò rỉ giữa train/test). Kết quả mô phỏng dùng để so sánh tương đối giữa các mô hình, không khẳng định con số tuyệt đối trên dữ liệu thật.

**2. Vì sao BKT ROC-AUC cao nhất mà lại không chọn?**
Vì simulation bias: dữ liệu sinh bằng IRT cùng dạng tham số theo từng KC như BKT, tạo lợi thế không công bằng. Ngoài ra BKT xử lý từng KC riêng, không cho dự đoán đồng thời 17 KC trong một forward như DKT, nên kém phù hợp cho gợi ý realtime.

**3. Vì sao chọn tỷ lệ blend 70-30 mà không phải tỷ lệ khác?**
KT nắm động lực chuỗi và quan hệ giữa các KC nên cho trọng số trội 70%. EMA giữ 30% để ổn định dự đoán, chống dao động khi gặp chuỗi nhiễu, đặc biệt ở giai đoạn đầu. Đây là hằng số cấu hình, có thể tinh chỉnh khi có dữ liệu thật.

**4. PR-AUC Gain là gì và vì sao không dùng accuracy?**
Do pass rate tới 82,5%, một mô hình đoán "Pass" hết cũng đạt accuracy 82%. PR-AUC Gain là phần PR-AUC vượt trên baseline, phản ánh khả năng phân biệt thực sự của mô hình trong điều kiện mất cân bằng.

**5. Quality label khác nhãn nhị phân thế nào?**
Nhãn nhị phân chỉ ghi đúng/sai. Quality label dùng điểm liên tục (0, 0.5, 1.0 chuẩn hóa từ điểm chất lượng 0/1/2), cung cấp tín hiệu gradient phong phú hơn khi train với MSE, giúp giảm RMSE và tăng PR-AUC.

**6. Vì sao mô hình deep không tốt hơn?**
Nút thắt là kích thước dữ liệu (28.000 tương tác train), chưa đủ để mô hình sâu hơn khai thác hết năng lực. Tăng độ sâu chỉ làm tăng thời gian (DKT-Deep 116 giây so với 31 giây) mà không cải thiện AUC.

**7. Chấm điểm bằng LLM có nhất quán không?**
Có rubric và các ý chính cố định để giảm dao động. Khi LLM lỗi, hệ thống lui về local rubric dựa trên độ phủ từ khóa. Hạn chế là chưa calibrate với chấm tay của con người — đây là hướng cải tiến.

**8. Hệ thống xử lý người dùng mới (cold-start) ra sao?**
EMA chạy ngay từ câu đầu để có ước lượng ban đầu; mô hình KT chỉ tham gia khi đã có ít nhất 3 tương tác. Ngoài ra có cold-start vector từ self-rating lúc onboarding.

---

## Ghi chú khi nói

- Mỗi người mở đầu phần của mình bằng câu chuyển tiếp ngắn (đã có trong script).
- Nói số liệu chậm và rõ; chỉ tay vào bảng/biểu đồ khi đọc con số.
- Phần demo là trọng tâm — luyện trước ít nhất 2 lần, canh đúng 2 phút.
- Khi bị hỏi mà chưa chắc, trả lời phần mình nắm rõ trước, rồi mời thành viên phụ trách bổ sung.
- Mục "Số liệu để nắm" và Q&A là phần dự phòng — không cần đọc khi trình bày, chỉ dùng khi thầy cô hỏi sâu.
