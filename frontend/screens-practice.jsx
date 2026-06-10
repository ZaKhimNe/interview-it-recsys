// ============================================================
// screens-practice.jsx — Home, Interview, Questions library
// ============================================================

function HomeScreen({ onNav }) {
  const { state, t } = useStore();
  if (!state.role) return <EmptyState onNav={onNav} message="No role selected" />;
  const color = roleColor(state.role);
  const rawVec = currentVector(state);
  const target = ROLE_TARGETS[state.role] || [];
  const axes = SKILL_AXES[state.role] || [];
  // Đảm bảo cùng độ dài với axes (data thật từ Python)
  const vec = axes.map((_, i) => (rawVec || [])[i] ?? 0);
  const hasAttempt = state.attempts.some(a => a.role === state.role);
  const gaps = vec.map((v, i) => v - (target[i] ?? 0));
  const worstIdx = gaps.length > 0 ? gaps.reduce((bi, g, i) => g < gaps[bi] ? i : bi, 0) : 0;
  const worstSkill = axes[worstIdx] || '—';

  const vi = state.lang === 'vi';
  const modes = [
    { id:'quick',   title: t('home.quickDrill'), desc: t('home.qdDesc'), badge:'5 MIN', col:'#00e5ff' },
    { id:'focused', title: t('home.focused'),    desc: t('home.fpDesc'), badge:'15 MIN', col:'#ff7a1a' },
    { id:'mock',    title: t('home.mock'),       desc: t('home.mkDesc'), badge:'45 MIN', col:'#a3ff12' },
    { id:'custom',  title: t('home.custom'),     desc: t('home.ctDesc'), badge: vi ? 'TÙY CHỈNH' : 'CUSTOM', col:'#ff3366' },
  ];

  return (
    <>
      <PageHead
        kicker={t('home.kicker')}
        title={`${t('home.title')}, ${state.user.name}`}
        right={[
          <StatusBadge key="s" tone="good">{vi ? 'ĐỒNG BỘ' : 'SYNC OK'}</StatusBadge>,
          <button key="a" className="btn compact role" style={{ '--role-color': color, borderColor: color, color }}>★ {state.user.streak}{vi ? ' ngày' : 'd streak'}</button>,
        ]}
      />

      {/* metric row — chỉ hiện khi đã có attempt thật */}
      {hasAttempt ? (
        <div className="split-4" style={{ marginBottom: 24 }}>
          <div className="metric info">
            <div className="k">{vi ? 'TỔNG QUAN' : 'OVERALL'}</div>
            <div className="v">{(vec.reduce((a,b)=>a+b,0)/vec.length).toFixed(1)}<span className="unit">/10</span></div>
            <div className="delta">{vi ? 'SO MỤC TIÊU' : 'VS TARGET'} {((vec.reduce((a,b)=>a+b,0)-(target.reduce((a,b)=>a+b,0)||0))/vec.length).toFixed(1)}</div>
          </div>
          <div className="metric good">
            <div className="k">{vi ? 'ĐÃ TRẢ LỜI' : 'ANSWERED'}</div>
            <div className="v">{state.completedQs.length}<span className="unit">{vi ? 'câu' : 'qs'}</span></div>
            <div className="delta">{vi ? 'TỔNG CỘNG' : 'LIFETIME'}</div>
          </div>
          <div className="metric warn">
            <div className="k">{vi ? 'GAP LỚN NHẤT' : 'BIGGEST GAP'}</div>
            <div className="v" style={{ fontSize: 18 }}>{worstSkill}</div>
            <div className="delta">{gaps[worstIdx] != null ? gaps[worstIdx].toFixed(1) : '—'}</div>
          </div>
          <div className="metric bad">
            <div className="k">{vi ? 'CẦN ÔN TẬP' : 'DUE FOR REPETITION'}</div>
            <div className="v">{state.completedQs.length > 0 ? Math.ceil(state.completedQs.length * 0.15) : 0}<span className="unit">{vi ? 'câu' : 'qs'}</span></div>
            <div className="delta">{vi ? 'HÔM NAY' : 'SCHEDULED TODAY'}</div>
          </div>
        </div>
      ) : (
        <div className="card warn-top" style={{ marginBottom: 24, padding: '18px 22px' }}>
          <div className="row between" style={{ alignItems:'center' }}>
            <div>
              <div className="mono" style={{ fontSize: 10, color:'var(--accent-warn)', letterSpacing:'.22em', fontWeight:900, marginBottom:6 }}>
                {state.lang === 'vi' ? 'BẮT ĐẦU ĐÁNH GIÁ' : 'START YOUR ASSESSMENT'}
              </div>
              <div style={{ fontFamily:'var(--font-sans)', fontSize:18, fontWeight:950, color:'var(--fg-0)', textTransform:'uppercase', letterSpacing:'-.02em' }}>
                {state.lang === 'vi' ? 'Chưa có dữ liệu radar' : 'No radar data yet'}
              </div>
              <div className="muted" style={{ fontSize:13, marginTop:4 }}>
                {state.lang === 'vi' ? 'Làm phỏng vấn đầu tiên để dựng vector năng lực của bạn.' : 'Complete your first interview to build your competency vector.'}
              </div>
            </div>
            <button className="btn primary" onClick={() => onNav('interview', { mode: 'quick' })}>
              {state.lang === 'vi' ? 'Bắt đầu →' : 'Start →'}
            </button>
          </div>
        </div>
      )}

      <div className="split-2" style={{ alignItems:'start' }}>
        <div>
          <div className="mono" style={{ fontSize: 11, color:'var(--fg-5)', letterSpacing:'.22em', textTransform:'uppercase', marginBottom: 14 }}>{state.lang === 'vi' ? 'CHỌN PHIÊN PHỎNG VẤN' : 'PICK A SESSION MODE'}</div>
          <div className="split-2">
            {modes.map(m => (
              <div key={m.id} className="card raised" style={{ borderTop: `4px solid ${m.col}`, cursor:'pointer', minHeight: 160, display:'flex', flexDirection:'column' }}
                   onClick={() => onNav('interview', { mode: m.id })}>
                <div className="row between">
                  <div className="mono" style={{ fontSize: 10, color: m.col, letterSpacing:'.2em', fontWeight: 900 }}>{m.badge}</div>
                  <div className="mono" style={{ fontSize: 11, color:'var(--fg-5)' }}>→</div>
                </div>
                <div style={{ fontFamily:'var(--font-sans)', fontSize: 22, fontWeight: 950, color:'var(--fg-0)', textTransform:'uppercase', letterSpacing:'-.03em', marginTop: 16, lineHeight: 1 }}>{m.title}</div>
                <div className="muted" style={{ fontSize: 13, marginTop: 8, lineHeight: 1.5 }}>{m.desc}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="stack">
          {hasAttempt ? (
            <>
              <div className="card role-top" style={{ '--role-color': color }}>
                <h3 style={{ color }}>{t('home.next').toUpperCase()}</h3>
                <div style={{ fontFamily:'var(--font-sans)', fontSize: 18, fontWeight: 800, color:'var(--fg-0)', lineHeight: 1.3, marginBottom: 10 }}>
                  {vi ? `Tập trung vào ${worstSkill}` : `Focus on ${worstSkill}`}
                </div>
                <div className="muted" style={{ fontSize: 13, marginBottom: 14 }}>
                  {vi ? `Đây là gap lớn nhất (${gaps[worstIdx].toFixed(1)} dưới mục tiêu). 3 câu hỏi đợi sẵn.` : `Your biggest gap (${gaps[worstIdx].toFixed(1)} below target). 3 questions ready.`}
                </div>
                <button className="btn role full" style={{ '--role-color': color }} onClick={() => onNav('interview', { skill: worstSkill })}>
                  {vi ? 'Bắt đầu →' : 'Start →'}
                </button>
              </div>
              <div className="card">
                <h3>{vi ? 'ÔN TẬP CÁCH QUÃNG' : 'SPACED REPETITION'}</h3>
                <div className="stack" style={{ gap: 8 }}>
                  <div className="row between" style={{ fontSize: 12 }}><span className="mono muted">{vi ? 'HÔM NAY' : 'DUE TODAY'}</span><span className="mono cyan">{Math.max(1, Math.ceil(state.completedQs.length * 0.15))} qs</span></div>
                  <div className="row between" style={{ fontSize: 12 }}><span className="mono muted">{vi ? 'TUẦN NÀY' : 'DUE THIS WEEK'}</span><span className="mono">{Math.max(2, Math.ceil(state.completedQs.length * 0.35))} qs</span></div>
                  <div className="row between" style={{ fontSize: 12 }}><span className="mono muted">{vi ? 'CÒN LẠI' : 'BACKLOG'}</span><span className="mono hot">{Math.max(0, state.completedQs.length - Math.ceil(state.completedQs.length * 0.35))} qs</span></div>
                </div>
                <button className="btn ghost compact full" style={{ marginTop: 14 }} onClick={() => onNav('questions')}>{vi ? 'Xem tất cả →' : 'Browse →'}</button>
              </div>
            </>
          ) : (
            <div className="card" style={{ padding: 24 }}>
              <div className="mono" style={{ fontSize: 10, color:'var(--fg-5)', letterSpacing:'.22em', textTransform:'uppercase', marginBottom: 12 }}>
                {vi ? 'SAU KHI LÀM PHỎNG VẤN' : 'AFTER YOUR FIRST SESSION'}
              </div>
              <div style={{ fontFamily:'var(--font-sans)', fontSize: 16, fontWeight: 800, color:'var(--fg-2)', textTransform:'uppercase', letterSpacing:'-.02em', lineHeight: 1.4, marginBottom: 10 }}>
                {vi ? 'Radar · Lộ trình · Ôn tập cách quãng sẽ xuất hiện ở đây.' : 'Radar · Roadmap · Spaced repetition will appear here.'}
              </div>
              <div className="muted" style={{ fontSize: 13, lineHeight: 1.55 }}>
                {vi ? 'Hoàn thành 1 phiên để unlock toàn bộ dashboard.' : 'Complete 1 session to unlock your full dashboard.'}
              </div>
            </div>
          )}
        </div>
      </div>
      {/* Diagnostic Test banner */}
      <div className="card" style={{ marginTop:16, borderTop:'4px solid #00e5ff', cursor:'pointer', padding:'18px 22px' }}
           onClick={() => onNav('diagnostic')}>
        <div className="row between" style={{ alignItems:'center', flexWrap:'wrap', gap:12 }}>
          <div>
            <div className="mono" style={{ fontSize:10, color:'#00e5ff', letterSpacing:'.22em', fontWeight:900, marginBottom:6 }}>
              DIAGNOSTIC TEST · MST · 10 CAU
            </div>
            <div style={{ fontFamily:'var(--font-sans)', fontSize:18, fontWeight:950, color:'var(--fg-0)', textTransform:'uppercase', letterSpacing:'-.02em' }}>
              {vi ? 'Danh gia nang luc toan dien' : 'Full Competency Assessment'}
            </div>
            <div className="muted" style={{ fontSize:13, marginTop:4 }}>
              {vi
                ? 'Stage 1: 4 cau dinh vi · Stage 2: 6 cau thich ung theo ket qua. Ghe GRE/TOEFL.'
                : 'Stage 1: 4 placement questions · Stage 2: 6 questions adaptive to your result.'}
            </div>
          </div>
          <button className="btn primary" style={{ flexShrink:0 }}>
            {vi ? 'Bat dau →' : 'Start →'}
          </button>
        </div>
      </div>
    </>
  );
}

// ============================================================
// INTERVIEW — supports modes: quick/focused/mock/custom + sandbox
// ============================================================
function InterviewScreen({ onNav, opts }) {
  const { state, set, t } = useStore();
  if (!state.role) return <EmptyState onNav={onNav} message="No role selected" />;
  const role = state.role;
  const color = roleColor(role);
  const [tab, setTab] = React.useState('answer');
  const [running, setRunning] = React.useState(false);
  const [streamed, setStreamed] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);
  const [elapsed, setElapsed] = React.useState(0);
  const [code, setCode] = React.useState('');
  const [sandboxOut, setSandboxOut] = React.useState('');
  const [answer, setAnswer] = React.useState('');
  // MC_SINGLE: selected option id string
  const [selectedOption, setSelectedOption] = React.useState('');
  // TRUE_FALSE: null | true | false
  const [boolAnswer, setBoolAnswer] = React.useState(null);
  // FILL_BLANK: array of strings, one per blank
  const [blankAnswers, setBlankAnswers] = React.useState([]);

  const mode = (opts && opts.mode) || 'focused';
  const isAssessment = mode === 'assessment';

  // pick a question: specific qid > skill-filtered > random from role pool
  const question = React.useMemo(() => {
    if (opts && opts.qid) {
      return QUESTIONS.find(q => q.id === opts.qid) || QUESTIONS[0];
    }
    const candidates = QUESTIONS.filter(q => q.role === role);
    const pool = (opts && opts.skill)
      ? candidates.filter(q => q.tags && q.tags.some(tag => tag.includes(opts.skill.replace(/[\s.]/g, '_').toUpperCase())))
      : candidates;
    const src = pool.length ? pool : candidates;
    return src[Math.floor(Math.random() * src.length)] || QUESTIONS[0];
  }, [role, opts && opts.qid, opts && opts.skill]);

  const lang = state.lang;
  const title = lang === 'vi' && question.title_vi ? question.title_vi : question.title_en;
  const body = lang === 'vi' && question.body_vi ? question.body_vi : question.body_en;

  React.useEffect(() => {
    if (question.starterCode) setCode(question.starterCode);
    else setCode('');
    // reset per-type answer state
    setSelectedOption('');
    setBoolAnswer(null);
    const blanks = (question.template || '').split('[___]').length - 1;
    setBlankAnswers(Array(Math.max(blanks, 0)).fill(''));
    setAnswer('');
  }, [question && question.id]);

  React.useEffect(() => {
    if (submitted) return;
    const i = setInterval(() => setElapsed(e => e + 1), 1000);
    return () => clearInterval(i);
  }, [submitted]);

  const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
  const ss = String(elapsed % 60).padStart(2, '0');

  const runSandbox = () => {
    setRunning(true);
    setSandboxOut(lang === 'vi' ? '> đang chạy…' : '> running…');
    setTimeout(() => {
      if (question.id.startsWith('Q_DA')) {
        setSandboxOut(`> running query against sample.employees (50 rows)…\n\n  salary\n  ───────\n  187500.00\n\n[OK] 1 row returned · 0.124s`);
      } else if (question.id.startsWith('Q_DS')) {
        setSandboxOut(`> python interpreter (sample dataset · 10,000 rows · 100 positives)\n>>> from sklearn.metrics import f1_score, roc_auc_score\n>>> y_pred = clf.predict(X_test)\n>>> y_score = clf.predict_proba(X_test)[:,1]\n>>>\nF1:      0.241\nROC-AUC: 0.873\nPR-AUC:  0.412\n\n[OK] done · 0.482s`);
      } else {
        setSandboxOut(`> sandbox ready · no auto-execution for this question type`);
      }
      setRunning(false);
    }, 900);
  };

  const qtype = (question && question.questionType) || 'THEORY';

  // Determine if answer is ready to submit
  const canSubmit = (() => {
    if (qtype === 'MC_SINGLE') return !!selectedOption;
    if (qtype === 'TRUE_FALSE') return boolAnswer !== null;
    if (qtype === 'FILL_BLANK') return blankAnswers.length > 0 && blankAnswers.every(b => b.trim());
    if (qtype === 'CODING_EXERCISE') return code.trim().length > 10;
    return answer.trim().length > 0;
  })();

  const submit = () => {
    // Stub: tính toán vector cải thiện nhỏ (chờ Model Lead thay bằng AI thật)
    const axes = SKILL_AXES[role] || [];
    const rawVec = currentVector(state) || [];
    const curVec = axes.map((_, i) => rawVec[i] ?? 0);
    const tgtVec = ROLE_TARGETS[role] || [];

    // Cải thiện ~0.15 điểm trên mỗi trục, không vượt target
    const newVector = curVec.map((v, i) => {
      const target = tgtVec[i] ?? 10;
      const gain = answer.trim().length > 30 || selectedOption || boolAnswer !== null ? 0.15 : 0.05;
      return Math.min(target, parseFloat((v + gain).toFixed(2)));
    });

    const newAttempt = {
      id: `session-${Date.now()}`,
      date: new Date().toISOString().slice(0, 10),
      role,
      vector: newVector,
    };
    const newCompleted = state.completedQs.includes(question.id)
      ? state.completedQs
      : [...state.completedQs, question.id];

    set({ attempts: [...state.attempts, newAttempt], completedQs: newCompleted });
    setSubmitted(true);
    setStreamed(false);
    // MC/TF/FILL_BLANK: kết quả đã hiện inline trong tab Answer → giữ nguyên
    // THEORY/CODING/PRACTICE/CODING_EXERCISE: switch sang Expert tab
    const showResultInline = ['MC_SINGLE', 'TRUE_FALSE', 'FILL_BLANK'].includes(qtype);
    if (!showResultInline) setTab('expert');
  };

  return (
    <>
      <PageHead
        kicker={isAssessment ? (lang === 'vi' ? 'ĐÁNH GIÁ BAN ĐẦU · XÂY DỰNG RADAR' : 'INITIAL ASSESSMENT · BUILD YOUR RADAR') : `${t('interview.kicker')} · MODE: ${mode.toUpperCase()}`}
        title={isAssessment ? (lang === 'vi' ? 'Câu hỏi đánh giá' : 'Assessment Question') : t('interview.title')}
        right={[
          <button key="sk" className="btn ghost compact" onClick={() => onNav('home')}>{t('interview.skip')}</button>,
          <button key="en" className="btn danger compact" onClick={() => {
            if (submitted || confirm(lang === 'vi' ? 'Kết thúc phiên? Câu trả lời hiện tại sẽ không được lưu.' : 'End session? Current answer will not be saved.')) {
              onNav('dashboard');
            }
          }}>{t('interview.end')}</button>,
        ]}
      />
      <SpecStrip items={[
        <span key="r">ROLE: <span className="role-color" style={{ color }}>{state.role}</span></span>,
        question.id,
        <span key="d" className="warn-c">{question.difficulty}</span>,
        `${question.estMin} MIN EST.`,
        `SESSION_${Date.now().toString().slice(-6)}`,
      ]} />

      <div className="iv-workbench">
        <div className="card raised role-top" style={{ '--role-color': color }}>
          <div className="row wrap" style={{ gap: 6, marginBottom: 10 }}>
            {question.tags.map(t2 => <span key={t2} className="chip role" style={{ '--role-color': color, borderColor: color, color }}>#{t2}</span>)}
          </div>
          <div style={{ fontFamily:'var(--font-sans)', fontSize: 24, fontWeight: 800, color:'var(--fg-0)', letterSpacing:'-.01em', lineHeight: 1.25, marginBottom: 10 }}>{title}</div>
          <div className="muted" style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 18 }}>{body}</div>

          <div className="iv-tabs">
            <button className={`iv-tab ${tab === 'answer' ? 'active' : ''}`} style={{ '--role-color': color }} onClick={() => setTab('answer')}>{lang === 'vi' ? 'Trả lời' : 'Answer'}</button>
            {(question.starterCode || qtype === 'CODING_EXERCISE') && <button className={`iv-tab ${tab === 'sandbox' ? 'active' : ''}`} style={{ '--role-color': color }} onClick={() => setTab('sandbox')}>{lang === 'vi' ? 'Code' : 'Code'}</button>}
            {submitted && <button className={`iv-tab ${tab === 'expert' ? 'active' : ''}`} style={{ '--role-color': color }} onClick={() => setTab('expert')}>{lang === 'vi' ? 'Đáp án chuyên gia' : 'Expert answer'}</button>}
          </div>

          {tab === 'answer' && (() => {
            // MC_SINGLE
            if (qtype === 'MC_SINGLE') {
              const opts = question.options || [];
              const correctId = question.correctOptionId;
              return (
                <div className="stack" style={{ gap: 10, marginTop: 8 }}>
                  {opts.map(opt => {
                    const isSelected = selectedOption === opt.id;
                    const isCorrect = submitted && opt.id === correctId;
                    const isWrong = submitted && isSelected && opt.id !== correctId;
                    const borderCol = isCorrect ? 'var(--success)' : isWrong ? 'var(--danger)' : isSelected ? color : 'var(--line-med)';
                    return (
                      <button key={opt.id}
                        onClick={() => !submitted && setSelectedOption(opt.id)}
                        style={{
                          textAlign: 'left', padding: '12px 16px', borderRadius: 8,
                          border: `2px solid ${borderCol}`,
                          background: isSelected ? `${color}18` : 'var(--bg-3)',
                          color: isCorrect ? 'var(--success)' : isWrong ? 'var(--danger)' : 'var(--fg-0)',
                          cursor: submitted ? 'default' : 'pointer', fontSize: 14, fontFamily: 'var(--font-sans)',
                          transition: 'all .15s',
                        }}>
                        <span className="mono" style={{ color: borderCol, marginRight: 10, fontWeight: 700 }}>{opt.id}.</span>
                        {opt.text}
                        {isCorrect && ' ✓'}
                        {isWrong && ' ✗'}
                      </button>
                    );
                  })}
                  {submitted && question.explanation && (
                    <div className="muted" style={{ fontSize: 13, padding: '10px 14px', background: 'var(--bg-3)', borderRadius: 6, borderLeft: `3px solid ${color}`, lineHeight: 1.6 }}>
                      {question.explanation}
                    </div>
                  )}
                </div>
              );
            }

            // TRUE_FALSE
            if (qtype === 'TRUE_FALSE') {
              const correct = question.correctAnswer;
              return (
                <div className="stack" style={{ gap: 10, marginTop: 8 }}>
                  <div className="row" style={{ gap: 12 }}>
                    {[true, false].map(val => {
                      const isSelected = boolAnswer === val;
                      const isCorrect = submitted && val === correct;
                      const isWrong = submitted && isSelected && val !== correct;
                      const borderCol = isCorrect ? 'var(--success)' : isWrong ? 'var(--danger)' : isSelected ? color : 'var(--line-med)';
                      return (
                        <button key={String(val)}
                          onClick={() => !submitted && setBoolAnswer(val)}
                          style={{
                            flex: 1, padding: '18px 0', borderRadius: 8,
                            border: `2px solid ${borderCol}`,
                            background: isSelected ? `${color}18` : 'var(--bg-3)',
                            color: isCorrect ? 'var(--success)' : isWrong ? 'var(--danger)' : 'var(--fg-0)',
                            cursor: submitted ? 'default' : 'pointer',
                            fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)',
                            transition: 'all .15s',
                          }}>
                          {val ? 'TRUE ✓' : 'FALSE ✗'}
                        </button>
                      );
                    })}
                  </div>
                  {submitted && question.explanation && (
                    <div className="muted" style={{ fontSize: 13, padding: '10px 14px', background: 'var(--bg-3)', borderRadius: 6, borderLeft: `3px solid ${color}`, lineHeight: 1.6 }}>
                      {question.explanation}
                    </div>
                  )}
                </div>
              );
            }

            // FILL_BLANK
            if (qtype === 'FILL_BLANK') {
              const tmpl = question.template || question.body_vi || '';
              const parts = tmpl.split('[___]');
              return (
                <div className="stack" style={{ gap: 12, marginTop: 8 }}>
                  <div style={{ fontSize: 14, lineHeight: 2, color: 'var(--fg-1)' }}>
                    {parts.map((part, i) => (
                      <React.Fragment key={i}>
                        {part}
                        {i < parts.length - 1 && (
                          <input
                            value={blankAnswers[i] || ''}
                            onChange={e => {
                              const next = [...blankAnswers];
                              next[i] = e.target.value;
                              setBlankAnswers(next);
                            }}
                            readOnly={submitted}
                            placeholder={`(${i + 1})`}
                            style={{
                              display: 'inline-block', width: 140, margin: '0 6px',
                              padding: '4px 10px', borderRadius: 6,
                              border: `1.5px solid ${submitted ? (blankAnswers[i] ? 'var(--success)' : 'var(--danger)') : color}`,
                              background: 'var(--bg-3)', color: 'var(--fg-0)',
                              fontFamily: 'var(--font-mono)', fontSize: 13,
                            }}
                          />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                  {submitted && question.explanation && (
                    <div className="muted" style={{ fontSize: 13, padding: '10px 14px', background: 'var(--bg-3)', borderRadius: 6, borderLeft: `3px solid ${color}`, lineHeight: 1.6 }}>
                      {question.explanation}
                    </div>
                  )}
                </div>
              );
            }

            // Default: THEORY / PRACTICE / CODING / CODING_EXERCISE (textarea)
            return (
              <textarea className="textarea" placeholder={t('interview.placeholder')}
                        style={{ '--role-color': color, minHeight: 220 }}
                        value={answer}
                        onChange={(e) => setAnswer(e.target.value)}
                        readOnly={submitted} />
            );
          })()}
          {tab === 'sandbox' && (
            <div className="stack" style={{ gap: 8 }}>
              <div className="row between" style={{ fontSize: 11 }}>
                <span className="mono muted">
                  {qtype === 'CODING_EXERCISE'
                    ? `Python · ${question.allowedLanguages ? question.allowedLanguages.join('/') : 'Python'}`
                    : question.id.startsWith('Q_DA') ? 'SQL · sample.employees' : 'Python · sklearn + numpy'}
                </span>
                <button className="btn compact role" style={{ '--role-color': color, borderColor: color, color }} disabled={running} onClick={runSandbox}>
                  {running ? (lang === 'vi' ? '⏳ Đang chạy…' : '⏳ Running…') : `▶ ${lang === 'vi' ? 'Chạy' : 'Run'}`}
                </button>
              </div>
              <textarea className="textarea iv-editor"
                style={{ '--role-color': color, fontFamily:'var(--font-mono)', fontSize:13, minHeight:180, resize:'vertical' }}
                value={code}
                onChange={e => setCode(e.target.value)}
                readOnly={submitted}
                spellCheck={false}
              />
              {qtype === 'CODING_EXERCISE' && question.testCases && (
                <div>
                  <div className="mono muted" style={{ fontSize: 10, letterSpacing:'.18em', textTransform:'uppercase', marginBottom: 6 }}>TEST CASES</div>
                  <div className="stack" style={{ gap: 4 }}>
                    {question.testCases.map((tc, i) => (
                      <div key={i} className="mono" style={{ fontSize: 11, color:'var(--fg-3)', padding:'4px 10px', background:'var(--bg-3)', borderRadius:4 }}>
                        <span style={{ color:'var(--fg-5)' }}>#{i+1}</span> input: <span style={{ color:'var(--accent-cyan)' }}>{String(tc.input)}</span> → expected: <span style={{ color:'var(--accent-green)' }}>{String(tc.expected_output)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {question.constraints && (
                <div className="muted" style={{ fontSize: 11 }}>⚠ {question.constraints}</div>
              )}
              <div className="mono muted" style={{ fontSize: 10, letterSpacing:'.18em', textTransform:'uppercase' }}>OUTPUT</div>
              <div className="iv-sandbox-out">{sandboxOut || (lang === 'vi' ? '> chưa chạy. nhấn ▶ Chạy.' : '> not run yet. press ▶ Run.')}</div>
            </div>
          )}
          {tab === 'expert' && (
            <div className="card" style={{ background: 'rgba(0,0,0,.34)', padding: 16, borderLeft: `3px solid ${color}` }}>
              <h3 style={{ color }}>EXPERT REFERENCE</h3>
              <div style={{ fontSize: 14, color:'var(--fg-2)', lineHeight: 1.7 }}>{question.expert_en}</div>
            </div>
          )}

          <div className="row between" style={{ marginTop: 18 }}>
            <div className="mono muted" style={{ fontSize: 10, letterSpacing:'.12em', textTransform:'uppercase' }}>
              <span className="kbd">⌘</span> + <span className="kbd">↵</span> &nbsp; {lang === 'vi' ? 'để gửi' : 'to submit'}
            </div>
            {!submitted ? (
              <button className="btn primary"
                      disabled={!canSubmit}
                      style={{ opacity: canSubmit ? 1 : 0.4 }}
                      onClick={submit}>
                {t('interview.submit')}
              </button>
            ) : (
              <div className="row" style={{ gap: 10 }}>
                {!isAssessment && (
                  <button className="btn ghost compact" onClick={() => {
                    setSubmitted(false); setAnswer(''); setTab('answer'); setElapsed(0); setStreamed(false);
                    onNav('interview', { mode });
                  }}>
                    {lang === 'vi' ? '↻ Câu tiếp theo' : '↻ Next question'}
                  </button>
                )}
                <button className="btn role" style={{ '--role-color': color, borderColor: color, color }}
                        onClick={() => onNav('dashboard')}>
                  {isAssessment
                    ? (lang === 'vi' ? 'Xem radar của bạn →' : 'See your radar →')
                    : (lang === 'vi' ? 'Xem radar →' : 'View radar →')}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Side panel */}
        <div className="iv-side">
          <div className="card role-top" style={{ '--role-color': color }}>
            <h3 style={{ color }}>{lang === 'vi' ? 'BỘ ĐẾM GIỜ' : 'SESSION TIMER'}</h3>
            <div className="iv-timer" style={{ '--role-color': color }}>{mm}<span className="sep">:</span>{ss}</div>
            <div className="mono muted" style={{ fontSize: 10, letterSpacing:'.12em', textTransform:'uppercase', textAlign:'center' }}>
              {lang === 'vi' ? `Đề xuất ${question.estMin} phút · không giới hạn cứng` : `Suggested ${question.estMin} min · no hard cap`}
            </div>
          </div>

          {submitted ? (
            <div className="card hot-top">
              <h3 style={{ color:'var(--accent-cyan)' }}>{t('interview.streaming').toUpperCase()}</h3>
              <div className="iv-stream">
                <StreamingText speed={28} text={lang === 'vi'
                  ? 'Câu trả lời tốt — bạn nhận diện được window function là đúng hướng. Một số điểm cần làm rõ:\n\n• DENSE_RANK chuẩn hơn ROW_NUMBER khi có lương trùng — bạn đã nhắc đến.\n• Edge case NULL: nên thêm WHERE salary IS NOT NULL hoặc dùng IGNORE NULLS.\n• Performance: nếu bảng lớn, cân nhắc index trên salary cột.\n\nTổng điểm: 7.5/10. SQL_FUNDAMENTALS +0.6.'
                  : 'Solid answer — you correctly identified the window function approach. A few points to clarify:\n\n• DENSE_RANK is more robust than ROW_NUMBER when salaries tie — you mentioned this.\n• Edge case for NULL: filter with WHERE salary IS NOT NULL or use IGNORE NULLS.\n• Performance: for large tables, consider an index on salary.\n\nOverall score: 7.5/10. SQL_FUNDAMENTALS +0.6.'} />
              </div>
            </div>
          ) : (
            <div className="card">
              <h3>{t('interview.whyKicker')}</h3>
              <div className="muted" style={{ fontSize: 13, lineHeight: 1.6 }}>{t('interview.why')}</div>
              <div className="row wrap" style={{ gap: 6, marginTop: 12 }}>
                {question.tags.slice(0, 3).map(tg => <span key={tg} className="chip">#{tg}</span>)}
              </div>
            </div>
          )}

          <div className="card">
            <h3>{lang === 'vi' ? 'KỸ NĂNG ĐƯỢC DÒ' : 'SKILLS PROBED'}</h3>
            <div className="stack" style={{ gap: 6 }}>
              {question.tags.map(t2 => (
                <div key={t2} className="row between" style={{ paddingBottom: 6, borderBottom: '1px solid var(--line-soft)', fontSize: 11 }}>
                  <span className="mono muted">#{t2}</span>
                  <span className="mono" style={{ color }}>active</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Custom mode config (only when mode === 'custom') */}
      {mode === 'custom' && !submitted && (
        <div className="card warn-top" style={{ marginTop: 22 }}>
          <h3 style={{ color:'var(--accent-warn)' }}>{lang === 'vi' ? 'CẤU HÌNH CUSTOM' : 'CUSTOM CONFIG'}</h3>
          <div className="split-3">
            <div className="slider-row">
              <div className="mono" style={{ fontSize: 11, textTransform:'uppercase' }}>{lang === 'vi' ? 'Thời gian' : 'Duration'}</div>
              <input type="range" min={5} max={120} step={5} defaultValue={state.customMode.duration} className="slider"
                     onChange={(e) => set({ customMode: { ...state.customMode, duration: parseInt(e.target.value) } })} />
              <div className="mono warn-c">{state.customMode.duration}m</div>
            </div>
            <div className="slider-row">
              <div className="mono" style={{ fontSize: 11, textTransform:'uppercase' }}>{lang === 'vi' ? 'Số câu' : 'Questions'}</div>
              <input type="range" min={1} max={20} defaultValue={state.customMode.questionCount} className="slider"
                     onChange={(e) => set({ customMode: { ...state.customMode, questionCount: parseInt(e.target.value) } })} />
              <div className="mono warn-c">{state.customMode.questionCount}q</div>
            </div>
            <div>
              <div className="mono" style={{ fontSize: 10, color:'var(--fg-5)', letterSpacing:'.18em', textTransform:'uppercase', marginBottom: 6 }}>{lang === 'vi' ? 'Độ khó' : 'Difficulty'}</div>
              <select className="select" value={state.customMode.difficulty} onChange={(e) => set({ customMode: { ...state.customMode, difficulty: e.target.value } })}>
                <option value="beginner">BEGINNER</option>
                <option value="mixed">MIXED</option>
                <option value="advanced">ADVANCED</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ============================================================
// QUESTION LIBRARY — browse + filter
// ============================================================
function QuestionsScreen({ onNav }) {
  const { state, t } = useStore();
  const [filterRole, setFilterRole] = React.useState(state.role || 'ALL');
  const [filterDiff, setFilterDiff] = React.useState('ALL');
  const [filterStatus, setFilterStatus] = React.useState('ALL');
  const [search, setSearch] = React.useState('');

  const filtered = QUESTIONS.filter(q => {
    if (filterRole !== 'ALL' && q.role !== filterRole) return false;
    if (filterDiff !== 'ALL' && q.difficulty !== filterDiff) return false;
    const isDone = state.completedQs.includes(q.id);
    const isBm = state.bookmarks.includes(q.id);
    if (filterStatus === 'DONE' && !isDone) return false;
    if (filterStatus === 'BOOKMARKED' && !isBm) return false;
    if (filterStatus === 'TODO' && (isDone || isBm)) return false;
    if (search) {
      const s = search.toLowerCase();
      const hay = (q.title_en + ' ' + q.title_vi + ' ' + q.tags.join(' ') + ' ' + q.id).toLowerCase();
      if (!hay.includes(s)) return false;
    }
    return true;
  });

  return (
    <>
      <PageHead
        kicker={t('lib.kicker')}
        title={t('lib.title')}
        right={[<span key="c" className="mono muted" style={{ fontSize: 12, letterSpacing:'.18em', textTransform:'uppercase' }}>{filtered.length} / {QUESTIONS.length}</span>]}
      />
      <div className="q-grid">
        <aside className="q-filters">
          <input className="input" placeholder={t('lib.searchPh')} value={search} onChange={(e) => setSearch(e.target.value)} />
          <div className="card" style={{ padding: 16 }}>
            <div className="label">{t('lib.filterRole')}</div>
            <div className="row wrap" style={{ gap: 6 }}>
              {['ALL','DA','DE','DS'].map(r => (
                <span key={r} className={`chip ${filterRole === r ? 'active' : ''}`}
                      style={r !== 'ALL' && filterRole === r ? { '--role-color': roleColor(r) } : {}}
                      onClick={() => setFilterRole(r)}>{r}</span>
              ))}
            </div>
            <div className="label" style={{ marginTop: 14 }}>{t('lib.filterDiff')}</div>
            <div className="row wrap" style={{ gap: 6 }}>
              {['ALL','BEGINNER','INTERMEDIATE','ADVANCED'].map(d => (
                <span key={d} className={`chip ${filterDiff === d ? 'active' : ''}`} onClick={() => setFilterDiff(d)}>{d}</span>
              ))}
            </div>
            <div className="label" style={{ marginTop: 14 }}>{t('lib.filterStatus')}</div>
            <div className="row wrap" style={{ gap: 6 }}>
              {['ALL','TODO','BOOKMARKED','DONE'].map(s => (
                <span key={s} className={`chip ${filterStatus === s ? 'active' : ''}`} onClick={() => setFilterStatus(s)}>{s}</span>
              ))}
            </div>
          </div>
          <div className="alert">
            <span className="dot"></span>
            <div>{state.lang === 'vi' ? 'Spaced repetition đề xuất 3 câu hôm nay. Tag #DUE.' : 'Spaced repetition suggests 3 questions today. Tag #DUE.'}</div>
          </div>
        </aside>
        <div>
          {filtered.length === 0 && (
            <div className="card raised" style={{ textAlign:'center', padding: 40 }}>
              <div className="mono muted" style={{ letterSpacing:'.22em', textTransform:'uppercase' }}>NO MATCHES</div>
            </div>
          )}
          {filtered.map(q => {
            const isDone = state.completedQs.includes(q.id);
            const isBm = state.bookmarks.includes(q.id);
            const title = state.lang === 'vi' && q.title_vi ? q.title_vi : q.title_en;
            return (
              <div key={q.id} className="q-row" style={{ '--role-color': roleColor(q.role) }} onClick={() => onNav('interview', { qid: q.id })}>
                <div>
                  <div className="qtitle">{title}</div>
                  <div className="qmeta">
                    <span className="chip" style={{ '--role-color': roleColor(q.role), borderColor: roleColor(q.role), color: roleColor(q.role) }}>{q.role}</span>
                    <span className="chip">{q.id}</span>
                    {q.tags.slice(0, 3).map(t2 => <span key={t2} className="chip muted">#{t2}</span>)}
                  </div>
                </div>
                <div className="qright">
                  <span className="diff">{q.difficulty}</span>
                  <span className="muted">{q.estMin} MIN</span>
                  {isDone && <span className="status done">✓ DONE</span>}
                  {!isDone && isBm && <span className="status bookmarked">★ SAVED</span>}
                  {!isDone && !isBm && <span className="status">○ TODO</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}

Object.assign(window, { HomeScreen, InterviewScreen, QuestionsScreen });
