# Pipeline Notebooks: `01_eda` → `04_evaluation`

Mô tả từng bước của quy trình huấn luyện Knowledge Tracing offline. Bốn notebook chạy **tuần tự**, mỗi notebook nhận đầu ra của notebook trước:

```
data/raw/* ──▶ 01_eda ──▶ (phát hiện & fix issue)
            ──▶ 02_feature_engineering ──▶ data/processed/*.pkl
            ──▶ 03_train_models ──▶ results/models/*, results/metrics/*, results/ablation/*
            ──▶ 04_evaluation ──▶ results/plots/* (phân tích sâu)
```

Toàn bộ cố định `seed = 42`; notebook 03–04 chạy trên Kaggle (GPU NVIDIA Tesla T4, PyTorch 2.6).

> **Lưu ý số liệu:** các con số trong báo cáo dùng snapshot cuối (1.578 câu hỏi, 1.000 người dùng, ~40.140 tương tác). Header của một số notebook bản nháp đầu còn ghi snapshot cũ hơn (1.175 câu / 500 user / 20.000 tương tác); pipeline và các bước xử lý là như nhau.

---

## 1. `01_eda.ipynb` — Phân tích khám phá dữ liệu

**Mục đích:** Kiểm tra chất lượng dữ liệu thô (null, mất cân bằng, bất thường) và phát hiện các vấn đề cần sửa **trước khi** feature engineering.

**Đầu vào** (`data/raw/`): `question_bank.json`, `virtual_users.json`, `interaction_log.csv`, `self_rating_log.csv`.

**Các bước:**
1. **Question Bank** — phân bố câu hỏi theo vai trò (DA/DS/DE), mức độ khó và loại câu; độ phủ theo từng KC. *(xuất `qbank_distribution.png`, `qbank_skill_coverage.png`)*
2. **Virtual Users** — phân bố người dùng theo vai trò/trình độ; heatmap skill vector. *(`user_distribution.png`, `user_skill_vector.png`)*
3. **Interaction Log:**
   - 3.1 Phân phối quality score (0 = Fail, 1 = Pass HR, 2 = Pass Tech). *(`quality_distribution.png`)*
   - 3.2 Độ dài chuỗi tương tác mỗi người dùng — **phát hiện cảnh báo** mọi user có cùng độ dài (uniform), không thực tế. *(`sequence_length.png`)*
   - 3.3 Learning curve — năng lực trung bình theo thứ tự câu. *(`learning_curve_eda.png`, `learning_curve_by_type.png`)*
   - 3.4 Độ phủ competency & ma trận sparsity user–KC. *(`quality_heatmap_competency.png`, `sparsity_matrix.png`)*
   - 3.5 Quality theo độ khó & skill. *(`quality_by_difficulty.png`)*
4. **Self-Rating Log** — đối chiếu tự đánh giá với skill thực → phát hiện confidence bias ($r\approx0.72$). *(`selfrating_vs_skill.png`, `confidence_bias.png`)*
5. **Tổng kết issues** — liệt kê vấn đề cần fix: chuẩn hóa quality → nhãn nhị phân (cho AUC) + nhãn float (cho RMSE); cảnh báo uniform sequence length; gợi ý chỉnh `simulation_config.py`.

**Đầu ra:** các biểu đồ trong `results/plots/` + danh sách issue định hướng bước tiếp theo.

---

## 2. `02_feature_engineering.ipynb` — Kỹ thuật đặc trưng

**Mục đích:** Biến dữ liệu thô đã làm sạch thành các chuỗi (sequence) sẵn sàng cho huấn luyện KT.

**Đầu vào:** `interaction_log.csv` (đã fix), `self_rating_log.csv`.

**Các bước:**
1. **Load & kiểm tra** thống kê độ dài chuỗi.
2. **Tạo nhãn:** `correct = (quality_score ≥ 1)` ∈ {0,1} (cho AUC — BKT, DKT-Binary, SAKT-Binary) và `quality_norm = quality_score / 2` ∈ {0, 0.5, 1.0} (cho RMSE — DKT-Quality, SAKT-Quality).
3. **Encoding:** ánh xạ KC, user, question, difficulty sang chỉ số (index) nguyên.
4. **Chia tập theo người dùng** (không theo thời gian) tỷ lệ 70/15/15 để tránh data leakage; in thống kê từng tập.
5. **Build sequences** — mỗi user thành 1 dict theo `session_order`, chứa: `kc_seq`, `q_seq`, `correct_seq`, `quality_seq`, `diff_seq`, `skill_seq` (skill thực để phân tích), `seq_len`, `split`.
6. **Cold-start features** — trích từ `self_rating_log` (vector tự đánh giá ban đầu).
7. **Lưu** dữ liệu đã xử lý và **verify**.

