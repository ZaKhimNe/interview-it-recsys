"""
build_reference.py — Dùng GPT-4o sinh reference docs cho 17 competency.

Cross-model: Gemini sinh câu hỏi → GPT-4o sinh reference → Claude Haiku review.
GPT-4o làm reference độc lập, tránh bias vòng kín.

Chạy: python utils/data/generation/build_reference.py
       python utils/data/generation/build_reference.py --force   # tạo lại hết
       python utils/data/generation/build_reference.py --comp DATABASE_INTERNALS
Output: data/reference/<COMPETENCY>.txt  (17 files)
"""

import os, sys, time, argparse
from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def get_client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        env_path = os.path.join(ROOT, ".env")
        if os.path.exists(env_path):
            for line in open(env_path, encoding="utf-8"):
                if "OPENAI_API_KEY" in line and "=" in line:
                    key = line.strip().split("=", 1)[1].strip().strip('"')
    if not key:
        raise ValueError("Chua set OPENAI_API_KEY trong .env")
    return OpenAI(api_key=key)


COMPETENCIES = [
    {
        "key": "SQL_DATABASE",
        "role": "DA",
        "topics": "SQL fundamentals, JOINs (INNER/LEFT/RIGHT/FULL), subqueries, window functions (ROW_NUMBER/RANK/DENSE_RANK/LAG/LEAD/NTILE), CTEs, indexes (B-tree, composite, covering), query optimization, execution plan, normalization (1NF-3NF), database design"
    },
    {
        "key": "BI_VISUALIZATION",
        "role": "DA",
        "topics": "Power BI (DAX measures vs calculated columns, data model, relationships, star schema in Power BI), Tableau (LOD expressions, calculated fields, blending), data visualization best practices (chart selection, color, clarity), OLAP concepts, slowly changing dimensions"
    },
    {
        "key": "STATISTICS_EXPERIMENTATION",
        "role": "DA",
        "topics": "Descriptive statistics (mean/median/mode/std/variance/skewness), probability distributions (normal, binomial, Poisson), hypothesis testing (t-test, chi-square, ANOVA), p-value interpretation, confidence intervals, A/B testing design and pitfalls, statistical significance vs practical significance, multiple testing correction (Bonferroni)"
    },
    {
        "key": "ANALYTICS_BUSINESS",
        "role": "DA",
        "topics": "Cohort analysis (retention cohort, behavior cohort), funnel analysis (conversion rates, drop-off), RFM analysis (Recency, Frequency, Monetary scoring), retention metrics, churn prediction, business KPIs (DAU/MAU/WAU, LTV, CAC, ARPU), attribution modeling (first-touch, last-touch, multi-touch), customer segmentation"
    },
    {
        "key": "PYTHON_ANALYTICS",
        "role": "DA",
        "topics": "Pandas (DataFrame creation, indexing/loc/iloc, groupby aggregations, merge/join types, pivot_table, apply/map/applymap, handling missing values with fillna/dropna), NumPy (array operations, broadcasting, vectorization), data cleaning techniques, datetime handling, string operations, matplotlib/seaborn plotting basics"
    },
    {
        "key": "ALGORITHM_THEORY",
        "role": "DS",
        "topics": "Supervised learning (linear regression assumptions, logistic regression, decision tree splitting criteria, random forest bagging+feature subsampling, gradient boosting weak learners, XGBoost, SVM kernels, KNN distance metrics), unsupervised learning (K-means elbow method, DBSCAN eps/min_samples, PCA variance explained), regularization (L1 sparsity, L2 weight decay, ElasticNet), bias-variance tradeoff, ensemble methods (bagging vs boosting vs stacking)"
    },
    {
        "key": "EVALUATION_METRICS",
        "role": "DS",
        "topics": "Classification: accuracy pitfall, precision vs recall tradeoff, F1-score, F-beta, ROC-AUC interpretation, PR-AUC for imbalanced data, confusion matrix (TP/FP/TN/FN). Regression: MAE vs RMSE sensitivity to outliers, R-squared vs adjusted R-squared, MAPE. Cross-validation: k-fold, stratified k-fold, time-series split, leave-one-out. Threshold selection, class imbalance impact on metrics"
    },
    {
        "key": "DATA_PREPROCESSING",
        "role": "DS",
        "topics": "Missing value strategies (mean/median/mode imputation, KNN imputation, indicator variables), outlier detection (IQR method, Z-score, isolation forest), feature scaling (StandardScaler vs MinMaxScaler vs RobustScaler — when to use each), encoding (one-hot encoding, label encoding, target encoding risks), feature engineering, feature selection (filter/wrapper/embedded methods), imbalanced datasets (SMOTE, ADASYN, class_weight, undersampling)"
    },
    {
        "key": "DEEP_LEARNING",
        "role": "DS",
        "topics": "Neural network fundamentals (forward pass, backpropagation, chain rule, activation functions: ReLU/sigmoid/tanh/softmax), CNN (convolution operation, pooling, receptive field, architectures: VGG/ResNet skip connections/EfficientNet), RNN/LSTM gating/GRU, optimization (SGD momentum, Adam, learning rate scheduling, warmup), regularization (dropout probability, batch normalization, weight decay), transfer learning (feature extraction vs fine-tuning)"
    },
    {
        "key": "NLP",
        "role": "DS",
        "topics": "Text preprocessing (tokenization, stemming vs lemmatization, stop words, normalization), Bag of Words, TF-IDF formula and weighting, word embeddings (Word2Vec CBOW vs Skip-gram, GloVe, FastText subword), transformer architecture (self-attention, multi-head attention, positional encoding), BERT (bidirectional, masked language model, fine-tuning), text classification, NER, evaluation (BLEU, ROUGE-N/L, perplexity)"
    },
    {
        "key": "TIME_SERIES",
        "role": "DS",
        "topics": "Components (trend, seasonality, cyclic, noise), stationarity (ADF test, KPSS, differencing to achieve stationarity), ARIMA (p/d/q parameters, ACF/PACF interpretation), SARIMA seasonal parameters, exponential smoothing (simple, Holt, Holt-Winters), feature engineering for TS (lag features, rolling mean/std, expanding window), train/test split without leakage, cross-validation for TS (time-series split), forecasting evaluation (MAPE, SMAPE, MAE, RMSE)"
    },
    {
        "key": "MLOPS",
        "role": "DS",
        "topics": "ML pipeline design (training/serving skew), experiment tracking with MLflow (runs, params, metrics, artifacts, model registry), model versioning, deployment patterns (REST API inference, batch scoring, streaming inference), model monitoring (data drift detection, concept drift, performance degradation alerts), CI/CD for ML (testing data pipelines, model validation gates), feature store (online vs offline), A/B testing models, SHAP values, LIME"
    },
    {
        "key": "DATA_PIPELINE",
        "role": "DE",
        "topics": "ETL vs ELT differences and when to use each, batch vs micro-batch vs streaming trade-offs, Apache Airflow (DAG definition, operators: PythonOperator/BashOperator/Sensors, scheduling, XCom, task dependencies, backfill), CDC (log-based vs trigger-based, Debezium), data quality checks in pipelines (Great Expectations, dbt tests), error handling and retry strategies, idempotency design, pipeline monitoring and alerting"
    },
    {
        "key": "DATA_ARCHITECTURE_MODELING",
        "role": "DE",
        "topics": "Data warehouse vs data lake vs lakehouse (delta format, ACID on lake), dimensional modeling (fact tables: additive/semi-additive/non-additive measures, dimension tables, surrogate keys), star schema vs snowflake schema trade-offs, SCD Type 1/2/3 implementation, data vault (hub/link/satellite), Lambda architecture (batch layer + speed layer), Kappa architecture, data mesh (domain ownership, data as product), partitioning strategies (by date, by key)"
    },
    {
        "key": "BIG_DATA_CLOUD_TOOLS",
        "role": "DE",
        "topics": "Apache Spark (RDD vs DataFrame vs Dataset, lazy evaluation, transformations vs actions, wide vs narrow transformations, shuffle operations, partitioning strategy, broadcast join vs shuffle join, Spark SQL, optimization: predicate pushdown/columnar storage), Apache Kafka (topics, partitions, replication factor, consumer groups, offset management, exactly-once semantics), Parquet vs Avro vs ORC (columnar vs row-based), Docker containerization, S3/GCS object storage patterns"
    },
    {
        "key": "DATABASE_INTERNALS",
        "role": "DE",
        "topics": "ACID properties (atomicity, consistency, isolation, durability — how each is implemented), transaction isolation levels (READ UNCOMMITTED/READ COMMITTED/REPEATABLE READ/SERIALIZABLE — dirty read, non-repeatable read, phantom read), indexing deep dive (B-tree structure, hash index, composite index column order, covering index, index selectivity), query execution plan (seq scan vs index scan, cost estimation), database scaling (vertical vs horizontal, read replicas, sharding strategies: range/hash), CAP theorem trade-offs, connection pooling"
    },
    {
        "key": "SYSTEM_ARCHITECTURE",
        "role": "DE",
        "topics": "Microservices vs monolithic (trade-offs: deployment independence vs network overhead), REST API design (statelessness, idempotency, HTTP methods, status codes, versioning), message queues (Kafka vs RabbitMQ use cases, pub/sub vs point-to-point), caching strategies (cache-aside, write-through, write-behind, TTL, Redis data structures), load balancing (round-robin, least-connections, consistent hashing), high availability patterns (failover, circuit breaker, bulkhead), system design for data-intensive applications"
    },
]


