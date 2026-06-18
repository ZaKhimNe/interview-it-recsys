// ============================================================
// chrome.jsx — Sidebar, TopBar, PageHead, AnimatedBackground
// ============================================================

// Per-route background treatment. Each one different.
function AnimatedBackground({ route, role }) {
  const color = roleColor(role || 'DA');
  // Pick treatment per route.
  if (route === 'landing') {
    return (
      <div className="bg-canvas">
        <div className="bg-photo" style={{ position:'absolute', inset:0, backgroundImage:'url(../assets/onboarding_bg.png)' }} />
        <div className="bg-orb a" />
        <div className="bg-orb b" />
        <div className="bg-orb c" />
        <div className="bg-canvas bg-grid" style={{ opacity: 0.7 }} />
        <div className="bg-canvas bg-vignette" />
      </div>
    );
  }
  if (route === 'onboarding') {
    return (
      <div className="bg-canvas">
        <div className="bg-photo" style={{ position:'absolute', inset:0, backgroundImage:'url(../assets/onboarding_bg.png)', filter:'saturate(0.7)' }} />
        <div className="bg-orb a" />
        <div className="bg-orb b" style={{ opacity: 0.25 }} />
      </div>
    );
  }
  if (route === 'home') {
    return (
      <div className="bg-canvas">
        <div className="bg-canvas bg-grid" />
        <div className="bg-orb a" style={{ background: color, opacity: 0.2 }} />
        <div className="bg-orb b" style={{ background: '#ff3366', opacity: 0.15 }} />
      </div>
    );
  }
  if (route === 'interview') {
    return (
      <div className="bg-canvas">
        <div className="bg-canvas bg-scan" />
        <div className="bg-orb a" style={{ background: color, opacity: 0.18, top: '-20%', left: '60%' }} />
      </div>
    );
  }
  if (route === 'questions') {
    return (
      <div className="bg-canvas">
        <div className="bg-canvas bg-dots" />
      </div>
    );
  }
  if (route === 'dashboard') {
    return (
      <div className="bg-canvas">
        <div className="bg-canvas bg-grid" style={{ opacity: 0.5 }} />
        <div className="bg-orb a" style={{ background: color, opacity: 0.3 }} />
        <div className="bg-orb b" style={{ opacity: 0.2 }} />
      </div>
    );
  }
  if (route === 'roadmap') {
    return (
      <div className="bg-canvas">
        <div className="bg-photo" style={{ position:'absolute', inset:0, backgroundImage:'url(../assets/role_ds_bg.png)', opacity:0.5 }} />
        <div className="bg-orb c" style={{ opacity: 0.3 }} />
      </div>
    );
  }
  if (route === 'history') {
    return (
      <div className="bg-canvas">
        <div className="bg-canvas bg-scan" />
        <div className="bg-canvas bg-dots" style={{ opacity: 0.5 }} />
      </div>
    );
  }
  if (route === 'leaderboard') {
    return (
      <div className="bg-canvas">
        <div className="bg-photo" style={{ position:'absolute', inset:0, backgroundImage:'url(../assets/role_de_bg.png)', opacity:0.7 }} />
        <div className="bg-orb b" style={{ opacity: 0.4 }} />
      </div>
    );
  }
  if (route === 'pair') {
    return (
      <div className="bg-canvas">
        <div className="bg-canvas bg-grid" style={{ opacity: 0.3 }} />
        <div className="bg-orb a" />
        <div className="bg-orb c" style={{ opacity: 0.3 }} />
      </div>
    );
  }
  if (route === 'notes') {
    return (
      <div className="bg-canvas">
        <div className="bg-photo" style={{ position:'absolute', inset:0, backgroundImage:'url(../assets/role_ds_bg.png)', opacity:0.4 }} />
      </div>
    );
  }
  if (route === 'settings') {
    return (
      <div className="bg-canvas">
        <div className="bg-canvas bg-dots" style={{ opacity: 0.4 }} />
        <div className="bg-orb a" style={{ opacity: 0.15 }} />
      </div>
    );
  }
  // default
  return (
    <div className="bg-canvas">
      <div className="bg-canvas bg-grid" style={{ opacity: 0.4 }} />
    </div>
  );
}