**Đầu ra** (`data/processed/`): `train_seqs.pkl`, `val_seqs.pkl`, `test_seqs.pkl` + các bộ encoder/metadata.

---

## 3. `03_train_models.ipynb` — Huấn luyện KT (Ablation Study)

**Mục đích:** Huấn luyện và so sánh 8 cấu hình KT trên cùng dữ liệu, cùng thiết lập.

**Đầu vào:** `data/processed/{train,val,test}_seqs.pkl`.

**8 cấu hình ablation:**

| # | Tên | Model | Nhãn | Tham số |
|---|-----|-------|------|---------|
| 0 | Baseline | Majority class | binary | — |
| 1 | BKT | Bayesian HMM | binary | 4 tham số/KC, L-BFGS-B |
| 2 | DKT-Binary | LSTM | binary (BCE) | h=128, L=1, d=0.2 |
| 3 | DKT-Quality★ | LSTM | quality (MSE) | h=128, L=1, d=0.2 |
| 4 | SAKT-Binary | Self-Attention | binary (BCE) | e=64, H=4, L=1 |
| 5 | SAKT-Quality★ | Self-Attention | quality (MSE) | e=64, H=4, L=1 |
| 6 | DKT-Deep | LSTM (sâu) | binary | h=256, L=2, d=0.3 |
| 7 | SAKT-Deep | Self-Attention (sâu) | binary | e=128, H=4, L=2 |

**Các bước:**
1. **Kiểm tra toàn vẹn dữ liệu (7 tiêu chí):** không rò rỉ user giữa train/test; phân phối nhãn train≈test; độ dài chuỗi; drift tần suất KC; mất cân bằng lớp (→ dùng PR-AUC); phân phối quality; độ phủ cold-start.
2. **Định nghĩa độ đo:** `roc_auc_score`, `average_precision_score` (PR-AUC, ổn định khi mất cân bằng), RMSE, Accuracy; hàm `record()` ghi kết quả val/test + thời gian.
3. **Huấn luyện** lần lượt 8 cấu hình: Baseline (majority), BKT (tối ưu L-BFGS-B theo KC), DKT/SAKT (binary với BCE, quality với MSE), và biến thể deep; batch 64, 30 epoch, early stopping.
4. **Lưu** trọng số + metrics + bảng tổng hợp ablation.

**Đầu ra:** `results/models/` (`bkt.npy`, `dkt_binary.pt`, `dkt_quality.pt`, `sakt_*.pt`, `*_deep.pt` + `metadata.json`), `results/metrics/*.json`, `results/ablation/ablation_results.csv`.

---

## 4. `04_evaluation.ipynb` — Đánh giá & phân tích sâu

**Mục đích:** Phân tích chuyên sâu kết quả sau huấn luyện để hiểu hành vi mô hình và rút kết luận có phản biện.

**Đầu vào:** `results/models/*` + `data/processed/*_seqs.pkl`.

**Các bước (mục):**
1. **Load** models (BKT, DKT-Binary/Quality/Deep, SAKT-Binary/Quality/Deep) + dữ liệu test.
2. **Per-KC AUC** — AUC riêng từng KC, so sánh BKT vs DKT-Quality★; bảng delta. *(`per_kc_auc.png`)*
3. **Phân tích theo vị trí trong chuỗi** — early vs late (mô hình học tốt hơn khi có nhiều lịch sử). *(`position_auc.png`)*
4. **Phân tầng theo độ khó** — EASY/MEDIUM/HARD. *(`difficulty_auc.png`)*
5. **Phân tích theo loại người dùng** — beginner/intermediate/advanced. *(`usertype_auc.png`)*
6. **Cold-start vs độ chính xác** — tương quan cold-start score với per-user AUC. *(`coldstart_vs_acc.png`)*
7. **Phân tích lỗi** — confusion matrix + phân phối điểm dự đoán của mô hình tốt nhất (DKT-Quality★). *(`error_analysis.png`)*

**Đầu ra:** các biểu đồ phân tích trong `results/plots/`; kết luận chọn DKT-Quality★ làm mô hình triển khai.

---

## 5. Tái lập (Reproducibility)

1. Đặt dữ liệu thô vào `data/raw/`.
2. Chạy tuần tự: `01_eda` → `02_feature_engineering` → `03_train_models` → `04_evaluation`.
3. Giữ `seed = 42`; notebook 03–04 cần GPU (Kaggle Tesla T4, PyTorch 2.6).
4. Mô hình tốt nhất (`dkt_quality.pt`) được nạp ở runtime bởi `src/kt/kt_predictor.py` cho hệ thống web.