PROMPT_TEMPLATE = """You are a principal engineer and technical interviewer with 10+ years of experience hiring for Data Analytics, Data Science, and Data Engineering roles at top-tier tech companies.

Your task: Write a **technical reference document** for competency **{key}** (role: {role}).

This document will serve as the **ground truth** used by an AI reviewer to evaluate interview questions. It must be precise, deep, and unambiguous — a weak or vague reference will cause the reviewer to accept bad questions or reject good ones.

## Topics to cover (all required):
{topics}

## Document requirements:

**Depth:**
- For each concept: precise technical definition → underlying mechanism → when/why it matters in practice
- Explicitly state common confusions (e.g. "Many candidates confuse X with Y — the key difference is...")
- Include quantitative thresholds, complexity bounds, or formula references where applicable (e.g. "O(log n) for B-tree lookup", "p-value < 0.05 threshold", "L1 produces sparse weights because...")
- Flag interview-critical distinctions: things that separate a strong answer from a mediocre one

**Format:**
- Use ## headings for each major topic
- Use bullet points for sub-concepts and comparisons
- Use **bold** for key terms on first use
- Length: 1100-1400 words (thorough coverage, no padding)

**Quality bar:**
- Technically accurate at senior/staff engineer level
- No hand-waving — every claim must be precise enough to evaluate a candidate answer against
- Include at least 2-3 "interviewer red flags" — wrong answers or misconceptions that should cause a question to FAIL QC

Output ONLY the document. No intro sentence, no outro, no meta-commentary."""


