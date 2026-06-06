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

      <div className="card role-top" style={{ '--role-color': color }}>
        <h2>{state.lang === 'vi' ? 'Lộ trình liên kết' : 'Linked roadmap'}</h2>
        <div className="muted" style={{ fontSize: 13, marginBottom: 16 }}>{state.lang === 'vi' ? 'Mỗi bước liên kết với một hoặc nhiều kỹ năng. Hover trục radar phía trên để xem.' : 'Each step links to one or more skill axes. Hover the radar above to see.'}</div>
        <RoadmapList role={role} compact />
        <div style={{ marginTop: 14, textAlign:'right' }}>
          <button className="btn role compact" style={{ '--role-color': color, borderColor: color, color }} onClick={() => onNav('roadmap')}>{state.lang === 'vi' ? 'Lộ trình đầy đủ →' : 'Full roadmap →'}</button>
        </div>
      </div>
    </>
  );
}

// ============================================================
// ROADMAP
// ============================================================
function RoadmapScreen({ onNav }) {
  const { state, t } = useStore();
  if (!state.role) return <EmptyState onNav={onNav} message="No role selected" />;
  const vi = state.lang === 'vi';
  const hasAttempt = state.attempts.some(a => a.role === state.role);
  if (!hasAttempt) return (
    <div style={{ padding: '60px 32px', textAlign:'center' }}>
      <div className="mono" style={{ fontSize:10, color:'var(--fg-5)', letterSpacing:'.22em', textTransform:'uppercase', marginBottom:14 }}>
        {vi ? 'LỘ TRÌNH · CHƯA CÓ DỮ LIỆU' : 'ROADMAP · NO DATA YET'}
      </div>
      <div style={{ fontFamily:'var(--font-sans)', fontSize:28, fontWeight:950, textTransform:'uppercase', letterSpacing:'-.04em', color:'var(--fg-0)', marginBottom:12 }}>
        {vi ? 'Lộ trình được tạo sau đánh giá' : 'Roadmap is generated after assessment'}
      </div>
      <div className="muted" style={{ fontSize:14, marginBottom:28, maxWidth:480, margin:'0 auto 28px' }}>
        {vi ? 'Làm phỏng vấn đầu tiên → AI phân tích gap → lộ trình 5 tuần cá nhân hóa theo role của bạn.' : 'Complete an interview → AI analyzes your gaps → generates a personalized 5-week plan for your role.'}
      </div>
      <button className="btn primary" onClick={() => onNav('interview', { mode: 'quick' })}>
        {vi ? 'Bắt đầu đánh giá →' : 'Start assessment →'}
      </button>
    </div>
  );
  const role = state.role;
  const color = roleColor(role);
  const steps = ROADMAP_STEPS[role];
  const totalHrs = steps.reduce((acc, s) => acc + parseInt(s.meta), 0);

  return (
    <>
      <PageHead
        kicker={`${role} · ${t('roadmap.kicker')}`}
        title={t('roadmap.title')}
        right={[
          <button key="b" className="btn ghost compact" onClick={() => onNav('dashboard')}>← {state.lang === 'vi' ? 'Dashboard' : 'Dashboard'}</button>,
          <button key="p" className="btn primary compact">📅 {t('roadmap.pin')}</button>,
        ]}
      />
      <SpecStrip items={[
        <span key="r">ROLE: <span style={{ color }}>{state.role === 'DA' ? 'Data Analyst' : state.role === 'DE' ? 'Data Engineer' : 'Data Scientist'}</span></span>,
        `~${totalHrs} hrs total`,
        '5 weeks',
        state.lang === 'vi' ? 'Sắp theo độ ưu tiên gap' : 'Sequenced by gap severity',
        state.lang === 'vi' ? 'Tự refresh sau retake' : 'Auto-reflows on retake',
      ]} />

      <div className="split-2" style={{ alignItems:'start' }}>
        <div className="card raised role-top" style={{ '--role-color': color }}>
          <h2>{state.lang === 'vi' ? 'Kế hoạch 5 tuần' : '5-week plan'}</h2>
          <RoadmapList role={role} />
        </div>
        <div className="stack">
          <div className="card warn-top">
            <h3 style={{ color:'var(--accent-warn)' }}>{t('roadmap.nextMs').toUpperCase()}</h3>
            <div style={{ fontFamily:'var(--font-sans)', fontSize: 18, fontWeight: 900, color:'var(--fg-0)', lineHeight: 1.25, marginBottom: 10, textTransform:'uppercase', letterSpacing:'-.01em' }}>
              {steps[0].title}
            </div>
            <div className="muted" style={{ fontSize: 13, marginBottom: 14 }}>
              {state.lang === 'vi' ? `Đến ${steps[0].meta} từ giờ tới Chủ nhật. Sau đó retake radar.` : `${steps[0].meta} before Sunday. Then retake the radar.`}
            </div>
            <button className="btn primary full">{state.lang === 'vi' ? 'Bắt đầu bước 01 →' : 'Start step 01 →'}</button>
          </div>
          <div className="card">
            <h3>RESOURCES</h3>
            <div className="stack" style={{ gap: 10 }}>
              <div className="row between" style={{ fontSize: 12 }}><span className="mono">📺 LeetCode SQL</span><span className="cyan mono">25 problems</span></div>
              <div className="row between" style={{ fontSize: 12 }}><span className="mono">📖 SQL Window guide</span><span className="cyan mono">12 min</span></div>
              <div className="row between" style={{ fontSize: 12 }}><span className="mono">🎥 Recursive CTE tutorial</span><span className="cyan mono">18 min</span></div>
              <div className="row between" style={{ fontSize: 12 }}><span className="mono">🧪 Sandbox: SQL playground</span><span className="cyan mono">→</span></div>
            </div>
          </div>
          <div className="card">
            <h3>COHORT PROGRESS</h3>
            <div className="muted" style={{ fontSize: 12, marginBottom: 10 }}>{state.lang === 'vi' ? 'Trung bình người cùng track' : 'Average for your role'}</div>
            <div className="stack" style={{ gap: 8 }}>
              <div>
                <div className="row between" style={{ fontSize: 11, marginBottom: 4 }}><span className="mono muted">YOU</span><span className="mono cyan">40%</span></div>
                <div style={{ height: 6, background:'rgba(255,255,255,.1)', position:'relative' }}><div style={{ position:'absolute', left: 0, top: 0, height:'100%', width: '40%', background: color }}></div></div>
              </div>
              <div>
                <div className="row between" style={{ fontSize: 11, marginBottom: 4 }}><span className="mono muted">COHORT AVG</span><span className="mono muted">28%</span></div>
                <div style={{ height: 6, background:'rgba(255,255,255,.1)', position:'relative' }}><div style={{ position:'absolute', left: 0, top: 0, height:'100%', width: '28%', background: 'var(--fg-5)' }}></div></div>
              </div>
            </div>
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
