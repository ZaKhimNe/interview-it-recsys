// ============================================================
// screens-diagnostic.jsx — Multi-stage Testing (MST)
// ============================================================

function DiagnosticScreen({ onNav }) {
  const { state, set } = useStore();
  const role = state.role;
  const vi = state.lang === 'vi';
  const color = roleColor(role);
  const mst = state.mst || {};

  const [tab, setTab] = React.useState('answer');
  const [submitted, setSubmitted] = React.useState(false);
  const [selectedOption, setSelectedOption] = React.useState('');
  const [boolAnswer, setBoolAnswer] = React.useState(null);
  const [blankAnswers, setBlankAnswers] = React.useState([]);
  const [answer, setAnswer] = React.useState('');
  const [code, setCode] = React.useState('');
  const [showGate, setShowGate] = React.useState(false);

  // Init MST on mount if not active
  React.useEffect(() => {
    if (!mst.active && !mst.done) {
      const s1Qs = pickStage1(role);
      set(s => ({ ...s,
        mst: {
          active: true, stage: 1,
          s1Ids: s1Qs.map(q => q.id), s1Results: [],
          s2Ids: [], s2Results: [],
          routing: null, done: false,
          startedAt: new Date().toISOString(),
        }
      }));
    }
  }, []);

  const stage     = mst.stage || 1;
  const s1Results = mst.s1Results || [];
  const s2Results = mst.s2Results || [];
  const s1Ids     = mst.s1Ids || [];
  const s2Ids     = mst.s2Ids || [];
  const curResults = stage === 1 ? s1Results : s2Results;
  const curIds     = stage === 1 ? s1Ids     : s2Ids;

  // When submitted=true, show the question just answered (length-1); else next (length)
  const curIdx  = submitted ? curResults.length - 1 : curResults.length;
  const question = curIds[curIdx] ? QUESTIONS.find(q => q.id === curIds[curIdx]) : null;

  React.useEffect(() => {
    if (!question) return;
    setTab('answer'); setSubmitted(false);
    setSelectedOption(''); setBoolAnswer(null); setAnswer('');
    setCode(question.starterCode || '');
    const blanks = (question.template || '').split('[___]').length - 1;
    setBlankAnswers(Array(Math.max(blanks, 0)).fill(''));
  }, [question && question.id]);

  const qtype = (question && question.questionType) || 'THEORY';

  const canSubmit = (() => {
    if (!question || submitted) return false;
    if (qtype === 'MC_SINGLE')       return !!selectedOption;
    if (qtype === 'TRUE_FALSE')      return boolAnswer !== null;
    if (qtype === 'FILL_BLANK')      return blankAnswers.length > 0 && blankAnswers.every(b => b.trim());
    if (qtype === 'CODING_EXERCISE') return code.trim().length > 10;
    return answer.trim().length > 0;
  })();

  const handleSubmit = () => {
    if (!question) return;
    const result = scoreAnswer(question, { answer, selectedOption, boolAnswer, blankAnswers, code });
    const newResult = {
      qId: question.id, score: result.score, isCorrect: result.isCorrect,
      groups: question.skillGroups || [], diffScore: question.difficultyScore || 5,
    };
    setSubmitted(true);
    if (!['MC_SINGLE','TRUE_FALSE','FILL_BLANK'].includes(qtype)) setTab('expert');

    if (stage === 1) {
      const newS1 = [...s1Results, newResult];
      if (newS1.length >= s1Ids.length && s1Ids.length > 0) {
        const avg     = mstAvgScore(newS1);
        const routing = mstRouting(avg);
        const weakGroups = newS1.filter(r => r.score < 0.5).flatMap(r => r.groups);
        const s2Qs = pickStage2(role, routing, s1Ids, weakGroups);
        set(s => ({ ...s, mst: { ...s.mst, s1Results: newS1, routing, s2Ids: s2Qs.map(q => q.id) } }));
      } else {
        set(s => ({ ...s, mst: { ...s.mst, s1Results: newS1 } }));
      }
    } else {
      const newS2 = [...s2Results, newResult];
      if (newS2.length >= s2Ids.length && s2Ids.length > 0) {
        const allR     = [...s1Results, ...newS2];
        const avgScore = mstAvgScore(allR);
        const avgDiff  = Math.round(allR.reduce((s, r) => s + r.diffScore, 0) / allR.length);
        const delta    = calcDelta(avgScore, avgDiff);
        const axes     = SKILL_AXES[role] || [];
        const rawVec   = currentVector(state) || [];
        const curVec   = axes.map((_, i) => rawVec[i] ?? 0);
        const newVector = curVec.map((v, i) => {
          const tgt = (ROLE_TARGETS[role] || [])[i] ?? 10;
          return parseFloat(Math.max(0, Math.min(tgt, v + delta)).toFixed(2));
        });
        const newAttempt = {
          id: `mst-${Date.now()}`, date: new Date().toISOString().slice(0, 10),
          role, vector: newVector, source: 'MST',
        };
        const newCompleted = [...new Set([...state.completedQs, ...s1Ids, ...s2Ids])];
        set(s => ({ ...s,
          mst: { ...s.mst, s2Results: newS2, done: true, active: false },
          attempts: [...s.attempts, newAttempt],
          completedQs: newCompleted,
        }));
      } else {
        set(s => ({ ...s, mst: { ...s.mst, s2Results: newS2 } }));
      }
    }
  };

  const handleNext = () => {
    const stage1Done = stage === 1 && s1Results.length >= s1Ids.length && s1Ids.length > 0;
    if (stage1Done) { setShowGate(true); }
    else { setSubmitted(false); setTab('answer'); }
  };

  const exitMST = () => {
    const msg = vi ? 'Thoat? Tien trinh se bi mat.' : 'Exit? Progress will be lost.';
    if (confirm(msg)) {
      set(s => ({ ...s, mst: { active:false,stage:1,s1Ids:[],s1Results:[],s2Ids:[],s2Results:[],routing:null,done:false,startedAt:null } }));
      onNav('home');
    }
  };

  // ── RESULT ──────────────────────────────────────────────────
  if (mst.done) return (
    <MSTResult mst={mst} role={role} color={color} vi={vi} state={state} onNav={onNav} set={set} />
  );

  // ── GATE ────────────────────────────────────────────────────
  if (showGate) {
    const avg = mstAvgScore(s1Results);
    const routing = mst.routing || 'MID';
    const RINFO = {
      WEAK:   { label: vi ? 'CAN CUNG CO' : 'BUILD FOUNDATION', col: '#a3ff12',
                desc:  vi ? '4 cau co ban + 2 cau trung binh' : '4 beginner + 2 intermediate' },
      MID:    { label: vi ? 'DANG TIEN BO' : 'ON TRACK',        col: '#fde047',
                desc:  vi ? '2 cau co ban + 2 trung binh + 2 kho' : '2 beginner + 2 intermediate + 2 advanced' },
      STRONG: { label: vi ? 'THANH THAO' : 'STRONG',           col: '#ff3366',
                desc:  vi ? '2 cau trung binh + 4 cau kho' : '2 intermediate + 4 advanced' },
    };
    const info = RINFO[routing] || RINFO.MID;
    return (
      <div style={{ display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',minHeight:'60vh',gap:24,padding:'40px 20px' }}>
        <div className="mono" style={{ fontSize:10,color:'var(--fg-5)',letterSpacing:'.22em',textTransform:'uppercase' }}>
          {vi ? 'GIAI DOAN 1 HOAN TAT' : 'STAGE 1 COMPLETE'}
        </div>
        <div style={{ textAlign:'center' }}>
          <div className="mono" style={{ fontSize:10,color:info.col,letterSpacing:'.22em',textTransform:'uppercase',marginBottom:8 }}>
            {vi ? 'KET QUA DINH VI' : 'ROUTING RESULT'}
          </div>
          <div style={{ fontFamily:'var(--font-sans)',fontSize:38,fontWeight:950,color:info.col,letterSpacing:'-.04em',textTransform:'uppercase',lineHeight:1 }}>
            {info.label}
          </div>
          <div className="muted" style={{ fontSize:14,marginTop:10 }}>
            {vi ? `Diem trung binh: ${(avg*100).toFixed(0)}%` : `Avg score: ${(avg*100).toFixed(0)}%`}
            {' · '}{info.desc}
          </div>
        </div>
        <div style={{ display:'flex',gap:8 }}>
          {s1Results.map((r,i) => {
            const sc = r.isCorrect === true ? 'var(--success)' : r.isCorrect === false ? 'var(--danger)' : 'var(--accent-warn)';
            return (
              <div key={i} style={{ width:48,height:48,borderRadius:8,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',
                background:`${sc}18`,border:`1.5px solid ${sc}`,fontFamily:'var(--font-mono)',gap:1 }}>
                <span style={{ fontSize:13,fontWeight:700,color:sc }}>{(r.score*100).toFixed(0)}</span>
                <span style={{ fontSize:9,color:'var(--fg-5)' }}>Q{i+1}</span>
              </div>
            );
          })}
        </div>
        <button className="btn primary" onClick={() => {
          set(s => ({ ...s, mst: { ...s.mst, stage:2 } }));
          setShowGate(false); setSubmitted(false); setTab('answer');
        }}>
          {vi ? 'Bat dau Stage 2 →' : 'Start Stage 2 →'}
        </button>
        <button className="btn ghost compact" onClick={exitMST}>{vi ? 'Thoat' : 'Exit'}</button>
      </div>
    );
  }

  // ── LOADING ─────────────────────────────────────────────────
  if (!mst.active || !question) return (
    <div className="card" style={{ padding:40,textAlign:'center' }}>
      <div className="mono muted" style={{ letterSpacing:'.18em',textTransform:'uppercase' }}>Initializing...</div>
    </div>
  );

  // ── PROGRESS BAR ─────────────────────────────────────────────
  const totalStage = stage === 1 ? s1Ids.length : s2Ids.length;
  const displayNum = curIdx + 1;
  const title = vi && question.title_vi ? question.title_vi : question.title_en;
  const body  = vi && question.body_vi  ? question.body_vi  : question.body_en;

  const barColor = (res) => res
    ? (res.isCorrect === true ? 'var(--success)' : res.isCorrect === false ? 'var(--danger)' : 'var(--accent-warn)')
    : 'var(--bg-4)';

  return (
    <>
      <PageHead
        kicker={vi ? `DANH GIA NANG LUC · GIAI DOAN ${stage}` : `DIAGNOSTIC TEST · STAGE ${stage}`}
        title={vi ? 'Cau hoi danh gia' : 'Assessment Question'}
        right={[<button key="x" className="btn ghost compact" onClick={exitMST}>{vi ? 'Thoat' : 'Exit'}</button>]}
      />

      {/* Progress */}
      <div style={{ marginBottom:16 }}>
        <div className="row between" style={{ marginBottom:6 }}>
          <div className="mono muted" style={{ fontSize:10,letterSpacing:'.18em',textTransform:'uppercase' }}>
            {vi ? `GIAI DOAN ${stage} · CAU ${displayNum}/${totalStage}` : `STAGE ${stage} · Q${displayNum}/${totalStage}`}
          </div>
          <div className="mono" style={{ fontSize:10,color,letterSpacing:'.12em' }}>
            {stage === 1 ? (vi ? 'DINH VI' : 'PLACEMENT') : (mst.routing || 'MID')}
          </div>
        </div>
        <div style={{ display:'flex',gap:3,marginBottom:3 }}>
          {s1Ids.map((id,i) => {
            const active = stage===1 && i===curResults.length && !submitted;
            const bg = s1Results[i] ? barColor(s1Results[i]) : active ? color : 'var(--bg-4)';
            return <div key={id} style={{ flex:1,height:4,borderRadius:2,background:bg,transition:'background .3s' }} />;
          })}
        </div>
        {s2Ids.length > 0 && (
          <div style={{ display:'flex',gap:3 }}>
            {s2Ids.map((id,i) => {
              const active = stage===2 && i===s2Results.length && !submitted;
              const bg = s2Results[i] ? barColor(s2Results[i]) : active ? color : 'var(--bg-3)';
              return <div key={id} style={{ flex:1,height:4,borderRadius:2,background:bg,transition:'background .3s',opacity:stage===2?1:0.35 }} />;
            })}
          </div>
        )}
      </div>

      <div className="iv-workbench">
        <div className="card raised role-top" style={{ '--role-color':color }}>
          <div className="row wrap" style={{ gap:6,marginBottom:10 }}>
            {(question.tags||[]).map(t2 => <span key={t2} className="chip role" style={{ '--role-color':color,borderColor:color,color }}>#{t2}</span>)}
            <span className="chip" style={{ marginLeft:'auto' }}>{question.difficulty}</span>
          </div>
          <div style={{ fontFamily:'var(--font-sans)',fontSize:22,fontWeight:800,color:'var(--fg-0)',letterSpacing:'-.01em',lineHeight:1.25,marginBottom:10 }}>{title}</div>
          <div className="muted" style={{ fontSize:14,lineHeight:1.6,marginBottom:16 }}>{body}</div>

          <div className="iv-tabs">
            <button className={`iv-tab ${tab==='answer'?'active':''}`} style={{ '--role-color':color }} onClick={() => setTab('answer')}>
              {vi ? 'Tra loi' : 'Answer'}
            </button>
            {submitted && (
              <button className={`iv-tab ${tab==='expert'?'active':''}`} style={{ '--role-color':color }} onClick={() => setTab('expert')}>
                {vi ? 'Dap an' : 'Expert answer'}
              </button>
            )}
          </div>

          {/* Answer tab */}
          {tab === 'answer' && (() => {
            if (qtype === 'MC_SINGLE') {
              const opts2 = question.options || [];
              const correctId = question.correctOptionId;
              return (
                <div className="stack" style={{ gap:10,marginTop:8 }}>
                  {opts2.map(opt => {
                    const isSel = selectedOption === opt.id;
                    const isCorr = submitted && opt.id === correctId;
                    const isWrong = submitted && isSel && opt.id !== correctId;
                    const bc = isCorr ? 'var(--success)' : isWrong ? 'var(--danger)' : isSel ? color : 'var(--line-med)';
                    return (
                      <button key={opt.id} onClick={() => !submitted && setSelectedOption(opt.id)}
                        style={{ textAlign:'left',padding:'12px 16px',borderRadius:8,border:`2px solid ${bc}`,
                          background:isSel?`${color}18`:'var(--bg-3)',
                          color:isCorr?'var(--success)':isWrong?'var(--danger)':'var(--fg-0)',
                          cursor:submitted?'default':'pointer',fontSize:14,fontFamily:'var(--font-sans)',transition:'all .15s' }}>
                        <span className="mono" style={{ color:bc,marginRight:10,fontWeight:700 }}>{opt.id}.</span>
                        {opt.text}{isCorr && ' ✓'}{isWrong && ' ✗'}
                      </button>
                    );
                  })}
                  {submitted && question.explanation && (
                    <div className="muted" style={{ fontSize:13,padding:'10px 14px',background:'var(--bg-3)',borderRadius:6,borderLeft:`3px solid ${color}`,lineHeight:1.6 }}>
                      {question.explanation}
                    </div>
                  )}
                </div>
              );
            }

            if (qtype === 'TRUE_FALSE') {
              const correct = question.correctAnswer;
              return (
                <div className="stack" style={{ gap:10,marginTop:8 }}>
                  <div className="row" style={{ gap:12 }}>
                    {[true,false].map(val => {
                      const isSel = boolAnswer === val;
                      const isCorr = submitted && val === correct;
                      const isWrong = submitted && isSel && val !== correct;
                      const bc = isCorr ? 'var(--success)' : isWrong ? 'var(--danger)' : isSel ? color : 'var(--line-med)';
                      return (
                        <button key={String(val)} onClick={() => !submitted && setBoolAnswer(val)}
                          style={{ flex:1,padding:'18px 0',borderRadius:8,border:`2px solid ${bc}`,
                            background:isSel?`${color}18`:'var(--bg-3)',
                            color:isCorr?'var(--success)':isWrong?'var(--danger)':'var(--fg-0)',
                            cursor:submitted?'default':'pointer',fontSize:16,fontWeight:700,fontFamily:'var(--font-mono)',transition:'all .15s' }}>
                          {val ? 'TRUE ✓' : 'FALSE ✗'}
                        </button>
                      );
                    })}
                  </div>
                  {submitted && question.explanation && (
                    <div className="muted" style={{ fontSize:13,padding:'10px 14px',background:'var(--bg-3)',borderRadius:6,borderLeft:`3px solid ${color}`,lineHeight:1.6 }}>
                      {question.explanation}
                    </div>
                  )}
                </div>
              );
            }

            if (qtype === 'FILL_BLANK') {
              const tmpl = question.template || question.body_vi || '';
              const parts = tmpl.split('[___]');
              return (
                <div className="stack" style={{ gap:12,marginTop:8 }}>
                  <div style={{ fontSize:14,lineHeight:2,color:'var(--fg-1)' }}>
                    {parts.map((part,i) => (
                      <React.Fragment key={i}>
                        {part}
                        {i < parts.length-1 && (
                          <input value={blankAnswers[i]||''} readOnly={submitted}
                            onChange={e => { const n=[...blankAnswers]; n[i]=e.target.value; setBlankAnswers(n); }}
                            placeholder={`(${i+1})`}
                            style={{ display:'inline-block',width:140,margin:'0 6px',padding:'4px 10px',borderRadius:6,
                              border:`1.5px solid ${submitted?(blankAnswers[i]?'var(--success)':'var(--danger)'):color}`,
                              background:'var(--bg-3)',color:'var(--fg-0)',fontFamily:'var(--font-mono)',fontSize:13 }} />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                  {submitted && question.explanation && (
                    <div className="muted" style={{ fontSize:13,padding:'10px 14px',background:'var(--bg-3)',borderRadius:6,borderLeft:`3px solid ${color}`,lineHeight:1.6 }}>
                      {question.explanation}
                    </div>
                  )}
                </div>
              );
            }

            return (
              <textarea className="textarea" style={{ '--role-color':color,minHeight:200 }}
                placeholder={vi ? '// go cau tra loi o day...' : '// type your answer here...'}
                value={answer} onChange={e => setAnswer(e.target.value)} readOnly={submitted} />
            );
          })()}

          {tab === 'expert' && (
            <div className="card" style={{ background:'rgba(0,0,0,.34)',padding:16,borderLeft:`3px solid ${color}` }}>
              <h3 style={{ color }}>EXPERT REFERENCE</h3>
              <div style={{ fontSize:14,color:'var(--fg-2)',lineHeight:1.7 }}>{question.expert_en}</div>
            </div>
          )}

          <div className="row between" style={{ marginTop:18 }}>
            <div />
            {!submitted ? (
              <button className="btn primary" disabled={!canSubmit} style={{ opacity:canSubmit?1:0.4 }} onClick={handleSubmit}>
                {vi ? 'Gui →' : 'Submit →'}
              </button>
            ) : (
              <button className="btn role" style={{ '--role-color':color,borderColor:color,color }} onClick={handleNext}>
                {stage===1 && s1Results.length>=s1Ids.length
                  ? (vi ? 'Xem ket qua Stage 1 →' : 'View Stage 1 result →')
                  : (vi ? 'Cau tiep theo →' : 'Next question →')}
              </button>
            )}
          </div>
        </div>

        {/* Side panel */}
        <div className="iv-side">
          <div className="card role-top" style={{ '--role-color':color }}>
            <h3 style={{ color }}>{vi ? 'TIEN TRINH' : 'PROGRESS'}</h3>
            <div style={{ fontFamily:'var(--font-mono)',fontSize:36,fontWeight:950,color,textAlign:'center',padding:'12px 0' }}>
              {displayNum}<span style={{ fontSize:16,color:'var(--fg-5)' }}>/{totalStage}</span>
            </div>
            <div className="mono muted" style={{ fontSize:10,letterSpacing:'.12em',textAlign:'center',textTransform:'uppercase' }}>
              {vi ? `GIAI DOAN ${stage} / 2` : `STAGE ${stage} OF 2`}
            </div>
          </div>

          <div className="card">
            <h3>{vi ? 'THONG TIN CAU HOI' : 'QUESTION INFO'}</h3>
            <div className="stack" style={{ gap:8 }}>
              <div className="row between" style={{ fontSize:11 }}>
                <span className="mono muted">TYPE</span>
                <span className="mono" style={{ color }}>{qtype}</span>
              </div>
              <div className="row between" style={{ fontSize:11 }}>
                <span className="mono muted">DIFF</span>
                <span className="mono warn-c">{question.difficulty}</span>
              </div>
              <div className="row between" style={{ fontSize:11 }}>
                <span className="mono muted">SCORE</span>
                <span className="mono" style={{ color:['MC_SINGLE','TRUE_FALSE','FILL_BLANK'].includes(qtype)?'var(--success)':'var(--accent-warn)' }}>
                  {['MC_SINGLE','TRUE_FALSE','FILL_BLANK'].includes(qtype)
                    ? (vi ? 'TU DONG' : 'AUTO')
                    : 'SLM (0.5)'}
                </span>
              </div>
            </div>
          </div>

          {stage === 1 ? (
            <div className="card warn-top">
              <h3 style={{ color:'var(--accent-warn)' }}>{vi ? 'GIAI DOAN 1 · DINH VI' : 'STAGE 1 · PLACEMENT'}</h3>
              <div className="muted" style={{ fontSize:12,lineHeight:1.6 }}>
                {vi
                  ? '4 cau INTERMEDIATE de dinh vi nang luc. Sau do he thong chon bai phu hop voi trinh do cua ban.'
                  : '4 INTERMEDIATE questions to calibrate your level. Stage 2 will be tailored to your performance.'}
              </div>
            </div>
          ) : (
            <div className="card" style={{ borderTop:`3px solid ${mst.routing==='STRONG'?'var(--danger)':mst.routing==='WEAK'?'var(--success)':'var(--accent-warn)'}` }}>
              <h3>{vi ? 'DINH TUYEN' : 'ROUTING'}</h3>
              <div style={{ fontFamily:'var(--font-mono)',fontSize:16,fontWeight:900,textTransform:'uppercase',
                color:mst.routing==='STRONG'?'var(--danger)':mst.routing==='WEAK'?'var(--success)':'var(--accent-warn)' }}>
                {mst.routing==='STRONG'?(vi?'THANH THAO':'STRONG')
                  :mst.routing==='WEAK'?(vi?'CAN CUNG CO':'BUILD FOUNDATION')
                  :(vi?'DANG TIEN BO':'ON TRACK')}
              </div>
              <div className="muted" style={{ fontSize:11,marginTop:4 }}>
                {vi ? `Diem Stage 1: ${(mstAvgScore(s1Results)*100).toFixed(0)}%` : `Stage 1 score: ${(mstAvgScore(s1Results)*100).toFixed(0)}%`}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

// ── MST RESULT ──────────────────────────────────────────────────
function MSTResult({ mst, role, color, vi, state, onNav, set }) {
  const allR       = [...(mst.s1Results||[]), ...(mst.s2Results||[])];
  const avgScore   = mstAvgScore(allR);
  const autoGraded = allR.filter(r => r.isCorrect !== null);
  const correct    = autoGraded.filter(r => r.isCorrect === true).length;

  const RINFO = {
    WEAK:   { label: vi ? 'CAN CUNG CO' : 'BUILD FOUNDATION', col: '#a3ff12' },
    MID:    { label: vi ? 'DANG TIEN BO' : 'ON TRACK',        col: '#fde047' },
    STRONG: { label: vi ? 'THANH THAO' : 'STRONG',            col: '#ff3366' },
  };
  const info = RINFO[mst.routing] || RINFO.MID;
  const s1Len = (mst.s1Ids||[]).length;

  const resetMST = () => set(s => ({ ...s,
    mst: { active:false,stage:1,s1Ids:[],s1Results:[],s2Ids:[],s2Results:[],routing:null,done:false,startedAt:null }
  }));

  return (
    <>
      <PageHead
        kicker={vi ? 'KET QUA DANH GIA NANG LUC' : 'DIAGNOSTIC COMPLETE'}
        title={vi ? 'Ket qua' : 'Your Results'}
      />
      <div className="split-2" style={{ alignItems:'start',gap:24 }}>
        <div className="stack" style={{ gap:16 }}>

          {/* Routing result */}
          <div className="card" style={{ borderTop:`4px solid ${info.col}`,padding:24 }}>
            <div className="mono" style={{ fontSize:10,color:info.col,letterSpacing:'.22em',marginBottom:8 }}>
              {vi ? 'KET QUA DINH VI' : 'ROUTING RESULT'}
            </div>
            <div style={{ fontFamily:'var(--font-sans)',fontSize:34,fontWeight:950,color:info.col,textTransform:'uppercase',letterSpacing:'-.03em' }}>
              {info.label}
            </div>
            <div className="muted" style={{ fontSize:13,marginTop:8 }}>
              {vi
                ? `Diem TB: ${(avgScore*100).toFixed(0)}% · Tu dong cham: ${correct}/${autoGraded.length} dung`
                : `Avg: ${(avgScore*100).toFixed(0)}% · Auto-graded: ${correct}/${autoGraded.length} correct`}
            </div>
          </div>

          {/* Question breakdown */}
          <div className="card">
            <h3>{vi ? 'CHI TIET TUNG CAU' : 'QUESTION BREAKDOWN'}</h3>
            <div className="stack" style={{ gap:4 }}>
              {allR.map((r,i) => {
                const q = QUESTIONS.find(q2 => q2.id === r.qId);
                const isS1 = i < s1Len;
                const sc = r.isCorrect===true?'var(--success)':r.isCorrect===false?'var(--danger)':'var(--accent-warn)';
                const ttl = q ? (vi&&q.title_vi?q.title_vi:q.title_en) : r.qId;
                return (
                  <div key={r.qId} style={{ padding:'7px 10px',background:'var(--bg-3)',borderRadius:6,display:'flex',alignItems:'center',gap:10 }}>
                    <div className="mono" style={{ fontSize:10,color:'var(--fg-5)',minWidth:28 }}>
                      {isS1?`S1.${i+1}`:`S2.${i-s1Len+1}`}
                    </div>
                    <div style={{ flex:1,fontSize:12,color:'var(--fg-2)',overflow:'hidden',whiteSpace:'nowrap',textOverflow:'ellipsis' }}>
                      {ttl}
                    </div>
                    <div className="mono" style={{ fontSize:11,color:sc,fontWeight:700,minWidth:36,textAlign:'right' }}>
                      {r.isCorrect===null?'~SLM':`${(r.score*100).toFixed(0)}%`}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="stack" style={{ gap:16 }}>
          {/* Vector update */}
          <div className="card" style={{ padding:24 }}>
            <h3 style={{ color }}>{vi ? 'CAP NHAT VECTOR' : 'VECTOR UPDATE'}</h3>
            {(() => {
              const axes    = SKILL_AXES[role] || [];
              const attempts = state.attempts || [];
              const mstAttempt = [...attempts].reverse().find(a => a.source==='MST' && a.role===role);
              const prevAttempt = attempts.length>1 ? attempts[attempts.length-2] : null;
              const prevVec = (prevAttempt&&prevAttempt.role===role) ? prevAttempt.vector : axes.map(()=>0);
              const newVec  = mstAttempt ? mstAttempt.vector : axes.map(()=>0);
              return axes.map((ax,i) => {
                const pv = prevVec[i]??0;
                const nv = newVec[i]??0;
                const delta = parseFloat((nv-pv).toFixed(2));
                const deltaCol = delta>0?'var(--success)':delta<0?'var(--danger)':'var(--fg-5)';
                return (
                  <div key={ax} style={{ marginBottom:10 }}>
                    <div className="row between" style={{ fontSize:11,marginBottom:3 }}>
                      <span className="mono muted">{ax}</span>
                      <span style={{ fontFamily:'var(--font-mono)',fontSize:11 }}>
                        <span style={{ color:'var(--fg-1)' }}>{nv.toFixed(1)}</span>
                        <span style={{ color:'var(--fg-5)' }}>/10</span>
                        {delta!==0 && <span style={{ color:deltaCol,marginLeft:6 }}>{delta>0?'+':''}{delta}</span>}
                      </span>
                    </div>
                    <div style={{ height:4,background:'var(--bg-4)',borderRadius:2,overflow:'hidden' }}>
                      <div style={{ height:'100%',width:`${nv*10}%`,background:color,borderRadius:2 }} />
                    </div>
                  </div>
                );
              });
            })()}
          </div>

          <button className="btn primary full" style={{ fontSize:14 }} onClick={() => { resetMST(); onNav('dashboard'); }}>
            {vi ? 'Xem Dashboard →' : 'View Dashboard →'}
          </button>
          <button className="btn ghost compact full" onClick={() => { resetMST(); onNav('diagnostic'); }}>
            {vi ? '↻ Lam lai' : '↻ Retake'}
          </button>
          <button className="btn ghost compact full" onClick={() => { resetMST(); onNav('home'); }}>
            {vi ? '← Ve trang chu' : '← Back to home'}
          </button>
        </div>
      </div>
    </>
  );
}

window.DiagnosticScreen = DiagnosticScreen;
