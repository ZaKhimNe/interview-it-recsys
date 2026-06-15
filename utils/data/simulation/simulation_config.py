"""
simulation_config.py — Config trung tâm cho toàn bộ simulation pipeline.

QUAN TRỌNG: Competency keys PHẢI khớp với skill_taxonomy.schema.json
  DA: SQL_DATABASE, BI_VISUALIZATION, STATISTICS_EXPERIMENTATION, ANALYTICS_BUSINESS, PYTHON_ANALYTICS
  DS: ALGORITHM_THEORY, EVALUATION_METRICS, DATA_PREPROCESSING, DEEP_LEARNING, NLP, TIME_SERIES, MLOPS
  DE: DATA_PIPELINE, DATA_ARCHITECTURE_MODELING, BIG_DATA_CLOUD_TOOLS, DATABASE_INTERNALS, SYSTEM_ARCHITECTURE
"""

# ── Simulation parameters ────────────────────────────────────────────────────
N_USERS            = 500
QUESTIONS_PER_USER = 40
NOISE              = 0.30   # Quality 1 dat ~14%; tang len de gan target 20-25%
LEARNING_RATE      = 0.08   # skill tang sau cau dung (tang de learning curve ro rang)
FORGETTING_RATE    = 0.002  # skill giam sau cau sai (giam de curve duong)
SEED               = 42

# ── Difficulty → numeric (0–1) ───────────────────────────────────────────────
DIFFICULTY_MAP = {
    "EASY":   0.30,
    "MEDIUM": 0.55,
    "HARD":   0.80,
}

# ── Phân bổ users theo role ──────────────────────────────────────────────────
ROLE_DIST = {
    "DA": 167,
    "DS": 166,
    "DE": 167,
}

# ── Mapping skill_tag → competency key (khớp skill_taxonomy.schema.json) ─────
#
# KEY RULE: competency values phải là UPPERCASE keys trong skill_taxonomy.schema.json
# vì user_profile.schema.json yêu cầu skill_vector keys = ^[A-Z][A-Z0-9_]*$
#

