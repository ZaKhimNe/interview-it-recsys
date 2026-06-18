# Bao cao nghiem thu module AI Core

## 1. Muc tieu thuc hien

Module AI Core cua du an InternHub duoc hoan thien de phuc vu hai nghiep vu chinh:

1. Goi y cau hoi phong van/danh gia nang luc dua tren vector nang luc hien tai cua ung vien.
2. Cham diem cau tra loi cua ung vien va sinh cau hoi follow-up phu hop.

Trong qua trinh ra soat, phat hien logic ban dau dang bi lech huong: cac TODO va vector nang luc cu duoc thiet ke theo nhom ky su phan mem chung nhu `dsa`, `system_design`, `database`, `oop`, `networking`, `devops`. Tuy nhien, du lieu that trong `data/mock/mockdata.json` lai la ngan hang cau hoi cho cac nhom nganh du lieu, gom `DA`, `DE`, `DS`, voi cac skill nhu SQL, Analytics, Statistics, Data Engineering, Big Data, Machine Learning, Deep Learning va MLOps.

Vi vay, phan viec da lam khong chi la dien code vao cac ham TODO, ma con dieu chinh lai truc nang luc va logic recommender de khop voi mock data hien co.

## 2. Pham vi thay doi

Nhung file da duoc cap nhat:

| File | Noi dung thay doi |
| --- | --- |
| `ai_core/recommender.py` | Cai dat thuat toan goi y cau hoi thich ung, map cau hoi theo skill cua nhom nganh data, tinh diem goi y va do kho muc tieu. |
| `ai_core/grader.py` | Cai dat cham diem cau tra loi bang Gemini khi co API key, kem fallback local deterministic khi khong co API key hoac API loi. |
| `core/competency_engine.py` | Doi truc vector nang luc tu 6 domain ky su phan mem sang 10 competency phu hop mock data. |
| `config.py` | Cap nhat danh sach competency hien thi trong cau hinh chung. |
| `tests/test_ai_core.py` | Them test cho recommender, adaptive difficulty, grader fallback va follow-up fallback. |
| `tests/test_core.py` | Cap nhat test competency engine theo vector 10 chieu moi. |

## 3. Dieu chinh truc nang luc

### 3.1. Truc cu

Truoc khi dieu chinh, he thong su dung 6 domain:

```text
dsa
system_design
database
oop
networking
devops
```

Truc nay phu hop hon voi phong van Software Engineer/Backend Engineer tong quat, nhung khong phan anh dung ngan hang cau hoi hien co.

### 3.2. Truc moi

Truc nang luc moi gom 10 competency:

```text
sql
analytics
statistics
visualization
data_engineering
big_data
machine_learning
deep_learning
mlops
programming
```

Ly do chon cac competency nay:

| Competency | Y nghia | Vi du tag trong mock data |
| --- | --- | --- |
| `sql` | Kien thuc SQL, database, query optimization | `SQL_JOIN`, `SQL_FUNDAMENTALS`, `DATABASE_INDEXING`, `DAX_FUNDAMENTALS` |
| `analytics` | Phan tich kinh doanh, metrics, product analytics | `ANALYTICS_BUSINESS`, `ANALYTICS_COHORT`, `ANALYTICS_FUNNEL` |
| `statistics` | Thong ke, A/B testing, hypothesis testing | `STAT_AB_TESTING`, `STAT_DESCRIPTIVE`, `STAT_HYPOTHESIS_TESTING` |
| `visualization` | BI tool va truc quan hoa du lieu | `TOOL_POWER_BI`, `TOOL_TABLEAU`, `DATA_VISUALIZATION` |
| `data_engineering` | Pipeline, warehouse, orchestration, CDC | `DATA_PIPELINE_DESIGN`, `DATA_WAREHOUSE`, `PIPE_CDC`, `TOOL_AIRFLOW` |
| `big_data` | Xu ly du lieu lon va streaming | `TOOL_SPARK`, `TOOL_KAFKA`, `BIG_DATA_OPTIMIZATION` |
| `machine_learning` | ML co ban, model selection, feature engineering | `ML_MODEL_SELECTION`, `ML_SUPERVISED`, `FEATURE_ENGINEERING` |
| `deep_learning` | Deep Learning va training neural network | `DL_TRAINING`, `DL_CNN`, `ML_REGULARIZATION` |
| `mlops` | Trien khai, monitoring, drift, explainability | `ML_MLOPS`, `ML_MONITORING`, `ML_EXPLAINABILITY` |
| `programming` | Python, Pandas, coding va tien xu ly du lieu | `PYTHON_PANDAS`, `DATA_PREPROCESSING`, `CODING` |