// ---------------- SIDEBAR ---------------------------------------
function Sidebar({ route, onNav }) {
  const { state, t } = useStore();
  const color = state.role ? roleColor(state.role) : '#00e5ff';
  const sections = [
    { label: t('nav.practice'), items: [
      { id:'home',       idx:'01', label: t('nav_items.home') },
      { id:'interview',  idx:'02', label: t('nav_items.interview') },
      { id:'questions',  idx:'03', label: t('nav_items.questions') },
    ]},
    { label: t('nav.progress'), items: [
      { id:'dashboard', idx:'04', label: t('nav_items.dashboard') },
      { id:'roadmap',   idx:'05', label: t('nav_items.roadmap') },
      { id:'history',   idx:'06', label: t('nav_items.history') },
    ]},
    { label: t('nav.system'), items: [
      { id:'notes',     idx:'07', label: t('nav_items.notes') },
      { id:'settings',  idx:'08', label: t('nav_items.settings') },
      { id:'profile',   idx:'09', label: t('nav_items.profile') },
    ]},
  ];
  return (
    <aside className="sidebar">
      <div className="sb-brand">
        <a href="#/" style={{ textDecoration:'none' }} onClick={(e) => { e.preventDefault(); onNav('landing'); }}>
          <div className="mark">INTERN<span>HUB</span></div>
          <div className="sub">{t('appTag')} · v0.1</div>
        </a>
      </div>
      {sections.map((s, i) => (
        <div key={i} className="sb-section">
          <div className="sb-section-label">{s.label}</div>
          {s.items.map(it => (
            <a key={it.id} href={`#/${it.id}`} className={`sb-link ${route === it.id ? 'active' : ''}`}
               style={{ '--role-color': color }}
               onClick={(e) => { e.preventDefault(); onNav(it.id); }}>
              <span className="idx">{it.idx}</span>
              <span>{it.label}</span>
              <span className="dot"></span>
            </a>
          ))}
        </div>
      ))}
      <div className="sb-foot">
        <div className="sb-streak">
          <div className="n">{state.user.streak}<span style={{ fontSize:14, color:'var(--fg-5)', marginLeft:4 }}>d</span></div>
          <div className="l">{state.lang === 'vi' ? 'Chuỗi ngày luyện' : 'Day streak'}</div>
        </div>
      </div>
    </aside>
  );
}

// ---------------- TOPBAR ----------------------------------------
function TopBar({ route, crumb }) {
  const { state, set, t } = useStore();
  const color = state.role ? roleColor(state.role) : '#00e5ff';
  return (
    <div className="topbar">
      <span className="tb-crumb">{crumb || route.toUpperCase()}</span>
      <span className="tb-spacer"></span>
      {state.role && (
        <span className="tb-pill" style={{ '--role-color': color }}>
          <span className="dot"></span>
          <span style={{ color }}>{state.role}</span>
          <span style={{ color: 'var(--fg-5)' }}>
            {state.role === 'DA' ? (state.lang === 'vi' ? 'Phân tích dữ liệu' : 'Data Analyst') : state.role === 'DE' ? (state.lang === 'vi' ? 'Kỹ thuật dữ liệu' : 'Data Engineer') : (state.lang === 'vi' ? 'Khoa học dữ liệu' : 'Data Scientist')}
          </span>
        </span>
      )}
      <button
        className="tb-lang"
        onClick={() => set({ lang: state.lang === 'en' ? 'vi' : 'en' })}
        title="Toggle language"
      >
        {state.lang === 'en' ? 'EN · VI' : 'VI · EN'}
      </button>
    </div>
  );
}

// ---------------- PAGE HEAD -------------------------------------
function PageHead({ kicker, title, right }) {
  return (
    <div className="page-head">
      <div className="left">
        <div className="kicker">{kicker}</div>
        <h1>{title}</h1>
      </div>
      {right && <div className="right">{right}</div>}
    </div>
  );
}

function SpecStrip({ items }) {
  return (
    <div className="spec-strip">
      {items.map((s, i) => (
        <React.Fragment key={i}>
          {i > 0 && <span className="sep">/</span>}
          <span>{s}</span>
        </React.Fragment>
      ))}
    </div>
  );
}

Object.assign(window, { AnimatedBackground, Sidebar, TopBar, PageHead, SpecStrip });
