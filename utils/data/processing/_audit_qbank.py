import json, os, re, sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

SKILL_GROUP_TO_COMPETENCY = {
    'SQL_DATABASE':'sql','SQL_FUNDAMENTALS':'sql','SQL_WINDOW_FUNCTION':'sql',
    'SQL_JOIN':'sql','SQL_AGGREGATION':'sql','SQL_PERFORMANCE':'sql','SQL_CTE':'sql',
    'STATISTICS_EXPERIMENTATION':'statistics','STAT_AB_TESTING':'statistics',
    'STAT_FUNDAMENTALS':'statistics','STAT_HYPOTHESIS_TESTING':'statistics',
    'STAT_CONFIDENCE_INTERVAL':'statistics',
    'ANALYTICS_COHORT':'analytics','ANALYTICS_FUNNEL':'analytics',
    'ANALYTICS_BUSINESS':'analytics','ANALYTICS_RFM':'analytics',
    'DATA_VISUALIZATION':'analytics','BI_CONCEPTS':'analytics','DAX_FUNDAMENTALS':'analytics',
    'TOOL_POWER_BI':'bi_tools','TOOL_TABLEAU':'bi_tools','DATABASE_DESIGN':'sql',
    'BI_VISUALIZATION':'bi_tools',
    'PYTHON_PANDAS':'python_da','PYTHON_ANALYTICS':'python_da',
    'ALGORITHM_THEORY':'machine_learning','ML_SUPERVISED':'machine_learning',
    'ML_UNSUPERVISED':'machine_learning','ML_REGULARIZATION':'machine_learning',
    'ML_RECOMMENDER_SYSTEM':'machine_learning','ML_ENSEMBLE':'machine_learning',
    'ML_DIMENSIONALITY_REDUCTION':'machine_learning','ML_ANOMALY_DETECTION':'machine_learning',
    'ML_EXPLAINABILITY':'machine_learning','ML_MODEL_SELECTION':'machine_learning',
    'DEEP_LEARNING':'deep_learning','DL_TRAINING':'deep_learning','DL_CNN':'deep_learning','DL_UNSUPERVISED':'deep_learning',
    'NLP':'nlp','NLP_PREPROCESSING':'nlp','NLP_EVALUATION':'nlp',
    'EVALUATION_METRICS':'evaluation','EVAL_CROSS_VALIDATION':'evaluation',
    'EVAL_CLASSIFICATION_REPORT':'evaluation','METRIC_F1_SCORE':'evaluation',
    'DATA_PREPROCESSING':'data_eng_ds','DATA_CLEANING':'data_eng_ds','FEATURE_ENGINEERING':'data_eng_ds',
    'ENCODING_TECHNIQUES':'data_eng_ds','IMBALANCED_DATA_HANDLING':'data_eng_ds',
    'LANG_PYTHON':'python_da',
    'TIME_SERIES':'mlops_ts','ML_TIME_SERIES':'mlops_ts','ML_MLOPS':'mlops_ts','ML_MONITORING':'mlops_ts',
    'BIG_DATA_CLOUD_TOOLS':'big_data','TOOL_SPARK':'big_data','TOOL_KAFKA':'big_data','TOOL_AIRFLOW':'big_data',
    'DATA_ARCHITECTURE_MODELING':'data_architecture','ARCH_DATA_ARCHITECTURE':'data_architecture',
    'ARCH_SYSTEM_DESIGN':'data_architecture','ARCH_STREAMING':'data_architecture',
    'DATA_WAREHOUSE':'data_architecture','MODELING_SCD':'data_architecture','MODELING_STAR_SCHEMA':'data_architecture',
    'DATABASE_INTERNALS':'databases','DATABASE_INDEXING':'databases','DATABASE_SCALING':'databases',
    'DATABASE_PERFORMANCE':'databases','DB_ACID':'databases',
    'DATA_PIPELINE':'pipelines','PIPE_CDC':'pipelines','PIPE_ELT':'pipelines','PIPE_ETL':'pipelines','PIPE_PERFORMANCE':'pipelines',
    'SYSTEM_ARCHITECTURE':'system','DEVOPS_DOCKER':'system',
    'CLOUD_AWS':'cloud_storage','CLOUD_GCP':'cloud_storage','CLOUD_S3':'cloud_storage',
    'FORMAT_AVRO':'cloud_storage','FORMAT_PARQUET':'cloud_storage',
}
ROLE_DEFAULT = {'DA':'sql','DS':'machine_learning','DE':'big_data'}

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def load_all():
    all_qs = []
    for path in ['data/raw/question_bank/question_bank.json','data/raw/question_bank/scraped/scraped_github.json',
                 'data/raw/question_bank/scraped/scraped_youssef.json','data/raw/question_bank/scraped/scraped_sql.json','data/raw/question_bank/scraped/converted_tf_fb.json']:
        fp = os.path.join(ROOT, path)
        if not os.path.exists(fp): continue
        with open(fp,'rb') as f: raw=f.read()
        try:
            data=json.loads(raw.rstrip(b'\x00').decode('utf-8'))
            all_qs.extend(data if isinstance(data,list) else data.get('questions',[]))
        except: pass
    de = os.path.join(ROOT, 'data/raw/question_bank/scraped/scraped_de.json')
    if os.path.exists(de):
        with open(de,'rb') as f: raw=f.read().decode('utf-8',errors='replace')
        ids=re.findall(r'"question_id":\s*"([^"]+)"',raw)
        roles=re.findall(r'"primary":\s*"(\w+)"',raw)
        diffs=re.findall(r'"difficulty_label":\s*"(\w+)"',raw)
        qtypes=re.findall(r'"question_type":\s*"(\w+)"',raw)
        groups=re.findall(r'"skill_groups":\s*\[\s*"(\w+)"',raw)
        n=min(len(ids),len(roles),len(diffs),len(qtypes),len(groups))
        for i in range(n):
            all_qs.append({'question_id':ids[i],'roles':{'primary':roles[i]},
                'difficulty_label':'HARD' if diffs[i]=='EXPERT' else diffs[i],
                'skill_groups':[groups[i]]})

    # Load generated files từ LLM
    gen_dir = os.path.join(ROOT, 'data/raw/question_bank/generated')
    for fname in sorted(os.listdir(gen_dir)):
        if fname.startswith('generated_') and fname.endswith('.json'):
            with open(os.path.join(gen_dir, fname), encoding='utf-8') as f:
                gen_qs = json.load(f)
            all_qs.extend(gen_qs)

    return all_qs