## 4. Logic goi y cau hoi

### 4.1. Dau vao

Ham chinh:

```python
recommend_questions(
    competency_vector: np.ndarray,
    question_bank: list[dict],
    num_recommendations: int = 5,
    focus_weak: bool = True,
) -> list[dict]
```

Dau vao gom:

| Tham so | Y nghia |
| --- | --- |
| `competency_vector` | Vector diem nang luc cua ung vien, moi diem trong khoang 0-10. |
| `question_bank` | Danh sach cau hoi lay tu mock data. |
| `num_recommendations` | So cau hoi can goi y. |
| `focus_weak` | Neu `True`, uu tien cac competency yeu. Neu `False`, uu tien cau hoi phu hop voi muc san sang hien tai. |

Thu tu vector phai khop voi `COMPETENCY_KEYS`:

```python
[
    "sql",
    "analytics",
    "statistics",
    "visualization",
    "data_engineering",
    "big_data",
    "machine_learning",
    "deep_learning",
    "mlops",
    "programming",
]
```

### 4.2. Buoc 1: Chuan hoa vector

Vector dau vao duoc dua ve numpy array, lam phang va cat/bo sung do dai cho bang 10 competency.

Neu vector ngan hon 10 chieu, cac chieu thieu duoc gan 0. Neu vector dai hon 10 chieu, chi lay 10 chieu dau. Sau do tat ca gia tri duoc clip ve khoang 0-10.

Muc dich:

1. Tranh loi khi du lieu dau vao khong dung kich thuoc.
2. Dam bao diem nang luc nam trong mien hop le.
3. Giu he thong chay on dinh trong demo/test.

### 4.3. Buoc 2: Suy ra competency cua tung cau hoi

Moi cau hoi duoc map vao mot competency bang ham noi bo `_question_competency()`.

Thu tu suy luan:

1. Doc `skill_tags` cua cau hoi.
2. So khop tag voi cac cum tu goi y trong `TAG_COMPETENCY_HINTS`.
3. Neu khong map duoc bang tag, fallback theo `roles.primary`.
4. Neu van khong map duoc, competency cua cau hoi la `None` va se dung diem trung binh vector de tinh.

Vi du:

| Du lieu cau hoi | Competency suy ra |
| --- | --- |
| `skill_tags = ["SQL_JOIN"]` | `sql` |
| `skill_tags = ["DATA_PIPELINE_DESIGN"]` | `data_engineering` |
| `skill_tags = ["TOOL_SPARK"]` | `big_data` |
| `skill_tags = ["ML_MODEL_SELECTION"]` | `machine_learning` |
| `roles.primary = "DA"` va tag khong ro | `analytics` |
| `roles.primary = "DE"` va tag khong ro | `data_engineering` |
| `roles.primary = "DS"` va tag khong ro | `machine_learning` |

### 4.4. Buoc 3: Xac dinh do kho muc tieu

Ham:

```python
adaptive_difficulty(current_score: float, streak: int = 0) -> str
```

Logic:

| Diem nang luc | Do kho muc tieu |
| --- | --- |
| Nho hon 4.0 | `easy` |
| Tu 4.0 den nho hon 7.0 | `medium` |
| Tu 7.0 tro len | `hard` |

Tham so `streak` dung de dieu chinh theo phong do gan nhat:

| Streak | Cach dieu chinh |
| --- | --- |
| `streak >= 3` | Cong them 1 diem tam thoi de co the tang do kho. |
| `streak <= -2` | Tru 1 diem tam thoi de co the ha do kho. |
| Con lai | Giu nguyen diem hien tai. |

Vi du:

```text
current_score = 2.5 -> easy
current_score = 5.0 -> medium
current_score = 7.5 -> hard
current_score = 6.5, streak = 3 -> hard
current_score = 4.5, streak = -2 -> easy
```

### 4.5. Buoc 4: Tinh diem yeu cua competency

Neu cau hoi thuoc competency `sql`, he thong lay diem `sql` cua ung vien trong vector.

Cong thuc:

```text
weak_priority = (10 - competency_score) / 10
```

Y nghia:

| `competency_score` | `weak_priority` | Dien giai |
| --- | --- | --- |
| 2.0 | 0.8 | Rat nen uu tien vi day la diem yeu. |
| 5.0 | 0.5 | Muc trung binh. |
| 8.0 | 0.2 | Khong can uu tien neu dang focus vao diem yeu. |

### 4.6. Buoc 5: Tinh do khop do kho

