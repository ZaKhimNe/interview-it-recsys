// ============================================================
// screens-progress.jsx — Dashboard, Roadmap, History
// ============================================================

function DashboardScreen({ onNav }) {
  const { state, t, hl } = useStore();
  const vi = state.lang === 'vi';
  if (!state.role) return <EmptyState onNav={onNav} message="No role selected" />;
  const role = state.role;
  const color = roleColor(role);
  const axes = SKILL_AXES[role] || [];
  const rawCurrent = currentVector(state);
  const target = ROLE_TARGETS[role] || [];
  const n = axes.length;

  const hasAttempt = state.attempts.some(a => a.role === role);
  if (!hasAttempt || !rawCurrent) return (
    <div style={{ padding: '60px 32px', textAlign:'center' }}>
      <div className="mono" style={{ fontSize:10, color:'var(--fg-5)', letterSpacing:'.22em', textTransform:'uppercase', marginBottom:14 }}>
        {vi ? 'DASHBOARD · CHƯA CÓ DỮ LIỆU' : 'DASHBOARD · NO DATA YET'}
      </div>
      <div style={{ fontFamily:'var(--font-sans)', fontSize:28, fontWeight:950, textTransform:'uppercase', letterSpacing:'-.04em', color:'var(--fg-0)', marginBottom:12 }}>
        {vi ? 'Chưa có phiên đánh giá nào' : 'No assessments yet'}
      </div>
      <div className="muted" style={{ fontSize:14, marginBottom:28, maxWidth:480, margin:'0 auto 28px' }}>
        {vi ? 'Hoàn thành phiên phỏng vấn đầu tiên để xây dựng vector năng lực và mở khóa dashboard.' : 'Complete your first interview session to build your competency vector and unlock this dashboard.'}
      </div>
      <button className="btn primary" onClick={() => onNav('interview', { mode: 'quick' })}>
        {vi ? 'Bắt đầu đánh giá →' : 'Start assessment →'}
      </button>
    </div>
  );

  const current = rawCurrent;
  // Đảm bảo current và target cùng độ dài với axes
  const cur = axes.map((_, i) => current[i] ?? 0);
  const tgt = axes.map((_, i) => target[i] ?? 0);

  if (n === 0) return <EmptyState onNav={onNav} message="Chọn role trước" />;

  const gaps = cur.map((c, i) => c - tgt[i]);
  const critical = gaps.filter(d => d <= -2).length;
  const below = gaps.filter(d => d < -0.5 && d > -2).length;
  const locked = gaps.filter(d => d >= -0.5).length;
  const overall = (cur.reduce((a, b) => a + b, 0) / n).toFixed(1);
  const targetOverall = (tgt.reduce((a, b) => a + b, 0) / n).toFixed(1);

  return (
    <>
      <PageHead
        kicker={`${role} · ${t('dash.kicker')}`}
        title={t('dash.title')}
        right={[
          <button key="r" className="btn ghost compact" onClick={() => onNav('interview')}>↺ {state.lang === 'vi' ? 'Làm lại' : 'Retake'}</button>,
          <button key="e" className="btn ghost compact">↓ {t('common.export')}</button>,
          <button key="rm" className="btn primary compact" onClick={() => onNav('roadmap')}>{state.lang === 'vi' ? 'Xem lộ trình →' : 'View roadmap →'}</button>,
        ]}
      />
      <SpecStrip items={[
        <span key="r">ROLE: <span style={{ color }}>{state.role === 'DA' ? 'Data Analyst' : state.role === 'DE' ? 'Data Engineer' : 'Data Scientist'}</span></span>,
        `${state.completedQs.length} answers`,
        `${n} ${vi ? 'trục' : 'axes'}`,
        vi ? 'Cập nhật: 2 phút trước' : 'Last update: 2 min ago',
        <span key="s" className="cyan">{vi ? 'SPACED REP BẬT' : 'SPACED REP ACTIVE'}</span>,
      ]} />

      <div className="split-4" style={{ marginBottom: 24 }}>
        <div className="metric info" style={{ '--m-color': color }}>
          <div className="k">{t('dash.metricOverall')}</div>
          <div className="v">{overall}<span className="unit">/ {targetOverall}</span></div>
          <div className="delta">{t('dash.vsTarget')} {(parseFloat(overall) - parseFloat(targetOverall)).toFixed(1)}</div>
        </div>
        <div className="metric good">
          <div className="k">{t('dash.metricLocked')}</div>
          <div className="v">{locked}<span className="unit">/ {n}</span></div>
          <div className="delta">{vi ? 'ĐẠT MỤC TIÊU' : 'AT OR ABOVE TARGET'}</div>
        </div>
        <div className="metric warn">
          <div className="k">{t('dash.metricBelow')}</div>
          <div className="v">{below}<span className="unit">/ {n}</span></div>
          <div className="delta">{vi ? 'CẦN LUYỆN THÊM' : 'NEEDS PRACTICE'}</div>
        </div>
        <div className="metric bad">
          <div className="k">{t('dash.metricCritical')}</div>
          <div className="v">{critical}<span className="unit">/ {n}</span></div>
          <div className="delta">{vi ? 'ƯU TIÊN NGAY' : 'PRIORITY FOCUS'}</div>
        </div>
      </div>

      <div className="split-2" style={{ alignItems:'start', marginBottom: 22 }}>
        <div className="card raised role-top" style={{ '--role-color': color }}>
          <div className="row between" style={{ marginBottom: 8 }}>
            <h2>{t('dash.vector')}</h2>
            <div className="row" style={{ gap: 12 }}>
              <span className="mono" style={{ fontSize: 10, letterSpacing:'.12em', display:'inline-flex', alignItems:'center', gap: 6 }}><span style={{ width: 10, height: 10, background: color, borderRadius:'50%', boxShadow:`0 0 8px ${color}` }}></span>{t('dash.legendCur')}</span>
              <span className="mono" style={{ fontSize: 10, letterSpacing:'.12em', display:'inline-flex', alignItems:'center', gap: 6 }}><span style={{ width: 10, height: 10, background:'#ff3366', borderRadius:'50%', boxShadow:'0 0 8px #ff3366' }}></span>{t('dash.legendTgt')}</span>
            </div>
          </div>
          <RadarChart axes={axes} current={cur} target={tgt} color={color} size={420} />
          <div className="mono muted" style={{ fontSize: 11, textAlign:'center', letterSpacing:'.14em', textTransform:'uppercase', marginTop: 8 }}>
            {state.lang === 'vi' ? 'Hover một trục để highlight gap + lộ trình tương ứng' : 'Hover an axis to highlight matching gap + roadmap step'}
          </div>
        </div>
        <div className="card hot-top">
          <h2>{t('dash.gaps')}</h2>
          <GapList skills={axes} current={cur} target={tgt} roleColor={color}
                   onPracticeSkill={(i, label) => onNav('interview', { skill: label })} />
        </div>
      </div>

    </>
  );
}

