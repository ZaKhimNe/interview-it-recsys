// ============================================================
// widgets.jsx — interactive, cross-connected widgets.
// Hover a radar axis → gap row + roadmap step highlight together.
// ============================================================

// ---------------- RADAR ----------------------------------------
function RadarChart({ axes, current, target, color = '#00e5ff', size = 400, onSkillHover }) {
  const { hl, setHl } = useStore();
  const N = axes.length;
  const cx = size / 2, cy = size / 2;
  const R = size * 0.38;
  const angle = (i) => (-Math.PI / 2) + (i * 2 * Math.PI / N);
  const point = (r, i) => [cx + r * Math.cos(angle(i)), cy + r * Math.sin(angle(i))];
  const polygon = (vec) => vec.map((v, i) => point((v / 10) * R, i).join(',')).join(' ');
  const labelPoint = (i) => point(R + 26, i);
  const rings = [0.25, 0.5, 0.75, 1].map(f => Array.from({ length: N }, (_, i) => point(f * R, i).join(',')).join(' '));

  const hover = (i) => { setHl(s => ({ ...s, skillIdx: i })); if (onSkillHover) onSkillHover(i); };
  const leave = () => setHl(s => ({ ...s, skillIdx: null }));

  return (
    <div className="radar-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* concentric grid */}
        {rings.map((pts, i) => (
          <polygon key={i} points={pts} fill="none" stroke="rgba(244,244,245,.10)" strokeWidth="1" />
        ))}
        {/* axes */}
        {Array.from({ length: N }, (_, i) => {
          const [x, y] = point(R, i);
          const isHl = hl.skillIdx === i;
          return <line key={i} x1={cx} y1={cy} x2={x} y2={y}
            stroke={isHl ? '#fde047' : 'rgba(244,244,245,.16)'} strokeWidth={isHl ? '1.5' : '1'} />;
        })}
        {/* target (hot pink, dashed) */}
        <polygon points={polygon(target)} fill="rgba(255,51,102,.10)" stroke="#ff3366" strokeWidth="1.5" strokeDasharray="4 4" />
        {/* current */}
        <polygon points={polygon(current)} style={{ fill: `${color}30` }} stroke={color} strokeWidth="2" />
        {/* dots */}
        {current.map((v, i) => {
          const [x, y] = point((v / 10) * R, i);
          const isHl = hl.skillIdx === i;
          return <circle key={i} cx={x} cy={y} r={isHl ? 6 : 3.5} fill={color} stroke="#05080d" strokeWidth="1.5" style={{ transition: 'r .15s ease' }} />;
        })}
        {/* invisible hover hit areas per axis (wedge) */}
        {axes.map((_, i) => {
          const [x, y] = point(R + 30, i);
          return <circle key={`h${i}`} cx={x} cy={y} r="32" fill="transparent" style={{ cursor:'pointer' }}
            onMouseEnter={() => hover(i)} onMouseLeave={leave} />;
        })}
        {/* labels */}
        {axes.map((label, i) => {
          const [x, y] = labelPoint(i);
          let anchor = 'middle';
          if (x < cx - 10) anchor = 'end';
          else if (x > cx + 10) anchor = 'start';
          return (
            <text key={i} x={x} y={y} textAnchor={anchor} dominantBaseline="middle"
                  className={`radar-axis-label ${hl.skillIdx === i ? 'hl' : ''}`}
                  onMouseEnter={() => hover(i)} onMouseLeave={leave}>
              {label}
            </text>
          );
        })}
        <circle cx={cx} cy={cy} r="2" fill="rgba(255,255,255,.3)" />
      </svg>
    </div>
  );
}