qs = load_all()
seen, unique = set(), []
for q in qs:
    k = q.get('question_id','')
    if k not in seen:
        seen.add(k); unique.append(q)

comp_diff = defaultdict(Counter)
for q in unique:
    role = q.get('roles',{}).get('primary','?')
    grp  = (q.get('skill_groups') or q.get('skill_tags') or ['?'])[0]
    comp = SKILL_GROUP_TO_COMPETENCY.get(grp, ROLE_DEFAULT.get(role,'unknown'))
    diff = q.get('difficulty_label','?')
    if diff == 'EXPERT': diff = 'HARD'
    comp_diff[f'{role}|{comp}'][diff] += 1

ROLE_COMPS = {
    'DA': ['sql','statistics','analytics','python_da','bi_tools'],
    'DS': ['machine_learning','deep_learning','nlp','evaluation','data_eng_ds','python_da','mlops_ts'],
    'DE': ['big_data','data_architecture','databases','pipelines','system','cloud_storage'],
}

# Target: 50 cau/competency (15E+25M+10H)
# Competency chu luc (>=80) giu nguyen, khong can sinh them
MIN_E, MIN_M, MIN_H = 15, 25, 10
TARGET = 50

print(f"{'Role':<4} | {'Competency':<22} | {'Hien co':>7} | {'Target':>6} | {'Can sinh':>8} | {'EASY':>4} | {'MED':>4} | {'HARD':>4} | Status")
print('-'*95)

total_gen = 0
plan = []  # for summary

for role, comps in ROLE_COMPS.items():
    for comp in comps:
        key = f'{role}|{comp}'
        c = comp_diff.get(key, Counter())
        cur = sum(c.values())
        tgt = max(TARGET, cur) if cur >= 80 else TARGET
        gap      = max(0, tgt - cur)
        e_gap    = max(0, MIN_E - c['EASY'])
        m_gap    = max(0, MIN_M - c['MEDIUM'])
        h_gap    = max(0, MIN_H - c['HARD'])
        # can sinh la max(gap, tong gap tung diff)
        need = max(gap, e_gap + m_gap + h_gap)

        if cur == 0:       status = '[URGENT] Khong co cau nao'
        elif cur < 15:     status = '[HIGH]   Qua it'
        elif cur < 30:     status = '[MEDIUM] Can them'
        elif need > 0:     status = '[LOW]    Thieu HARD/EASY'
        else:              status = '[OK]     Du'

        total_gen += need
        plan.append((role, comp, cur, tgt, need, e_gap, m_gap, h_gap, status))
        print(f"{role:<4} | {comp:<22} | {cur:>7} | {tgt:>6} | {need:>8} | {e_gap:>4} | {m_gap:>4} | {h_gap:>4} | {status}")
    print()

print(f"Tong cau can sinh them: {total_gen}")
print()
print("=== CHI TIET CAN SINH (bo qua OK) ===")
for role, comp, cur, tgt, need, eg, mg, hg, status in plan:
    if need > 0:
        print(f"  {role} / {comp}: can them {need} cau  (EASY+{eg}, MEDIUM+{mg}, HARD+{hg})")