// ============================================================
// ROADMAP
// ============================================================
// ── KT Pipeline helpers (dùng chung với KTDemoScreen) ──────────────────────
const KT_DEMO_EVENTS = {
  DA: [
    { kc:'SQL_DATABASE',               correct:true,  score:0.85, q:'Explain the difference between RANK() and DENSE_RANK().', type:'MC_SINGLE' },
    { kc:'BI_VISUALIZATION',           correct:false, score:0.30, q:'When should you use a scatter plot vs. a bar chart?', type:'THEORY' },
    { kc:'STATISTICS_EXPERIMENTATION', correct:true,  score:0.80, q:'What is a p-value and what are its limitations?', type:'PRACTICE' },
    { kc:'ANALYTICS_BUSINESS',         correct:false, score:0.40, q:'How do you build a cohort retention analysis?', type:'THEORY' },
    { kc:'PYTHON_ANALYTICS',           correct:true,  score:0.75, q:'Explain pandas groupby + agg pipeline.', type:'PRACTICE' },
    { kc:'SQL_DATABASE',               correct:true,  score:0.90, q:'[ADAPTIVE] Write a query using window functions to find running totals.', type:'PRACTICE' },
    { kc:'BI_VISUALIZATION',           correct:true,  score:0.65, q:'[ADAPTIVE] What makes a dashboard actionable vs. decorative?', type:'THEORY' },
  ],
  DS: [
    { kc:'ALGORITHM_THEORY',    correct:true,  score:0.85, q:'Explain the difference between bagging and boosting.', type:'THEORY' },
    { kc:'EVALUATION_METRICS',  correct:false, score:0.30, q:'When should you use F1-score vs ROC-AUC?', type:'MC_SINGLE' },
    { kc:'DATA_PREPROCESSING',  correct:true,  score:0.90, q:'How do you handle high-cardinality categorical features?', type:'PRACTICE' },
    { kc:'DEEP_LEARNING',       correct:false, score:0.40, q:'What are the problems with sigmoid as an activation function?', type:'TRUE_FALSE' },
    { kc:'NLP',                 correct:true,  score:0.75, q:'Explain attention mechanism in transformers.', type:'THEORY' },
    { kc:'TIME_SERIES',         correct:false, score:0.20, q:'What is stationarity and why does it matter?', type:'MC_SINGLE' },
    { kc:'MLOPS',               correct:true,  score:0.80, q:'What is model drift and how do you detect it?', type:'PRACTICE' },
    { kc:'EVALUATION_METRICS',  correct:true,  score:0.65, q:'[ADAPTIVE] Calculate precision & recall from a confusion matrix.', type:'PRACTICE' },
    { kc:'DEEP_LEARNING',       correct:true,  score:0.70, q:'[ADAPTIVE] Why use ReLU instead of sigmoid in hidden layers?', type:'THEORY' },
    { kc:'TIME_SERIES',         correct:false, score:0.35, q:'[ADAPTIVE] Explain ARIMA model components.', type:'THEORY' },
  ],
  DE: [
    { kc:'DATA_PIPELINE',              correct:true,  score:0.80, q:'Explain the difference between ETL and ELT.', type:'THEORY' },
    { kc:'DATA_ARCHITECTURE_MODELING', correct:false, score:0.35, q:'When would you use a data lake vs. data warehouse?', type:'MC_SINGLE' },
    { kc:'BIG_DATA_CLOUD_TOOLS',       correct:true,  score:0.75, q:'Explain Spark\'s lazy evaluation and DAG execution.', type:'PRACTICE' },
    { kc:'DATABASE_INTERNALS',         correct:false, score:0.40, q:'How does a B-tree index work?', type:'THEORY' },
    { kc:'SYSTEM_ARCHITECTURE',        correct:true,  score:0.85, q:'Design a real-time data pipeline for 1M events/sec.', type:'PRACTICE' },
    { kc:'DATA_PIPELINE',              correct:true,  score:0.70, q:'[ADAPTIVE] How do you handle late-arriving data in streaming?', type:'PRACTICE' },
    { kc:'DATABASE_INTERNALS',         correct:true,  score:0.65, q:'[ADAPTIVE] Explain write-ahead logging (WAL).', type:'THEORY' },
  ],
};