// ---------------- GAP LIST -------------------------------------
function GapList({ skills, current, target, roleColor, onPracticeSkill }) {
  const { hl, setHl, t } = useStore();
  const gaps = current.map((c, i) => ({ i, label: skills[i], current: c, target: target[i], delta: c - target[i] }));
  const sorted = [...gaps].sort((a, b) => a.delta - b.delta);
  return (
    <div className="stack" style={{ gap: 8 }}>
      {sorted.map(g => {
        const tone = g.delta <= -2 ? 'bad' : g.delta < -0.5 ? 'warn' : 'good';
        const status = g.delta <= -2 ? `GAP ${g.delta.toFixed(1)}` : g.delta < -0.5 ? `GAP ${g.delta.toFixed(1)}` : 'LOCKED';
        const isHl = hl.skillIdx === g.i;
        return (
          <div key={g.i} className={`gap-row ${tone} ${isHl ? 'hl' : ''}`}
               onMouseEnter={() => setHl(s => ({ ...s, skillIdx: g.i }))}
               onMouseLeave={() => setHl(s => ({ ...s, skillIdx: null }))}
               onClick={() => onPracticeSkill && onPracticeSkill(g.i, g.label)}>
            <div className="label">{g.label}</div>
            <div className="bar">
              <div className="fill" style={{ width: `${g.current * 10}%`, background: roleColor }} />
              <div className="target" style={{ left: `${g.target * 10}%` }} />
            </div>
            <div className="score">{g.current.toFixed(1)} / {g.target.toFixed(1)}</div>
            <div className="status">{status}</div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------- ROADMAP LIST ---------------------------------
const ROADMAP_STEPS = {
  DA: [
    { kicker:'WEEK 1–2', title:'Drill SQL window functions', desc:'PARTITION BY, ROW_NUMBER, LAG/LEAD. 25 LeetCode SQL Medium problems.', skills:['SQL_WINDOW_FUNCTION','SQL_CTE'], skillIdx:[0,0], meta:'12 hrs', state:'active' },
    { kicker:'WEEK 3', title:'Ship a Tableau dashboard', desc:'Public dataset, 3-page board with cross-filters. Defend chart choices.', skills:['TOOL_TABLEAU','DATA_VIZ'], skillIdx:[1], meta:'8 hrs', state:'next' },
    { kicker:'WEEK 4', title:'Stats + A/B test review', desc:'Hypothesis testing, p-values, CI. Re-run last mock A/B.', skills:['STAT_AB_TESTING','STAT_HYPOTHESIS'], skillIdx:[2], meta:'6 hrs', state:'locked' },
    { kicker:'WEEK 5', title:'Full mock onsite (4× 45-min)', desc:'SQL · case · stats · behavioral. Post-mortem against the radar.', skills:['ANALYTICS_BUSINESS'], skillIdx:[3,4], meta:'8 hrs', state:'locked' },
  ],
  DE: [
    { kicker:'WEEK 1', title:'Re-implement an ETL in Airflow', desc:'Retries, SLA, idempotency. Push to GitHub.', skills:['TOOL_AIRFLOW'], skillIdx:[0], meta:'10 hrs', state:'active' },
    { kicker:'WEEK 2–3', title:'Spark performance deep dive', desc:'Read 3 real Spark jobs. Identify shuffles + skew. Tune by 2×.', skills:['TOOL_SPARK','BIG_DATA_OPT'], skillIdx:[2], meta:'14 hrs', state:'next' },
    { kicker:'WEEK 4', title:'Design: streaming clickstream warehouse', desc:'2-page design doc. Kafka vs Kinesis. Whiteboard sketch.', skills:['ARCH_STREAMING'], skillIdx:[1,4], meta:'6 hrs', state:'locked' },
    { kicker:'WEEK 5', title:'Full mock onsite (4× 45-min)', desc:'System design × 2, coding (Py + SQL), behavioral.', skills:['ARCH_SYSTEM_DESIGN','DATABASE_INDEXING'], skillIdx:[3], meta:'8 hrs', state:'locked' },
  ],
  DS: [
    { kicker:'WEEK 1–2 · CRITICAL', title:'Build a Deep Learning project', desc:'Train a CNN on CIFAR-10 or chest X-ray. Track experiments. Write architecture choices.', skills:['DL_FUNDAMENTALS','DL_CNN'], skillIdx:[3], meta:'16 hrs', state:'active' },
    { kicker:'WEEK 3', title:'Imbalanced classification clinic', desc:'Build a fraud detector. F1, ROC-AUC, PR-AUC.', skills:['METRIC_F1','IMBALANCED'], skillIdx:[1,2], meta:'8 hrs', state:'next' },
    { kicker:'WEEK 4', title:'NLP fundamentals refresh', desc:'Tokenization, embeddings, attention. Transformer text classifier.', skills:['NLP_FUNDAMENTALS'], skillIdx:[4], meta:'10 hrs', state:'locked' },
    { kicker:'WEEK 5', title:'Full mock onsite (4× 45-min)', desc:'ML case · coding · stats · behavioral. Compare radar after.', skills:['ML_MODEL_SELECTION'], skillIdx:[0,5], meta:'8 hrs', state:'locked' },
  ],
};

function RoadmapList({ role, compact }) {
  const { hl, setHl } = useStore();
  const steps = ROADMAP_STEPS[role] || ROADMAP_STEPS.DA;
  return (
    <div>
      {steps.map((s, i) => {
        const stateC = s.state === 'active' ? roleColor(role) : s.state === 'next' ? '#fde047' : 'var(--fg-6)';
        const isHl = s.skillIdx && s.skillIdx.includes(hl.skillIdx);
        return (
          <div key={i}
               className={`rm-step ${s.state === 'locked' ? 'locked' : ''} ${isHl ? 'hl' : ''}`}
               style={{ '--rm-c': stateC }}
               onMouseEnter={() => s.skillIdx && setHl(st => ({ ...st, skillIdx: s.skillIdx[0] }))}
               onMouseLeave={() => setHl(st => ({ ...st, skillIdx: null }))}>
            <div className="num">{String(i + 1).padStart(2, '0')}</div>
            <div className="body">
              <div className="kicker">{s.kicker} · {s.state.toUpperCase()}</div>
              <div className="title">{s.title}</div>
              {!compact && <div className="desc">{s.desc}</div>}
              <div className="skills">{s.skills.map(sk => <span key={sk}>#{sk}</span>)}</div>
            </div>
            <div className="meta">{s.meta}</div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------- ROLE PICKER (mini) ---------------------------
function RolePickerMini({ value, onPick }) {
  const { state } = useStore();
  const lang = state.lang;
  const ROLES = [
    { id:'DA', name:'Data Analyst', kicker:'01 / FOUNDATION', desc: lang === 'vi' ? 'SQL, dashboard, insight kinh doanh.' : 'SQL, dashboards, business insight.' },
    { id:'DE', name:'Data Engineer', kicker:'02 / INFRASTRUCTURE', desc: lang === 'vi' ? 'Pipeline, kho dữ liệu, cloud.' : 'Pipelines, warehouses, cloud.' },
    { id:'DS', name:'Data Scientist', kicker:'03 / MODELING', desc: lang === 'vi' ? 'ML, đánh giá mô hình, thí nghiệm.' : 'ML, model evaluation, experiments.' },
  ];
  return (
    <div className="role-grid-mini">
      {ROLES.map(r => (
        <div key={r.id} className={`role-card-mini ${r.id.toLowerCase()} ${value === r.id ? 'active' : ''}`} onClick={() => onPick(r.id)}>
          <div className="rcno">{r.kicker}</div>
          <h3>{r.name}</h3>
          <div className="rcdesc">{r.desc}</div>
          {value === r.id && <div className="chip solid" style={{ marginTop: 14, '--role-color': roleColor(r.id) }}>SELECTED ✓</div>}
        </div>
      ))}
    </div>
  );
}

// ---------------- LIVE STREAMING TEXT --------------------------
function StreamingText({ text, speed = 24, onDone }) {
  const [shown, setShown] = React.useState('');
  React.useEffect(() => {
    setShown('');
    let i = 0;
    const interval = setInterval(() => {
      i += Math.max(1, Math.floor(text.length / (text.length / speed * 4))); // adaptive
      i += 1;
      setShown(text.slice(0, i));
      if (i >= text.length) { clearInterval(interval); if (onDone) onDone(); }
    }, 1000 / speed);
    return () => clearInterval(interval);
  }, [text]);
  return (
    <span>{shown}<span className="cursor"></span></span>
  );
}

// ---------------- HISTORY RADAR OVERLAY (small multiples + master) ----
function HistoryOverlay({ attempts, axes, target, role }) {
  const color = roleColor(role);
  const size = 320;
  const cx = size/2, cy = size/2;
  const R = size * 0.38;
  const N = axes.length;
  const angle = (i) => (-Math.PI / 2) + (i * 2 * Math.PI / N);
  const point = (r, i) => [cx + r * Math.cos(angle(i)), cy + r * Math.sin(angle(i))];
  const polygon = (vec) => vec.map((v, i) => point((v / 10) * R, i).join(',')).join(' ');
  // each attempt as a polygon, older ones fainter
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {[0.25,0.5,0.75,1].map((f,i) => (
        <polygon key={i} points={Array.from({length:N},(_,j)=>point(f*R,j).join(',')).join(' ')} fill="none" stroke="rgba(244,244,245,.08)" />
      ))}
      {Array.from({length:N},(_,i)=>{
        const [x,y]=point(R,i);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(244,244,245,.12)" />;
      })}
      {/* target */}
      <polygon points={polygon(target)} fill="none" stroke="#ff3366" strokeWidth="1.5" strokeDasharray="3 3" opacity="0.7" />
      {/* attempts — older = lower opacity */}
      {attempts.map((a, i) => {
        const opacity = 0.15 + (i / Math.max(1, attempts.length - 1)) * 0.85;
        return (
          <polygon key={a.id} points={polygon(a.vector)} fill="none" stroke={color} strokeWidth={i === attempts.length - 1 ? 2 : 1} opacity={opacity} />
        );
      })}
      {/* current dots */}
      {attempts.length > 0 && attempts[attempts.length-1].vector.map((v,i) => {
        const [x,y] = point((v/10)*R, i);
        return <circle key={i} cx={x} cy={y} r="3" fill={color} />;
      })}
      {/* labels */}
      {axes.map((l,i) => {
        const [x,y]=point(R+18,i);
        let anchor='middle'; if(x<cx-10) anchor='end'; else if(x>cx+10) anchor='start';
        return <text key={i} x={x} y={y} textAnchor={anchor} dominantBaseline="middle" fill="#a1a1aa" fontFamily="JetBrains Mono, monospace" fontSize="9" letterSpacing="1" style={{ textTransform:'uppercase', fontWeight:900 }}>{l}</text>;
      })}
    </svg>
  );
}

// ---------------- CONNECT STATUS BADGE (header) ----------------
function StatusBadge({ tone = 'cyan', children }) {
  const c = tone === 'good' ? 'var(--success)' : tone === 'warn' ? 'var(--warn)' : tone === 'bad' ? 'var(--danger)' : 'var(--accent-cyan)';
  return (
    <span className="tb-pill" style={{ '--role-color': c, color: c }}>
      <span className="dot" style={{ background: c, boxShadow: `0 0 8px ${c}` }}></span>
      {children}
    </span>
  );
}

Object.assign(window, {
  RadarChart, GapList, RoadmapList, RolePickerMini, StreamingText, HistoryOverlay, StatusBadge,
  ROADMAP_STEPS,
});