def build_one(client: OpenAI, comp: dict, min_words: int = 750, max_retries: int = 3) -> str:
    prompt = PROMPT_TEMPLATE.format(
        key=comp["key"],
        role=comp["role"],
        topics=comp["topics"]
    )
    last_content = ""
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=6000,
                temperature=0.2,
                timeout=60,
            )
            content = resp.choices[0].message.content.strip()
            word_count = len(content.split())
            last_content = content
            if word_count >= min_words:
                return content
            print(f"\n    attempt {attempt+1}: {word_count} words < {min_words}, retrying...", end=" ", flush=True)
            time.sleep(3)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                wait = 30 * (attempt + 1)
                print(f"\n    Rate limit (429), waiting {wait}s...", end=" ", flush=True)
                time.sleep(wait)
            else:
                raise  # lỗi thực sự, không retry
    return last_content  # trả về dù ngắn sau max_retries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Tạo lại dù file đã có")
    parser.add_argument("--comp", help="Chỉ build 1 competency (vd: DATABASE_INTERNALS)")
    args = parser.parse_args()

    out_dir = os.path.join(ROOT, "data/reference")
    os.makedirs(out_dir, exist_ok=True)
    client = get_client()

    existing = {f.replace(".txt", "") for f in os.listdir(out_dir) if f.endswith(".txt")}

    todo = COMPETENCIES
    if args.comp:
        todo = [c for c in COMPETENCIES if c["key"] == args.comp]
        if not todo:
            print(f"Competency '{args.comp}' not found.")
            return
    elif not args.force:
        todo = [c for c in COMPETENCIES if c["key"] not in existing]

    print(f"Model: gpt-4o (cross-model vs Gemini-generated questions)")
    print(f"Total competencies: {len(COMPETENCIES)}")
    print(f"Already built: {len(existing)}")
    print(f"To build: {len(todo)}\n")

    failed = []
    for i, comp in enumerate(todo):
        key = comp["key"]
        print(f"[{i+1}/{len(todo)}] Building {key}...", end=" ", flush=True)
        try:
            content = build_one(client, comp)
            word_count = len(content.split())
            out_path = os.path.join(out_dir, f"{key}.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {key} — Reference Document (Source: GPT-4o)\n\n")
                f.write(content)
            status = "OK" if word_count >= 750 else "SHORT"
            print(f"{status} ({word_count} words)")
            if status == "SHORT":
                failed.append(f"{key} ({word_count} words)")
        except Exception as e:
            print(f"ERROR: {e}")
            failed.append(f"{key} (ERROR: {e})")
        time.sleep(2)  # rate limit

    total = len([f for f in os.listdir(out_dir) if f.endswith(".txt")])
    print(f"\nDone. {total}/17 reference files in data/reference/")
    if failed:
        print(f"\nWARNING — {len(failed)} competency can check lai:")
        for item in failed:
            print(f"  - {item}")
        print(f"\nChay lai tung cai bi loi:")
        for item in failed:
            key = item.split(" ")[0]
            print(f"  python utils/data/generation/build_reference.py --comp {key}")
    else:
        print("\nTat ca OK. Buoc tiep theo:")
        print("  python utils/data/qc/qc_rag.py --all")


if __name__ == "__main__":
    main()