SKILL_GROUP_TO_COMPETENCY = {
    # ── DA ───────────────────────────────────────────────────────────────────
    "SQL_DATABASE":               "SQL_DATABASE",
    "SQL_FUNDAMENTALS":           "SQL_DATABASE",
    "SQL_WINDOW_FUNCTION":        "SQL_DATABASE",
    "SQL_JOIN":                   "SQL_DATABASE",
    "SQL_AGGREGATION":            "SQL_DATABASE",
    "SQL_PERFORMANCE":            "SQL_DATABASE",
    "SQL_CTE":                    "SQL_DATABASE",
    "DATABASE_DESIGN":            "SQL_DATABASE",

    "STATISTICS_EXPERIMENTATION": "STATISTICS_EXPERIMENTATION",
    "STAT_AB_TESTING":            "STATISTICS_EXPERIMENTATION",
    "STAT_FUNDAMENTALS":          "STATISTICS_EXPERIMENTATION",
    "STAT_DESCRIPTIVE":           "STATISTICS_EXPERIMENTATION",
    "STAT_HYPOTHESIS_TESTING":    "STATISTICS_EXPERIMENTATION",
    "STAT_CONFIDENCE_INTERVAL":   "STATISTICS_EXPERIMENTATION",

    "ANALYTICS_COHORT":           "ANALYTICS_BUSINESS",
    "ANALYTICS_FUNNEL":           "ANALYTICS_BUSINESS",
    "ANALYTICS_BUSINESS":         "ANALYTICS_BUSINESS",
    "ANALYTICS_RFM":              "ANALYTICS_BUSINESS",

    "BI_VISUALIZATION":           "BI_VISUALIZATION",
    "TOOL_POWER_BI":              "BI_VISUALIZATION",
    "TOOL_TABLEAU":               "BI_VISUALIZATION",
    "BI_CONCEPTS":                "BI_VISUALIZATION",
    "DAX_FUNDAMENTALS":           "BI_VISUALIZATION",
    "DATA_VISUALIZATION":         "BI_VISUALIZATION",
    "DATA_MODELING":              "BI_VISUALIZATION",

    "PYTHON_PANDAS":              "PYTHON_ANALYTICS",
    "PYTHON_ANALYTICS":           "PYTHON_ANALYTICS",
    "LANG_PYTHON":                "PYTHON_ANALYTICS",

    # ── DS ───────────────────────────────────────────────────────────────────
    "ALGORITHM_THEORY":           "ALGORITHM_THEORY",
    "ML_SUPERVISED":              "ALGORITHM_THEORY",
    "ML_UNSUPERVISED":            "ALGORITHM_THEORY",
    "ML_REGULARIZATION":          "ALGORITHM_THEORY",
    "ML_RECOMMENDER_SYSTEM":      "ALGORITHM_THEORY",
    "ML_ENSEMBLE":                "ALGORITHM_THEORY",
    "ML_DIMENSIONALITY_REDUCTION":"ALGORITHM_THEORY",
    "ML_ANOMALY_DETECTION":       "ALGORITHM_THEORY",
    "ML_MODEL_SELECTION":         "ALGORITHM_THEORY",
    "ML_CLUSTERING":              "ALGORITHM_THEORY",

    "DEEP_LEARNING":              "DEEP_LEARNING",
    "DL_TRAINING":                "DEEP_LEARNING",
    "DL_CNN":                     "DEEP_LEARNING",
    "DL_UNSUPERVISED":            "DEEP_LEARNING",
    "DL_FUNDAMENTALS":            "DEEP_LEARNING",
    "DL_OPTIMIZATION":            "DEEP_LEARNING",

    "NLP":                        "NLP",
    "NLP_PREPROCESSING":          "NLP",
    "NLP_EVALUATION":             "NLP",
    "NLP_FUNDAMENTALS":           "NLP",

    "EVALUATION_METRICS":         "EVALUATION_METRICS",
    "EVAL_CROSS_VALIDATION":      "EVALUATION_METRICS",
    "EVAL_CLASSIFICATION_REPORT": "EVALUATION_METRICS",
    "METRIC_F1_SCORE":            "EVALUATION_METRICS",
    "METRIC_ROC_AUC":             "EVALUATION_METRICS",
    "EVAL_REGRESSION":            "EVALUATION_METRICS",

    "DATA_PREPROCESSING":         "DATA_PREPROCESSING",
    "DATA_CLEANING":              "DATA_PREPROCESSING",
    "FEATURE_ENGINEERING":        "DATA_PREPROCESSING",
    "ENCODING_TECHNIQUES":        "DATA_PREPROCESSING",
    "IMBALANCED_DATA_HANDLING":   "DATA_PREPROCESSING",

    "TIME_SERIES":                "TIME_SERIES",
    "ML_TIME_SERIES":             "TIME_SERIES",

    "MLOPS":                      "MLOPS",
    "ML_MLOPS":                   "MLOPS",
    "ML_MONITORING":              "MLOPS",
    "ML_EXPLAINABILITY":          "MLOPS",

    # ── DE ───────────────────────────────────────────────────────────────────
    "BIG_DATA_CLOUD_TOOLS":       "BIG_DATA_CLOUD_TOOLS",
    "TOOL_SPARK":                 "BIG_DATA_CLOUD_TOOLS",
    "SPARK_DAG":                  "BIG_DATA_CLOUD_TOOLS",
    "TOOL_KAFKA":                 "BIG_DATA_CLOUD_TOOLS",
    "TOOL_AIRFLOW":               "BIG_DATA_CLOUD_TOOLS",
    "CLOUD_AWS":                  "BIG_DATA_CLOUD_TOOLS",
    "CLOUD_GCP":                  "BIG_DATA_CLOUD_TOOLS",
    "CLOUD_S3":                   "BIG_DATA_CLOUD_TOOLS",
    "BIG_DATA_OPTIMIZATION":      "BIG_DATA_CLOUD_TOOLS",
    "DEVOPS_DOCKER":              "BIG_DATA_CLOUD_TOOLS",
    "FORMAT_PARQUET":             "BIG_DATA_CLOUD_TOOLS",
    "FORMAT_AVRO":                "BIG_DATA_CLOUD_TOOLS",

    "DATA_ARCHITECTURE_MODELING": "DATA_ARCHITECTURE_MODELING",
    "ARCH_DATA_ARCHITECTURE":     "DATA_ARCHITECTURE_MODELING",
    "ARCH_SYSTEM_DESIGN":         "DATA_ARCHITECTURE_MODELING",
    "ARCH_STREAMING":             "DATA_ARCHITECTURE_MODELING",
    "DATA_WAREHOUSE":             "DATA_ARCHITECTURE_MODELING",
    "DATA_LAKE":                  "DATA_ARCHITECTURE_MODELING",
    "MODELING_SCD":               "DATA_ARCHITECTURE_MODELING",
    "MODELING_STAR_SCHEMA":       "DATA_ARCHITECTURE_MODELING",

    "DATABASE_INTERNALS":         "DATABASE_INTERNALS",
    "DATABASE_INDEXING":          "DATABASE_INTERNALS",
    "DATABASE_SCALING":           "DATABASE_INTERNALS",
    "DATABASE_PERFORMANCE":       "DATABASE_INTERNALS",
    "DB_ACID":                    "DATABASE_INTERNALS",

    "DATA_PIPELINE":              "DATA_PIPELINE",
    "PIPE_CDC":                   "DATA_PIPELINE",
    "PIPE_ELT":                   "DATA_PIPELINE",
    "PIPE_ETL":                   "DATA_PIPELINE",
    "PIPE_PERFORMANCE":           "DATA_PIPELINE",
    "PIPE_ORCHESTRATION":         "DATA_PIPELINE",
    "DATA_PIPELINE_DESIGN":       "DATA_PIPELINE",
    "PIPE_RELIABILITY":           "DATA_PIPELINE",

    "SYSTEM_ARCHITECTURE":        "SYSTEM_ARCHITECTURE",
}

# ── Competencies theo từng role (KHỚP skill_taxonomy.schema.json) ────────────
ROLE_COMPETENCIES = {
    "DA": [
        "SQL_DATABASE",
        "BI_VISUALIZATION",
        "STATISTICS_EXPERIMENTATION",
        "ANALYTICS_BUSINESS",
        "PYTHON_ANALYTICS",
    ],
    "DS": [
        "ALGORITHM_THEORY",
        "EVALUATION_METRICS",
        "DATA_PREPROCESSING",
        "DEEP_LEARNING",
        "NLP",
        "TIME_SERIES",
        "MLOPS",
    ],
    "DE": [
        "DATA_PIPELINE",
        "DATA_ARCHITECTURE_MODELING",
        "BIG_DATA_CLOUD_TOOLS",
        "DATABASE_INTERNALS",
        "SYSTEM_ARCHITECTURE",
    ],
}

# ── Fallback khi skill_group không có trong mapping ──────────────────────────
ROLE_DEFAULT_COMPETENCY = {
    "DA": "SQL_DATABASE",
    "DS": "ALGORITHM_THEORY",
    "DE": "BIG_DATA_CLOUD_TOOLS",
}