Moi cau hoi co `difficulty_score` tu 1-10 hoac `difficulty_label`.

He thong quy doi do kho muc tieu thanh diem:

| Do kho | Diem dai dien |
| --- | --- |
| `easy` | 2.5 |
| `medium` | 5.0 |
| `hard` | 7.5 |
| `expert` | 9.0 |

Cong thuc:

```text
difficulty_fit = 1 - min(abs(question_difficulty - target_difficulty) / 9, 1)
```

Y nghia:

1. Cau hoi co do kho cang gan muc tieu thi `difficulty_fit` cang cao.
2. Cau hoi qua de hoac qua kho so voi nang luc hien tai se bi giam diem.
3. Dieu nay giup he thong khong chi chon domain yeu, ma con chon cau hoi vua suc.

### 4.7. Buoc 6: Tinh diem goi y tong hop

Neu `focus_weak=True`, cong thuc:

```text
recommendation_score = 0.65 * weak_priority
                     + 0.30 * difficulty_fit
                     + coverage_bonus
```

Trong do:

| Thanh phan | Trong so | Y nghia |
| --- | --- | --- |
| `weak_priority` | 65% | Uu tien cai thien diem yeu. |
| `difficulty_fit` | 30% | Dam bao cau hoi dung muc do. |
| `coverage_bonus` | Nho | Bonus cho cau hoi khong map duoc competency de tranh bi loai hoan toan. |

Neu `focus_weak=False`, cong thuc:

```text
recommendation_score = 0.45 * readiness
                     + 0.45 * difficulty_fit
                     + coverage_bonus
```

Trong do:

```text
readiness = competency_score / 10
```

Che do nay phu hop khi muon luyen theo muc ung vien da san sang, thay vi chi tap trung vao diem yeu.

### 4.8. Buoc 7: Sap xep va tra ket qua

Moi cau hoi tra ve duoc bo sung them cac truong:

| Truong | Y nghia |
| --- | --- |
| `recommendation_score` | Diem goi y tong hop da lam tron. |
| `recommended_competency` | Competency ma he thong suy ra cho cau hoi. |
| `target_difficulty` | Do kho muc tieu cua ung vien o competency do. |

Sau do danh sach duoc sap xep giam dan theo `recommendation_score` va cat theo `num_recommendations`.

## 5. Logic cham diem cau tra loi

### 5.1. Ham chinh

```python
grade_answer(
    question: str,
    expected_answer: str,
    candidate_answer: str,
    scoring_rubric: Optional[str] = None,
) -> dict
```

Ket qua tra ve:

```python
{
    "score": float,
    "feedback": str,
    "strengths": list[str],
    "improvements": list[str],
}
```

### 5.2. Hai tang cham diem

He thong duoc thiet ke voi hai tang:

1. Cham diem bang Gemini neu `GOOGLE_API_KEY` duoc cau hinh.
2. Cham diem local fallback neu khong co API key hoac API loi.

Cach nay giup:

1. Demo va unit test chay duoc offline.
2. Khong phu thuoc bat buoc vao mang/API.
3. Khi co LLM, chat luong feedback tot hon.
4. Khi LLM loi, he thong van tra duoc ket qua thay vi crash.

### 5.3. Luong cham diem bang Gemini

Neu `GOOGLE_API_KEY` ton tai:

1. Tao prompt tu `GRADING_PROMPT` trong `ai_core/prompts.py`.
2. Dua vao cau hoi, dap an tham khao, cau tra loi ung vien va rubric.
3. Goi model Gemini cau hinh trong `config.py`.
4. Yeu cau response dang JSON.
5. Parse JSON va ep ve format chuan.
6. Clip diem ve khoang 0-10.

Neu response khong parse duoc JSON hoac API loi, he thong tu dong fallback sang cham diem local.

### 5.4. Luong cham diem local fallback

Fallback local khong co y dinh thay the hoan toan LLM, ma phuc vu cac muc tieu:

1. Co ket qua deterministic de test.
2. Co diem tham khao khi chua cau hinh API.
3. Dam bao ung dung khong bi dung khi API loi.

Quy trinh:

1. Chuan hoa `expected_answer`, `candidate_answer`, `scoring_rubric`.
2. Tach token bang regex.
3. Loai bo mot so stopword pho bien.
4. Tinh muc do trung khop keyword giua cau tra loi va dap an mau.
5. Tinh muc do trung khop voi rubric.
6. Tinh ti le do dai cau tra loi so voi dap an mau.
7. Tong hop thanh diem 0-10.

Cong thuc:

```text
score = (
    0.70 * expected_overlap
  + 0.20 * rubric_overlap
  + 0.10 * length_ratio
) * 10
```

Trong do:

| Thanh phan | Y nghia |
| --- | --- |
| `expected_overlap` | Ty le keyword trong dap an mau xuat hien trong cau tra loi. |
| `rubric_overlap` | Ty le keyword trong rubric xuat hien trong cau tra loi. |
| `length_ratio` | Do dai cau tra loi so voi dap an mau, toi da 1.0. |

### 5.5. Xu ly cau tra loi rong

Neu `candidate_answer` rong hoac chi gom khoang trang:

```python
{
    "score": 0.0,
    "feedback": "Chua co cau tra loi de cham diem.",
    "strengths": [],
    "improvements": [
        "Can tra loi bang cac y chinh lien quan den dap an tham khao."
    ],
}
```

### 5.6. Sinh feedback

Fallback local sinh feedback theo cac rule:

| Dieu kien | Ket qua |
| --- | --- |
| Trung khop dap an mau cao | Them strength: nam duoc nhieu y chinh. |
| Co trung khop mot phan | Them strength: co noi dung lien quan. |
| Khong trung khop | Them improvement: can bo sung khai niem cot loi. |
| Rubric co nhung trung khop thap | Them improvement: can bam sat rubric hon. |
| Cau tra loi qua ngan | Them improvement: can giai thich ro hon. |
| Khong co loi ro rang | Goi y bo sung vi du hoac edge case. |

## 6. Logic sinh cau hoi follow-up

Ham:

```python
generate_follow_up(
    question: str,
    candidate_answer: str,
    difficulty: str = "medium",
) -> str
```

Luong xu ly:

1. Neu co `GOOGLE_API_KEY`, tao prompt tu `FOLLOW_UP_PROMPT`.
2. Goi Gemini de sinh cau hoi follow-up theo cau tra loi cua ung vien.
3. Neu khong co API key hoac API loi, dung fallback local.

Fallback local:

| Difficulty | Cau hoi fallback |
| --- | --- |
| `easy` | Yeu cau giai thich lai bang vi du ngan gon. |
| `medium` | Yeu cau neu them vi du va ly do cach tiep can dung. |
| `hard` | Yeu cau phan tich edge case va trade-off trong he thong thuc te. |

## 7. Cap nhat competency engine

### 7.1. Tao vector nang luc

Ham:

```python
create_competency_vector(scores: dict[str, float]) -> np.ndarray
```

Truoc day ham nay tao vector 6 chieu. Hien tai ham tao vector 10 chieu theo `COMPETENCY_DOMAINS`:

```python
[
    "sql",
    "analytics",
    "statistics",
    "visualization",
    "data_engineering",
    "big_data",
    "machine_learning",
    "deep_learning",
    "mlops",
    "programming",
]
```

Neu mot competency khong co trong dict dau vao, diem mac dinh la `0.0`.

### 7.2. Cap nhat vector nang luc

Ham:

```python
update_competency(
    current_vector: np.ndarray,
    new_scores: np.ndarray,
    learning_rate: float = 0.3,
) -> np.ndarray
```

Logic giu nguyen theo Exponential Moving Average:

```text
updated = (1 - learning_rate) * current_vector + learning_rate * new_scores
```

Sau do clip ve khoang 0-10.

Y nghia:

1. Diem moi co anh huong nhung khong ghi de hoan toan diem cu.
2. `learning_rate` cang cao thi diem moi anh huong cang manh.
3. Phu hop voi he thong danh gia lien tuc sau moi bai test/phong van.

### 7.3. Xac dinh competency yeu

Ham:

```python
identify_weak_domains(vector: np.ndarray, threshold: float = 5.0) -> list[str]
```

Ham tra ve cac competency co diem nho hon threshold.

Vi du:

```text
sql = 7.0 -> khong yeu
analytics = 3.0 -> yeu
data_engineering = 2.0 -> yeu
```

## 8. Vi du luong hoat dong end-to-end

Gia su ung vien co vector:

```text
sql = 2.0
analytics = 8.0
statistics = 8.0
visualization = 8.0
data_engineering = 8.0
big_data = 8.0
machine_learning = 8.0
deep_learning = 8.0
mlops = 8.0
programming = 8.0
```

Nguoi dung goi:

```python
recommend_questions(vector, question_bank, num_recommendations=1)
```

He thong xu ly:

1. Duyet tung cau hoi.
2. Gap cau hoi co tag `SQL_JOIN`, map vao `sql`.
3. Diem `sql = 2.0`, nen `weak_priority = 0.8`.
4. `adaptive_difficulty(2.0)` tra ve `easy`.
5. Neu cau hoi SQL co `difficulty_score = 2`, do kho rat khop voi target `easy`.
6. Cau hoi SQL nhan diem goi y cao.
7. Cau hoi DS hard co `machine_learning = 8.0`, khong duoc uu tien trong che do focus diem yeu.
8. Ket qua tra ve cau hoi SQL.

## 9. Ket qua kiem thu

Da chay toan bo test suite bang lenh:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Ket qua:

```text
collected 8 items

tests\test_ai_core.py ....                                               [ 50%]
tests\test_core.py ....                                                  [100%]

8 passed
```

Nhung hanh vi da duoc test:

| Test | Muc dich |
| --- | --- |
| `test_recommend_questions_prioritizes_weak_domain` | Dam bao recommender uu tien competency yeu, vi du SQL diem thap thi goi y cau SQL. |
| `test_adaptive_difficulty` | Dam bao quy tac chon do kho easy/medium/hard va streak hoat dong dung. |
| `test_grade_answer_uses_local_fallback` | Dam bao cham diem fallback tra ve score, feedback, strengths, improvements hop le. |
| `test_generate_follow_up_fallback` | Dam bao fallback follow-up luon sinh cau hoi dang string. |
| `test_create_competency_vector` | Dam bao vector moi co 10 chieu va dung thu tu competency. |
| `test_identify_weak_domains` | Dam bao nhan dien dung competency yeu theo threshold. |

## 10. Diem manh cua thiet ke hien tai

1. Khop hon voi mock data hien co: recommender khong con ep data roles vao truc ky su phan mem.
2. Co kha nang giai thich ket qua: moi cau hoi tra ve co `recommendation_score`, `recommended_competency`, `target_difficulty`.
3. Chay duoc offline: grader co fallback local nen khong bat buoc co API key.
4. On dinh hon khi demo: neu Gemini loi, he thong khong crash.
5. De mo rong: chi can them hint vao `TAG_COMPETENCY_HINTS` khi mock data co tag moi.
6. Co unit test bao ve cac hanh vi quan trong.

## 11. Han che hien tai

1. Fallback grader chi cham theo keyword overlap, chua hieu ngu nghia sau nhu LLM.
2. Mapping tag sang competency dang dua tren rule-based hints, chua dung embedding hay semantic similarity.
3. Competency vector moi da duoc cap nhat trong core, nhung cac man hinh UI chua duoc tich hop day du voi recommender/grader.
4. `test_generator.py` hien van co dau hieu dung field cu `difficulty`, trong khi schema/mock data dung `difficulty_label` va `difficulty_score`; phan nay nen duoc sua trong dot tich hop tiep theo.
5. He thong chua co tracking lich su cau hoi da hoi, nen recommender co the lap lai cau hoi neu ben goi khong loc truoc.
6. Chua co trong so rieng theo target role. Vi du ung vien ung tuyen `DE` co the can uu tien `data_engineering` va `big_data` hon `analytics`.

## 12. De xuat cong viec tiep theo

1. Tich hop recommender vao UI Assessment/Interview de nguoi dung nhan cau hoi that tu mock data.
2. Sua `core/test_generator.py` de dung dung schema moi: `difficulty_label`, `difficulty_score`, `roles.primary`.
3. Them tham so `target_role` vao `recommend_questions()` de co role weighting rieng cho `DA`, `DE`, `DS`.
4. Them bo loc cau hoi da lam roi, tranh lap cau trong cung mot session.
5. Luu ket qua cham diem vao session/history, sau do cap nhat vector bang `update_competency()`.
6. Cai tien fallback grader bang semantic similarity local, vi du TF-IDF/cosine similarity hoac sentence embedding neu du an cho phep.
7. Viet integration test cho luong: load question bank -> recommend -> grade -> update competency -> recommend cau tiep theo.

## 13. Ket luan nghiem thu

Phan AI Core da duoc hoan thien o muc co the chay va kiem thu:

1. Thuat toan goi y cau hoi da duoc cai dat va dieu chinh dung voi mock data nhom nganh data.
2. He thong cham diem da co hai che do: LLM va fallback local.
3. Vector nang luc da duoc chuyen sang 10 competency phu hop voi `DA`, `DE`, `DS`.
4. Cac test hien tai deu pass.
5. Con mot so viec tich hop UI va generator nen thuc hien o dot tiep theo.

Trang thai: dat muc nghiem thu cho phan logic AI Core doc lap.
