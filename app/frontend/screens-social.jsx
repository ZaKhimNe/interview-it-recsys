// ============================================================
// screens-social.jsx — Notes, Settings
// ============================================================

// ============================================================
// NOTES
// ============================================================
function NotesScreen({ onNav }) {
  const { state, t } = useStore();
  const notes = state.notes || [];
  return (
    <>
      <PageHead
        kicker={t('notes.kicker')}
        title={t('notes.title')}
        right={[<button key="n" className="btn primary compact">+ {state.lang === 'vi' ? 'Ghi chú mới' : 'New note'}</button>]}
      />
      {notes.length === 0 ? (
        <EmptyState message="No notes yet" onNav={onNav} />
      ) : (
        <div className="split-2" style={{ alignItems:'start' }}>
          <div>
            {notes.map((n, i) => {
              const q = QUESTIONS.find(qq => qq.id === n.q);
              return (
                <div key={i} className="note-card">
                  <div className="nh">
                    <span className="nq">#{n.q}</span>
                    <span className="nd">{n.d}</span>
                  </div>
                  {q && <div style={{ fontFamily:'var(--font-sans)', fontSize: 15, fontWeight: 800, color:'var(--fg-0)', marginBottom: 8 }}>{state.lang === 'vi' && q.title_vi ? q.title_vi : q.title_en}</div>}
                  <div className="nb">{n.body}</div>
                </div>
              );
            })}
          </div>
          <div className="card warn-top">
            <h3 style={{ color:'var(--accent-warn)' }}>{state.lang === 'vi' ? 'GỢI Ý GHI CHÚ' : 'NOTE PROMPTS'}</h3>
            <div className="stack" style={{ gap: 14 }}>
              <div>
                <div className="mono cyan" style={{ fontSize: 10, letterSpacing:'.18em', marginBottom: 4 }}>WHAT</div>
                <div style={{ fontSize: 13, color:'var(--fg-3)' }}>{state.lang === 'vi' ? 'Concept chính của câu hỏi này là gì?' : 'What is the core concept this question probes?'}</div>
              </div>
              <div>
                <div className="mono cyan" style={{ fontSize: 10, letterSpacing:'.18em', marginBottom: 4 }}>WHY</div>
                <div style={{ fontSize: 13, color:'var(--fg-3)' }}>{state.lang === 'vi' ? 'Tại sao cách tiếp cận này tốt hơn cách khác?' : 'Why is this approach better than the alternative?'}</div>
              </div>
              <div>
                <div className="mono cyan" style={{ fontSize: 10, letterSpacing:'.18em', marginBottom: 4 }}>EDGE</div>
                <div style={{ fontSize: 13, color:'var(--fg-3)' }}>{state.lang === 'vi' ? 'Edge case nào dễ bỏ sót?' : 'What edge cases are easy to miss?'}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ============================================================
// SETTINGS
// ============================================================
function SettingsScreen({ onNav }) {
  const { state, set, t } = useStore();
  const Toggle = ({ on, onChange, label }) => (
    <div className={`toggle ${on ? 'on' : ''}`} onClick={() => onChange(!on)}>
      <div className="track"><div className="knob"></div></div>
      <span className="lbl">{label}</span>
    </div>
  );

  return (
    <>
      <PageHead kicker={t('settings.kicker')} title={t('settings.title')}
                right={[<button key="r" className="btn ghost compact" onClick={() => { if (confirm('Reset all data?')) { localStorage.removeItem(STORAGE_KEY); location.reload(); } }}>↺ Reset all data</button>]} />

      <div className="settings-section">
        <div>
          <div className="sl-title">{t('settings.sysLang')}</div>
          <div className="sl-sub">{t('settings.sysLangSub')}</div>
        </div>
        <div>
          <div className="row" style={{ gap: 10 }}>
            <span className={`chip ${state.lang === 'en' ? 'active' : ''}`} onClick={() => set({ lang: 'en' })}>EN · English</span>
            <span className={`chip ${state.lang === 'vi' ? 'active' : ''}`} onClick={() => set({ lang: 'vi' })}>VI · Tiếng Việt</span>
          </div>
        </div>
      </div>

      <div className="settings-section">
        <div>
          <div className="sl-title">{t('settings.sysRole')}</div>
          <div className="sl-sub">{t('settings.sysRoleSub')}</div>
        </div>
        <div>
          <div className="row" style={{ gap: 10 }}>
            {['DA','DE','DS'].map(r => (
              <span key={r} className={`chip ${state.role === r ? 'active' : ''}`}
                    style={{ '--role-color': roleColor(r), borderColor: state.role === r ? roleColor(r) : 'var(--line-strong)', color: state.role === r ? roleColor(r) : 'var(--fg-2)' }}
                    onClick={() => set({ role: r })}>
                {r === 'DA' ? 'Data Analyst' : r === 'DE' ? 'Data Engineer' : 'Data Scientist'}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="settings-section">
        <div>
          <div className="sl-title">{t('settings.sysAI')}</div>
          <div className="sl-sub">{t('settings.sysAISub')}</div>
        </div>
        <div className="stack" style={{ gap: 12 }}>
          <Toggle on={state.prefs.streamingFeedback} label={t('settings.sysStreaming')} onChange={(v) => set({ prefs: { ...state.prefs, streamingFeedback: v } })} />
          <Toggle on={state.prefs.spacedRepetition} label={t('settings.sysSpaced')} onChange={(v) => set({ prefs: { ...state.prefs, spacedRepetition: v } })} />
          <Toggle on={state.prefs.streamingFeedback} label={t('settings.sysWhy')} onChange={(v) => set({ prefs: { ...state.prefs, explainWhy: v } })} />
          <Toggle on={state.prefs.notifications} label={t('settings.sysNotif')} onChange={(v) => set({ prefs: { ...state.prefs, notifications: v } })} />
        </div>
      </div>

      <div className="settings-section">
        <div>
          <div className="sl-title">{t('settings.sysSandbox')}</div>
          <div className="sl-sub">{t('settings.sysSandboxSub')}</div>
        </div>
        <div>
          <Toggle on={state.prefs.sandboxAutorun} label={t('settings.sysAutorun')} onChange={(v) => set({ prefs: { ...state.prefs, sandboxAutorun: v } })} />
        </div>
      </div>

      <div className="settings-section">
        <div>
          <div className="sl-title">{t('settings.sysAccount')}</div>
          <div className="sl-sub">{t('settings.sysAccountSub')}</div>
        </div>
        <div className="split-2" style={{ gap: 14 }}>
          <div className="uploader">
            <div className="ic">📄</div>
            <div className="lbl1">{t('settings.uploadResume')}</div>
            <div className="lbl2">{t('settings.resumeHint')}</div>
          </div>
          <div className="uploader">
            <div className="ic">🔗</div>
            <div className="lbl1">{t('settings.uploadJD')}</div>
            <div className="lbl2">{t('settings.jdHint')}</div>
          </div>
        </div>
      </div>

      <div className="settings-section">
        <div>
          <div className="sl-title">{state.lang === 'vi' ? 'Dữ liệu cục bộ' : 'Local data'}</div>
          <div className="sl-sub">{state.lang === 'vi' ? 'Tất cả dữ liệu lưu trong trình duyệt. Không server, không tracking.' : 'All data stays in your browser. No server, no tracking.'}</div>
        </div>
        <div className="stack" style={{ gap: 12 }}>
          <div className="mono muted" style={{ fontSize: 12, letterSpacing:'.08em' }}>
            {state.lang === 'vi' ? 'NGƯỜI DÙNG' : 'USER'}: <span className="cyan">{state.user.name}</span>
          </div>
          <div className="mono muted" style={{ fontSize: 12, letterSpacing:'.08em' }}>
            ATTEMPTS: <span className="cyan">{state.attempts.length}</span> · NOTES: <span className="cyan">{state.notes.length}</span>
          </div>
          <div className="row" style={{ gap: 10 }}>
            <button className="btn ghost compact" onClick={() => {
              const blob = new Blob([JSON.stringify(state, null, 2)], { type:'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a'); a.href = url; a.download = `internhub-${state.user.name}.json`; a.click();
              URL.revokeObjectURL(url);
            }}>↓ {t('common.export')} JSON</button>
            <button className="btn ghost compact" onClick={() => {
              if (confirm(state.lang === 'vi' ? 'Đổi người dùng? Sẽ về màn hình chọn profile.' : 'Switch user?')) {
                localStorage.removeItem('internhub.current');
                location.reload();
              }
            }}>⇄ {state.lang === 'vi' ? 'Đổi profile' : 'Switch profile'}</button>
          </div>
        </div>
      </div>
    </>
  );
}

Object.assign(window, { NotesScreen, SettingsScreen });