function ktUpdate(sv, kc, score, histLen) {
  const prior = sv[kc] != null ? sv[kc] : 0.3;
  const lr = Math.min(0.4, 0.15 + histLen * 0.02);
  const target = score > 0.6 ? Math.min(prior + lr * (1 - prior), 0.98)
                              : Math.max(prior - lr * prior, 0.02);
  const obs = score > 0.5 ? 0.9 : 0.1;
  const post = (obs * target) / (obs * target + (1-obs)*(1-target));
  return Math.round(post * 100) / 100;
}
function emaKT(sv, kc, score) {
  const alpha = 0.35, cur = sv[kc] != null ? sv[kc] : 0.3;
  return Math.round((alpha * score + (1-alpha) * cur) * 100) / 100;
}
function blendKT(kt, ema) { return Math.round((0.7*kt + 0.3*ema) * 100) / 100; }

function RoadmapScreen({ onNav }) {
  const { state } = useStore();
  const role = state.role || 'DS';
  const vi   = state.lang === 'vi';
  const color = roleColor(role);
  const kcs   = SKILL_KEYS[role] || [];

  // Nguon du lieu: attempt MST da luu (ben vung qua dieu huong / reset)
  const mstAttempt = React.useMemo(() => {
    const a = (state.attempts || []).filter(x => x.role === role && x.source === 'MST' && x.results && x.results.length);
    return a.length ? a[a.length - 1] : null;
  }, [role, state.attempts]);

  const realEvents = React.useMemo(() => {
    const dataAll = (window.__INTERNHUB_DATA__ && window.__INTERNHUB_DATA__.questions) || QUESTIONS || [];
    const build = (results, s1Len) => results.map((r, i) => {
      const q = dataAll.find(x => x.id === r.qId) || {};
      const groups = r.groups || q.skillGroups || q.skill_groups || [];
      const kc = groups.find(g => kcs.includes(g)) || groups[0] || kcs[i % kcs.length];
      return {
        kc, score: r.score, correct: r.isCorrect != null ? r.isCorrect : (r.score >= 0.5),
        q: `${i >= s1Len ? '[ADAPTIVE] ' : ''}${q.title_en || q.title_vi || r.qId}`,
        type: q.questionType || 'THEORY',
      };
    });
    // 1) Attempt da luu (uu tien)
    if (mstAttempt) return build(mstAttempt.results, mstAttempt.s1Len || 0);
    // 2) Fallback: phien MST con song trong state
    const mst = state.mst || {};
    if (!mst.done) return null;
    const allResults = [...(mst.s1Results||[]), ...(mst.s2Results||[])];
    if (!allResults.length) return null;
    return build(allResults, (mst.s1Results||[]).length);
  }, [mstAttempt, state.mst && state.mst.done, role]);

  // Khong co du lieu -> empty state
  if (!realEvents) return (
    <div style={{ padding:'60px 32px', textAlign:'center' }}>
      <div className="mono" style={{ fontSize:10, color:'var(--fg-5)', letterSpacing:'.22em', textTransform:'uppercase', marginBottom:14 }}>
        {vi ? 'KT MODEL · CHƯA CÓ DỮ LIỆU' : 'KT MODEL · NO DATA YET'}
      </div>
      <div style={{ fontFamily:'var(--font-sans)', fontSize:28, fontWeight:950, textTransform:'uppercase', letterSpacing:'-.04em', color:'var(--fg-0)', marginBottom:12 }}>
        {vi ? 'Chưa có phiên đánh giá nào' : 'No assessment data yet'}
      </div>
      <div className="muted" style={{ fontSize:14, marginBottom:28, maxWidth:520, margin:'0 auto 28px' }}>
        {vi
          ? 'Hoàn thành phiên Diagnostic (7 câu Stage 1 + 3 câu adaptive Stage 2) để xem KT pipeline với dữ liệu thực của bạn — EMA, DKT, Blend, và lộ trình cá nhân hóa.'
          : 'Complete your Diagnostic session (7 Stage 1 questions + 3 adaptive Stage 2) to see the KT pipeline run on your real answers — EMA, DKT, Blend, and your personalized roadmap.'}
      </div>
      <button className="btn primary" onClick={() => onNav('interview', { mode: 'diagnostic' })}>
        {vi ? 'Bắt đầu đánh giá →' : 'Start diagnostic →'}
      </button>
    </div>
  );

  const events = realEvents;
  const stage1Count = (mstAttempt && mstAttempt.s1Len != null) ? mstAttempt.s1Len : (state.mst?.s1Results||[]).length;

  // Baseline = vector cua attempt NGAY TRUOC attempt MST nay (0-10 -> 0-1)
  const realVec = React.useMemo(() => {
    const same = (state.attempts || []).filter(a => a.role === role);
    const idx = mstAttempt ? same.indexOf(mstAttempt) : same.length;
    const prev = idx > 0 ? same[idx - 1] : null;
    const vec = prev && prev.vector;
    if (!vec || !vec.length) return null;
    return Object.fromEntries(kcs.map((k, i) => [k, Math.min(1, (vec[i] ?? 3) / 10)]));
  }, [role, state.attempts, mstAttempt]);

  const baseSV = realVec || Object.fromEntries(kcs.map(k => [k, 0.3]));
  // Ket qua KT cuoi cung — dung CHUNG mstSkillVector -> TRUNG KHOP Dashboard
  const finalKt = React.useMemo(() => mstSkillVector(role, events, realVec), [events, role]);

  const [step, setStep]     = React.useState(events.length);
  const [emaSV, setEma]     = React.useState(() => finalKt.ema);
  const [ktSV, setKt]       = React.useState(() => finalKt.kt);
  const [blendSV, setBlend] = React.useState(() => finalKt.blend);
  const [history, setHist]  = React.useState(() => events.map(e => ({ kc: e.kc, score: e.score })));
  const [pipeActive, setPipe] = React.useState(-1);
  const [done, setDone]     = React.useState(true);

  const pipeSteps = ['Input','EMA','DKT','Blend','Skill','Recommend'];

  const advance = () => {
    if (step >= events.length) return;
    const ev = events[step];
    const kc = ev.kc;
    const newHist = [...history, { kc, score: ev.score }];
    setHist(newHist);

    const newEma = { ...emaSV, [kc]: emaKT(emaSV, kc, ev.score) };
    const newKt  = { ...ktSV,  [kc]: newHist.length >= 3 ? ktUpdate(ktSV, kc, ev.score, newHist.length) : newEma[kc] };
    const newBlend = { ...blendSV, [kc]: blendKT(newKt[kc], newEma[kc]) };

    setEma(newEma); setKt(newKt); setBlend(newBlend);

    setPipe(0);
    [1,2,3,4,5].forEach(i => setTimeout(() => setPipe(i), i*180));
    setTimeout(() => setPipe(-1), 1200);

    const ns = step + 1;
    setStep(ns);
    if (ns >= events.length) setDone(true);
  };

  const reset = () => {
    setStep(0); setHist([]);
    setEma(baseSV); setKt(baseSV); setBlend(baseSV);
    setPipe(-1); setDone(false);
  };

  const avg = Object.values(blendSV).reduce((s,v)=>s+v,0) / (Object.keys(blendSV).length||1);
  const routing = avg >= 0.7 ? 'STRONG' : avg >= 0.45 ? 'MID' : 'WEAK';
  const routingColor = routing==='STRONG'?'var(--success)':routing==='MID'?'var(--accent-warn)':'var(--danger)';
  const weakKCs = kcs.filter(k => blendSV[k] < 0.5);

  return (
    <>
      <PageHead
        kicker={vi ? 'MÔ HÌNH KT · KNOWLEDGE TRACING' : 'KT MODEL · KNOWLEDGE TRACING'}
        title={vi ? 'Pipeline hoạt động như nào' : 'How the pipeline works'}
        right={[<button key="b" className="btn ghost compact" onClick={() => onNav('dashboard')}>← Dashboard</button>]}
      />

      {/* Pipeline diagram */}
      <div style={{ display:'flex', alignItems:'center', gap:4, flexWrap:'wrap', marginBottom:20 }}>
        {pipeSteps.map((p,i) => (
          <React.Fragment key={i}>
            <div style={{
              padding:'7px 12px', borderRadius:5, fontSize:11, fontFamily:'var(--font-mono)',
              border:`1px solid ${pipeActive===i?'var(--accent-cyan)':'rgba(244,244,245,.1)'}`,
              color: pipeActive===i?'var(--accent-cyan)':'var(--fg-4)',
              boxShadow: pipeActive===i?'0 0 10px rgba(0,229,255,.2)':'none',
              transition:'all .15s', textAlign:'center',
            }}>
              <div>{p}</div>
              <div style={{ fontSize:9, color:'var(--fg-6)', marginTop:2 }}>
                {['KC+score','luôn chạy','≥3 history','KT·70% EMA·30%','ghi profile','gợi ý câu'][i]}
              </div>
            </div>
            {i < pipeSteps.length-1 && <span style={{ color:'var(--fg-6)', fontSize:14 }}>→</span>}
          </React.Fragment>
        ))}
      </div>

      {/* Controls */}
      <div style={{ display:'flex', gap:8, alignItems:'center', marginBottom:20 }}>
        <button
          className="btn role"
          style={{ '--role-color': color, borderColor: color, color, opacity: done?0.4:1 }}
          onClick={advance} disabled={done}
        >
          ▶ {vi ? 'Câu tiếp theo' : 'Next question'}
        </button>
        <button className="btn ghost compact" onClick={reset}>↺ Reset</button>
        <span style={{ fontSize:11, color:'var(--fg-5)', fontFamily:'var(--font-mono)' }}>
          {step > 0
            ? `${vi?'Câu':'Q'} ${step}/${events.length} · KC: ${events[Math.min(step,events.length)-1].kc.replace(/_/g,' ')} · ${events[Math.min(step,events.length)-1].correct?'✓':'✗'} · method: ${history.length>=3?'KT·blend':'EMA only'}`
            : (vi ? 'Bấm ▶ để bắt đầu mô phỏng' : 'Press ▶ to start simulation')}
        </span>
      </div>

      {/* Radar nang luc — dong bo voi Dashboard (cung vector blend) */}
      <div style={{ display:'grid', gridTemplateColumns:'minmax(0,1fr) 300px', gap:16, alignItems:'start', marginBottom:16 }}>
        <div className="card raised role-top" style={{ '--role-color':color }}>
          <h3 style={{ marginBottom:6 }}>{vi ? 'VECTOR NANG LUC (KT)' : 'COMPETENCY VECTOR (KT)'}</h3>
          <div className="muted" style={{ fontSize:12, marginBottom:8 }}>
            {vi ? 'Ket qua blend EMA+DKT — khop voi Dashboard radar' : 'Blended EMA+DKT result — matches the Dashboard radar'}
          </div>
          <div style={{ display:'flex', justifyContent:'center' }}>
            <RadarChart axes={SKILL_AXES[role]||[]} current={kcs.map(k => Math.round((blendSV[k]||0)*100)/10)} target={ROLE_TARGETS[role]||[]} color={color} size={360} />
          </div>
        </div>
        <div className="card">
          <h3 style={{ marginBottom:10 }}>{vi ? 'TONG QUAN' : 'SUMMARY'}</h3>
          <div style={{ fontFamily:'var(--font-mono)', fontSize:13, lineHeight:1.9 }}>
            <div>{vi?'Diem TB':'Overall'}: <strong style={{ color:routingColor }}>{(avg*10).toFixed(1)}/10</strong></div>
            <div>{vi?'Phan loai':'Routing'}: <strong style={{ color:routingColor }}>{routing}</strong></div>
            <div>{vi?'So cau':'Questions'}: {events.length} <span style={{color:'var(--fg-5)'}}>({stage1Count} S1 + {events.length-stage1Count} S2)</span></div>
          </div>
          <div style={{ marginTop:10, paddingTop:10, borderTop:'1px solid var(--line)', color:'var(--fg-5)', fontSize:11, lineHeight:1.6 }}>
            {vi?'KC can luyen':'Weak KCs'}: {weakKCs.length ? weakKCs.map(k=>k.replace(/_/g,' ')).join(', ') : (vi?'khong co — tot!':'none — nice!')}
          </div>
        </div>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, alignItems:'start' }}>
        {/* LEFT — skill bars */}
        <div className="card">
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12 }}>
            <h3 style={{ color:'var(--fg-4)', fontSize:10, letterSpacing:'.14em', textTransform:'uppercase', fontFamily:'var(--font-mono)' }}>
              {vi ? 'SKILL MASTERY' : 'SKILL MASTERY'} · {role}
            </h3>
            <div style={{ display:'flex', gap:10, fontSize:10, fontFamily:'var(--font-mono)', color:'var(--fg-5)' }}>
              <span style={{ display:'flex', alignItems:'center', gap:4 }}>
                <span style={{ width:12, height:7, background:'rgba(0,229,255,.3)', display:'inline-block', borderRadius:2 }}></span> EMA
              </span>
              <span style={{ display:'flex', alignItems:'center', gap:4 }}>
                <span style={{ width:12, height:4, background:'var(--accent-cyan)', display:'inline-block', borderRadius:2 }}></span> DKT
              </span>
            </div>
          </div>
          {kcs.map(kc => (
            <div key={kc} style={{ display:'flex', alignItems:'center', gap:8, marginBottom:8 }}>
              <div style={{ fontSize:10, color:'var(--fg-4)', width:130, flexShrink:0, fontFamily:'var(--font-mono)' }}>
                {kc.replace(/_/g,' ')}
              </div>
              <div style={{ flex:1, height:12, background:'var(--bg-3)', borderRadius:4, overflow:'hidden', position:'relative' }}>
                <div style={{ height:'100%', width:`${Math.round((emaSV[kc]||0.3)*100)}%`, background:'rgba(0,229,255,.3)', borderRadius:4, transition:'width .6s cubic-bezier(.22,1,.36,1)' }} />
                <div style={{ position:'absolute', top:3, left:0, height:6, width:`${Math.round((ktSV[kc]||0.3)*100)}%`, background:'var(--accent-cyan)', borderRadius:4, transition:'width .6s cubic-bezier(.22,1,.36,1)' }} />
              </div>
              <div style={{ fontSize:10, fontFamily:'var(--font-mono)', width:36, textAlign:'right',
                color: blendSV[kc]>=0.7?'var(--success)': blendSV[kc]>=0.5?'var(--accent-warn)':'var(--danger)' }}>
                {((blendSV[kc]||0.3)*10).toFixed(1)}
              </div>
            </div>
          ))}

          {done && (
            <div style={{ marginTop:14, padding:10, borderRadius:6, border:`1px solid ${routingColor}`, fontFamily:'var(--font-mono)', fontSize:12 }}>
              <div style={{ color: routingColor, marginBottom:4 }}>
                {vi?'Routing':'Routing'}: <strong>{routing}</strong>
                <span style={{ color:'var(--fg-5)', marginLeft:8 }}>avg {(avg*10).toFixed(1)}/10</span>
              </div>
              {weakKCs.length > 0 && (
                <div style={{ color:'var(--fg-5)', fontSize:10 }}>
                  {vi?'KCs yếu →':'Weak KCs →'} {weakKCs.map(k=>k.replace(/_/g,' ')).join(', ')}
                </div>
              )}
              <div style={{ color:'var(--fg-6)', fontSize:10, marginTop:4 }}>
                {vi?'Recommender sẽ ưu tiên các KC yếu này':'Recommender will prioritize these weak KCs'}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT — event timeline */}
        <div className="card">
          <h3 style={{ color:'var(--fg-4)', fontSize:10, letterSpacing:'.14em', textTransform:'uppercase', fontFamily:'var(--font-mono)', marginBottom:12 }}>
            {vi?'CHUỖI CÂU HỎI':'QUESTION SEQUENCE'} · <span style={{color:'var(--success)'}}>YOUR RESULTS</span>
            <span style={{fontWeight:400,marginLeft:8}}>(Stage 1: {stage1Count}q + Stage 2: {events.length-stage1Count}q adaptive)</span>
          </h3>
          <div style={{ display:'flex', flexDirection:'column', gap:6, maxHeight:400, overflowY:'auto' }}>
            {events.map((ev, i) => (
              <div key={i} style={{
                display:'flex', alignItems:'flex-start', gap:10, padding:'7px 10px',
                borderRadius:6, background:'var(--bg-3)',
                borderLeft:`2px solid ${i < step ? (ev.correct?'var(--success)':'var(--danger)') : 'var(--fg-6)'}`,
                opacity: i < step ? 1 : 0.35,
                transition: 'opacity .3s, border-color .3s',
              }}>
                <div style={{ width:7, height:7, borderRadius:'50%', flexShrink:0, marginTop:4,
                  background: i < step ? (ev.correct?'var(--success)':'var(--danger)') : 'var(--fg-6)' }} />
                <div style={{ flex:1 }}>
                  <div style={{ fontSize:10, color:'var(--accent-cyan)', fontFamily:'var(--font-mono)', marginBottom:2 }}>
                    {ev.kc.replace(/_/g,' ')} · {ev.type}{ev.q.startsWith('[ADAPTIVE]')?' · ADAPTIVE':''}
                  </div>
                  <div style={{ fontSize:12, color:'var(--fg-2)', lineHeight:1.4 }}>{ev.q.replace('[ADAPTIVE] ','')}</div>
                  {i < step && (
                    <div style={{ fontSize:10, color:'var(--fg-5)', fontFamily:'var(--font-mono)', marginTop:3 }}>
                      score {(ev.score*10).toFixed(1)}/10 · {i>=2?'KT·blend':'EMA only'} · blend → {((blendSV[ev.kc]||0)*10).toFixed(1)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

// ============================================================
// HISTORY — radar overlay + delta line + session timeline
// ============================================================
function HistoryScreen({ onNav }) {
  const { state, t } = useStore();
  if (!state.role) return <EmptyState onNav={onNav} message="No role selected" />;
  const vi = state.lang === 'vi';
  const role = state.role;
  const color = roleColor(role);
  const attempts = state.attempts.filter(a => a.role === role);

  if (attempts.length === 0) return (
    <div style={{ padding: '60px 32px', textAlign:'center' }}>
      <div className="mono" style={{ fontSize:10, color:'var(--fg-5)', letterSpacing:'.22em', textTransform:'uppercase', marginBottom:14 }}>
        {vi ? 'LỊCH SỬ · CHƯA CÓ DỮ LIỆU' : 'HISTORY · NO DATA YET'}
      </div>
      <div style={{ fontFamily:'var(--font-sans)', fontSize:28, fontWeight:950, textTransform:'uppercase', letterSpacing:'-.04em', color:'var(--fg-0)', marginBottom:12 }}>
        {vi ? 'Chưa có phiên nào được ghi lại' : 'No sessions recorded yet'}
      </div>
      <div className="muted" style={{ fontSize:14, marginBottom:28, maxWidth:480, margin:'0 auto 28px' }}>
        {vi ? 'Mỗi lần submit câu trả lời sẽ tạo một điểm dữ liệu trong lịch sử. Trajectory và radar overlay sẽ xuất hiện ở đây.' : 'Each submitted answer creates a data point in history. Trajectory and radar overlay will appear here.'}
      </div>
      <button className="btn primary" onClick={() => onNav('interview', { mode: 'quick' })}>
        {vi ? 'Bắt đầu phiên đầu tiên →' : 'Start first session →'}
      </button>
    </div>
  );
  const axes = SKILL_AXES[role];
  const target = ROLE_TARGETS[role];

  // Line chart of overall over time
  const overallSeries = attempts.map(a => a.vector.reduce((x,y) => x+y, 0) / a.vector.length);
  const tgtOverall = target.reduce((a,b)=>a+b,0)/target.length;
  const W = 520, H = 180, pad = 32;
  const xStep = (W - pad*2) / Math.max(1, attempts.length - 1);
  const yMax = 10, yMin = 0;
  const yPos = (v) => H - pad - ((v - yMin) / (yMax - yMin)) * (H - pad*2);
  const path = overallSeries.map((v, i) => `${i === 0 ? 'M' : 'L'} ${pad + i*xStep} ${yPos(v)}`).join(' ');

  return (
    <>
      <PageHead
        kicker={`${role} · ${t('history.kicker')}`}
        title={t('history.title')}
        right={[<button key="r" className="btn ghost compact" onClick={() => onNav('dashboard')}>← Dashboard</button>]}
      />
      <SpecStrip items={[
        `${attempts.length} assessments`,
        `${attempts[0]?.date || '—'} → ${attempts.at(-1)?.date || '—'}`,
        <span key="d" className="cyan">{t('history.delta')} {(overallSeries.at(-1) - overallSeries[0]).toFixed(1)}</span>,
      ]} />
      <div className="muted" style={{ marginBottom: 22, maxWidth: 720, fontSize: 14 }}>{t('history.sub')}</div>

      <div className="split-2" style={{ alignItems:'start', marginBottom: 22 }}>
        <div className="card raised role-top" style={{ '--role-color': color }}>
          <h2>{state.lang === 'vi' ? 'OVERLAY RADAR' : 'RADAR OVERLAY'}</h2>
          <div className="muted" style={{ fontSize: 12, marginBottom: 10 }}>{state.lang === 'vi' ? 'Đường mờ hơn = lần đánh giá cũ hơn. Đường tươi nhất = hiện tại.' : 'Fainter polygon = older attempt. Brightest = current.'}</div>
          <div style={{ display:'flex', justifyContent:'center' }}>
            <HistoryOverlay attempts={attempts} axes={axes} target={target} role={role} />
          </div>
        </div>
        <div className="card">
          <h2>{state.lang === 'vi' ? 'TRAJECTORY' : 'OVERALL TRAJECTORY'}</h2>
          <div className="muted" style={{ fontSize: 12, marginBottom: 10 }}>{state.lang === 'vi' ? 'Điểm trung bình 6 trục theo thời gian' : '6-axis average over time'}</div>
          <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ display:'block', margin:'0 auto' }}>
            {/* grid */}
            {[2,4,6,8,10].map(v => (
              <g key={v}>
                <line x1={pad} y1={yPos(v)} x2={W-pad} y2={yPos(v)} stroke="rgba(244,244,245,.06)" />
                <text x={6} y={yPos(v)+3} fill="var(--fg-6)" fontFamily="JetBrains Mono, monospace" fontSize="9">{v}</text>
              </g>
            ))}
            {/* target line */}
            <line x1={pad} y1={yPos(tgtOverall)} x2={W-pad} y2={yPos(tgtOverall)} stroke="#ff3366" strokeWidth="1.5" strokeDasharray="4 4" />
            <text x={W-pad-6} y={yPos(tgtOverall)-5} fill="#ff3366" fontFamily="JetBrains Mono, monospace" fontSize="9" textAnchor="end">TARGET {tgtOverall.toFixed(1)}</text>
            {/* path */}
            <path d={path} fill="none" stroke={color} strokeWidth="2.5" />
            {/* dots */}
            {overallSeries.map((v, i) => (
              <circle key={i} cx={pad + i*xStep} cy={yPos(v)} r="4" fill={color} stroke="#05080d" strokeWidth="1.5" />
            ))}
            {/* x labels */}
            {attempts.map((a, i) => (
              <text key={i} x={pad + i*xStep} y={H-8} fill="var(--fg-5)" fontFamily="JetBrains Mono, monospace" fontSize="9" textAnchor="middle">{a.date.slice(5)}</text>
            ))}
          </svg>
          <div className="row between" style={{ marginTop: 14, fontSize: 12 }}>
            <span className="mono muted">START</span>
            <span className="mono cyan">{overallSeries[0].toFixed(1)}</span>
            <span className="mono muted">→</span>
            <span className="mono cyan">{overallSeries.at(-1).toFixed(1)}</span>
            <span className="mono" style={{ color:'var(--success)' }}>Δ +{(overallSeries.at(-1)-overallSeries[0]).toFixed(1)}</span>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>{state.lang === 'vi' ? 'TIMELINE PHIÊN' : 'SESSION TIMELINE'}</h2>
        <div className="timeline">
          {[...attempts].reverse().map((a, i, arr) => {
            const overall = (a.vector.reduce((x,y)=>x+y,0)/a.vector.length).toFixed(1);
            const prev = arr[i+1];
            const delta = prev ? overall - (prev.vector.reduce((x,y)=>x+y,0)/prev.vector.length) : null;
            return (
              <div key={a.id} className="timeline-item" style={{ '--role-color': color }}>
                <div className="ti-when">{a.date}</div>
                <div className="ti-title">{state.lang === 'vi' ? `Đánh giá #${attempts.length - i}` : `Assessment #${attempts.length - i}`}</div>
                <div className="row" style={{ gap: 14 }}>
                  <span className="mono" style={{ fontSize: 13, color }}>{overall} / 10</span>
                  {delta != null && <span className={`ti-delta ${delta < 0 ? 'neg' : ''}`} >Δ {delta > 0 ? '+' : ''}{delta.toFixed(1)}</span>}
                  {i === 0 && <span className="chip good">LATEST</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}

Object.assign(window, { DashboardScreen, RoadmapScreen, HistoryScreen });
