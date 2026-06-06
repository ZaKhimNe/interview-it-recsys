// ============================================================
// screens-public.jsx — UserGate, Landing, Onboarding, Profile
// ============================================================

// ============================================================
// USER GATE — màn hình đầu tiên, chọn / tạo profile
// ============================================================
function UserGateScreen({ onEnter }) {
  const profiles = getProfiles();
  const [name, setName] = React.useState('');
  const [showNew, setShowNew] = React.useState(profiles.length === 0);
  const vi = true; // Gate luôn hiện tiếng Việt (chưa có lang setting)

  const handleCreate = () => {
    if (!name.trim()) return;
    onEnter(name.trim());
  };

  return (
    <div style={{ minHeight:'100vh', background:'var(--bg-0)', display:'flex', alignItems:'center', justifyContent:'center', padding: 32 }}>
      <div style={{ maxWidth: 480, width:'100%' }}>
        {/* Logo */}
        <div style={{ fontFamily:'var(--font-sans)', fontWeight:950, fontSize:28, letterSpacing:'-.04em', textTransform:'uppercase', color:'var(--fg-0)', marginBottom: 8 }}>
          INTERN<span style={{ color:'#38bdf8', textShadow:'2px 2px 0 rgba(255,51,102,.5)' }}>HUB</span>
        </div>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:10, letterSpacing:'.22em', color:'var(--accent-cyan)', textTransform:'uppercase', marginBottom: 40 }}>
          CAREER CONSOLE · v0.1
        </div>

        {profiles.length > 0 && !showNew ? (
          /* Màn hình chọn profile cũ */
          <>
            <div style={{ fontFamily:'var(--font-sans)', fontSize:24, fontWeight:950, color:'var(--fg-0)', textTransform:'uppercase', letterSpacing:'-.03em', marginBottom:6 }}>
              Chào mừng trở lại
            </div>
            <div className="muted" style={{ fontSize:14, marginBottom:24 }}>Chọn profile của bạn:</div>
            <div className="stack" style={{ gap:8, marginBottom:16 }}>
              {profiles.map(p => (
                <div key={p.slug}
                     className="card"
                     style={{ cursor:'pointer', padding:'14px 18px', display:'flex', alignItems:'center', gap:14 }}
                     onClick={() => { switchProfile(p.slug); onEnter(p.name); }}>
                  <div style={{ width:40, height:40, background: roleColor('DA'), display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'var(--font-mono)', fontWeight:950, color:'#09090b', fontSize:14, flexShrink:0 }}>
                    {p.name.slice(0,2).toUpperCase()}
                  </div>
                  <div>
                    <div style={{ fontFamily:'var(--font-sans)', fontWeight:900, color:'var(--fg-0)', textTransform:'uppercase', letterSpacing:'-.01em' }}>{p.name}</div>
                    <div className="mono muted" style={{ fontSize:10, letterSpacing:'.12em' }}>
                      {new Date(p.createdAt).toLocaleDateString('vi-VN')}
                    </div>
                  </div>
                  <div style={{ marginLeft:'auto', color:'var(--accent-cyan)', fontSize:18 }}>→</div>
                </div>
              ))}
            </div>
            <button className="btn ghost compact full" onClick={() => setShowNew(true)}>+ Tạo profile mới</button>
          </>
        ) : (
          /* Màn hình tạo profile mới */
          <>
            <div style={{ fontFamily:'var(--font-sans)', fontSize:24, fontWeight:950, color:'var(--fg-0)', textTransform:'uppercase', letterSpacing:'-.03em', marginBottom:6 }}>
              Bắt đầu hành trình
            </div>
            <div className="muted" style={{ fontSize:14, marginBottom:28 }}>
              Nhập tên để tạo profile. Lịch sử luyện tập sẽ được lưu lại.
            </div>
            <div className="label">Tên của bạn</div>
            <input
              className="input"
              placeholder="Ví dụ: Minh, Lan, ..."
              value={name}
              maxLength={30}
              onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
              autoFocus
              style={{ marginBottom: 16 }}
            />
            <button className="btn primary full"
                    disabled={!name.trim()}
                    style={{ opacity: name.trim() ? 1 : 0.4 }}
                    onClick={handleCreate}>
              Bắt đầu →
            </button>
            {profiles.length > 0 && (
              <button className="btn ghost compact full" style={{ marginTop:10 }} onClick={() => setShowNew(false)}>
                ← Quay lại danh sách
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function LandingScreen({ onNav }) {
  const { state, t, set } = useStore();
  const lang = state.lang;
  // Demo radar — pretend DS role, mid-progress vector
  const demoVec = [7.9, 6.2, 7.4, 2.5, 4.6, 3.1];
  const demoTgt = ROLE_TARGETS.DS;
  const demoAxes = SKILL_AXES.DS;

  const scrollToDemo = () => {
    const el = document.getElementById('demo-section');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <>
      {/* ============ HERO ============ */}
      <div className="landing-hero">
        <div className="inner">
          <div className="kicker">{t('landing.kicker')}</div>
          <h1>{t('landing.titleA')}<br /><span className="hot">{t('landing.titleB')}</span></h1>
          <div className="lede">{t('landing.lede')}</div>
          <div className="ctas">
            <button className="btn primary" onClick={() => onNav('onboarding')}>
              {lang === 'vi' ? 'Bắt đầu miễn phí →' : 'Start free →'}
            </button>
            <button className="btn ghost" onClick={scrollToDemo}>
              {lang === 'vi' ? '↓ Xem demo bên dưới' : '↓ See it in action'}
            </button>
          </div>
          <div style={{ marginTop: 32, display:'inline-flex', gap: 26, fontFamily:'var(--font-mono)', fontSize: 10, letterSpacing:'.18em', textTransform:'uppercase', color:'var(--fg-5)', flexWrap:'wrap', justifyContent:'center' }}>
            <span><span className="cyan">●</span>&nbsp;&nbsp;{lang === 'vi' ? 'Miễn phí cho đồ án' : 'Free for school projects'}</span>
            <span><span className="cyan">●</span>&nbsp;&nbsp;{lang === 'vi' ? 'Không cần đăng ký' : 'No sign-up required'}</span>
            <span><span className="cyan">●</span>&nbsp;&nbsp;{lang === 'vi' ? 'Dữ liệu local' : 'Local-only data'}</span>
            <span><span className="cyan">●</span>&nbsp;&nbsp;{lang === 'vi' ? '3 vai trò · 6 trục kỹ năng' : '3 roles · 6 skill axes'}</span>
          </div>
        </div>
      </div>

      {/* ============ HOW IT WORKS (4 steps) ============ */}
      <div id="demo-section" style={{ maxWidth: 1180, margin: '0 auto', padding: '40px 32px 24px' }}>
        <div style={{ textAlign:'center', marginBottom: 36 }}>
          <div className="mono cyan" style={{ fontSize: 11, letterSpacing:'.32em', textTransform:'uppercase', fontWeight: 800, marginBottom: 10 }}>
            {lang === 'vi' ? 'CƠ CHẾ HOẠT ĐỘNG' : 'HOW IT WORKS'}
          </div>
          <h2 style={{ fontFamily:'var(--font-sans)', fontSize: 'clamp(2rem, 4.5vw, 3.5rem)', fontWeight: 950, letterSpacing:'-.05em', color:'var(--fg-0)', textTransform:'uppercase', margin: 0, lineHeight: 1 }}>
            {lang === 'vi' ? <>4 bước từ <span className="hot">bức rối</span> đến <span style={{ color: '#a3ff12' }}>sẵn sàng</span></> : <>4 steps from <span className="hot">stuck</span> to <span style={{ color: '#a3ff12' }}>interview-ready</span></>}
          </h2>
        </div>
        <div className="split-4" style={{ gap: 16 }}>
          <LandingStep no="01" color="#00e5ff" kicker={lang === 'vi' ? 'CHỌN' : 'PICK'} title={lang === 'vi' ? 'Chọn vai trò' : 'Pick your track'}
            desc={lang === 'vi' ? '3 track: DA, DE, DS. Mỗi track có bộ câu hỏi + vector mục tiêu riêng.' : '3 tracks: DA, DE, DS. Each has its own question bank + target vector.'} />
          <LandingStep no="02" color="#ff7a1a" kicker={lang === 'vi' ? 'TRẢ LỜI' : 'ANSWER'} title={lang === 'vi' ? 'Luyện câu hỏi' : 'Answer questions'}
            desc={lang === 'vi' ? 'Câu hỏi sinh ra theo vai trò, chấm điểm streaming. Có sandbox SQL/Python.' : 'Role-targeted questions, AI streams feedback. SQL & Python sandbox.'} />
          <LandingStep no="03" color="#a3ff12" kicker={lang === 'vi' ? 'DỰNG' : 'BUILD'} title={lang === 'vi' ? 'Dựng radar' : 'Build the radar'}
            desc={lang === 'vi' ? 'AI chấm câu trả lời và build vector 6 chiều. So sánh với JD thực.' : 'AI grades answers, builds a 6-D vector. Compare to real JD requirements.'} />
          <LandingStep no="04" color="#ff3366" kicker={lang === 'vi' ? 'CẢI THIỆN' : 'IMPROVE'} title={lang === 'vi' ? 'Lộ trình cá nhân' : 'Sequenced roadmap'}
            desc={lang === 'vi' ? '5 tuần, xếp theo gap. Retake → lộ trình reflow. Spaced repetition cho weak skills.' : '5 weeks, sequenced by gap. Retake → roadmap reflows. Spaced repetition for weak skills.'} />
        </div>
      </div>

      {/* ============ EMBEDDED LIVE DEMO ============ */}
      <div style={{ maxWidth: 1180, margin: '40px auto 0', padding: '0 32px' }}>
        <div className="card raised" style={{ borderTop: '4px solid #a3ff12', padding: 32 }}>
          <div className="row between" style={{ marginBottom: 20, flexWrap:'wrap', gap: 14 }}>
            <div>
              <div className="mono" style={{ fontSize: 10, color:'#a3ff12', letterSpacing:'.22em', fontWeight: 900, marginBottom: 6 }}>{lang === 'vi' ? 'PREVIEW · DATA SCIENTIST' : 'LIVE PREVIEW · DATA SCIENTIST'}</div>
              <h2 style={{ margin: 0, fontFamily:'var(--font-sans)', fontSize: 24, fontWeight: 950, textTransform:'uppercase', color:'var(--fg-0)', letterSpacing:'-.03em' }}>{lang === 'vi' ? 'Đây là dashboard sau phỏng vấn' : 'This is what your dashboard looks like'}</h2>
              <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>{lang === 'vi' ? 'Hover một trục radar — gap row + lộ trình highlight đồng thời' : 'Hover a radar axis — gap row + roadmap step highlight together'}</div>
            </div>
            <button className="btn primary compact" onClick={() => onNav('onboarding')}>
              {lang === 'vi' ? 'Dựng radar của tôi →' : 'Build my own →'}
            </button>
          </div>
          <div className="split-2" style={{ alignItems:'start' }}>
            <div style={{ background:'var(--bg-2)', border:'1px solid var(--line)', padding: 20 }}>
              <RadarChart axes={demoAxes} current={demoVec} target={demoTgt} color="#a3ff12" size={340} />
            </div>
            <div>
              <h3>{lang === 'vi' ? 'KHOẢNG CÁCH · XẾP HẠNG' : 'GAPS · RANKED'}</h3>
              <GapList
                skills={['ALGORITHM THEORY','EVAL METRICS','DATA PREPROC.','DEEP LEARNING','NLP','MLOPS']}
                current={demoVec} target={demoTgt} roleColor="#a3ff12"
                onPracticeSkill={() => onNav('onboarding')}
              />
            </div>
          </div>
        </div>
      </div>

      {/* ============ 3 FEATURE CARDS ============ */}
      <div className="landing-feat-grid" style={{ marginTop: 60 }}>
        <div className="card raised role-top" style={{ '--role-color':'#00e5ff' }}>
          <h3>01 / ASSESS</h3>
          <div className="mono cyan" style={{ fontSize: 11, marginBottom: 8, letterSpacing:'.18em', textTransform:'uppercase' }}>SKILL VECTOR</div>
          <div style={{ fontFamily:'var(--font-sans)', fontSize: 22, fontWeight: 950, textTransform:'uppercase', letterSpacing:'-.03em', color:'var(--fg-0)', lineHeight:1, marginBottom: 10 }}>{lang === 'vi' ? 'Dựng radar của bạn' : 'Build your radar'}</div>
          <div className="muted" style={{ fontSize: 13, lineHeight: 1.55 }}>
            {lang === 'vi' ? 'Một bộ câu hỏi nhanh dựng vector 6 chiều ban đầu. Mỗi câu trả lời tinh chỉnh nó.' : 'A quick intake builds an initial 6-dimension vector. Every answer refines it.'}
          </div>
        </div>
        <div className="card raised" style={{ '--role-color':'#ff7a1a' }}>
          <h3 style={{ color:'#ff7a1a' }}>02 / PRACTICE</h3>
          <div className="mono" style={{ fontSize: 11, marginBottom: 8, letterSpacing:'.18em', textTransform:'uppercase', color:'#ff7a1a' }}>ROLE-TARGETED</div>
          <div style={{ fontFamily:'var(--font-sans)', fontSize: 22, fontWeight: 950, textTransform:'uppercase', letterSpacing:'-.03em', color:'var(--fg-0)', lineHeight:1, marginBottom: 10 }}>{lang === 'vi' ? 'Câu hỏi thật, chấm live' : 'Real questions, graded live'}</div>
          <div className="muted" style={{ fontSize: 13, lineHeight: 1.55 }}>
            {lang === 'vi' ? 'Câu hỏi sinh ra theo vai trò, chấm điểm streaming. Có sandbox SQL/Python.' : 'Role-targeted questions, streaming AI feedback, SQL/Python sandbox.'}
          </div>
        </div>
        <div className="card raised" style={{ '--role-color':'#a3ff12' }}>
          <h3 style={{ color:'#a3ff12' }}>03 / IMPROVE</h3>
          <div className="mono" style={{ fontSize: 11, marginBottom: 8, letterSpacing:'.18em', textTransform:'uppercase', color:'#a3ff12' }}>SEQUENCED PLAN</div>
          <div style={{ fontFamily:'var(--font-sans)', fontSize: 22, fontWeight: 950, textTransform:'uppercase', letterSpacing:'-.03em', color:'var(--fg-0)', lineHeight:1, marginBottom: 10 }}>{lang === 'vi' ? 'Đóng gap lớn nhất trước' : 'Close the biggest gap first'}</div>
          <div className="muted" style={{ fontSize: 13, lineHeight: 1.55 }}>
            {lang === 'vi' ? 'Lộ trình tuần được sắp xếp theo độ ưu tiên gap. Refresh sau mỗi lần retake.' : 'Weekly roadmap sequenced by gap severity. Reflows after every retake.'}
          </div>
        </div>
      </div>

      {/* ============ FAQ ============ */}
      <div style={{ maxWidth: 1180, margin: '40px auto 0', padding: '0 32px' }}>
        <div style={{ textAlign:'center', marginBottom: 30 }}>
          <div className="mono cyan" style={{ fontSize: 11, letterSpacing:'.32em', textTransform:'uppercase', fontWeight: 800, marginBottom: 10 }}>FAQ</div>
          <h2 style={{ fontFamily:'var(--font-sans)', fontSize: 'clamp(1.8rem, 3.5vw, 2.6rem)', fontWeight: 950, letterSpacing:'-.04em', color:'var(--fg-0)', textTransform:'uppercase', margin: 0, lineHeight: 1 }}>
            {lang === 'vi' ? 'Câu hỏi thường gặp' : 'Common questions'}
          </h2>
        </div>
        <div className="split-2" style={{ gap: 14 }}>
          <FAQItem q={lang === 'vi' ? 'Dữ liệu của tôi lưu ở đâu?' : 'Where is my data stored?'}
                   a={lang === 'vi' ? 'Tất cả lưu trong trình duyệt (localStorage). Không server, không tracking. Export JSON bất kỳ lúc nào trong Settings.' : 'Everything stays in your browser (localStorage). No server, no tracking. Export JSON anytime from Settings.'} />
          <FAQItem q={lang === 'vi' ? 'Câu hỏi từ đâu?' : 'Where do the questions come from?'}
                   a={lang === 'vi' ? 'Bộ câu hỏi gốc từ thực tế phỏng vấn DA/DE/DS. AI sinh thêm câu theo skill gap của bạn.' : 'Seeded from real DA/DE/DS interview banks. AI generates additional questions tuned to your skill gaps.'} />
          <FAQItem q={lang === 'vi' ? 'Tôi có cần đăng ký không?' : 'Do I need to sign up?'}
                   a={lang === 'vi' ? 'Không. Phiên bản này là đồ án, chạy hoàn toàn local. Thông tin đăng nhập sẽ đứng vữới bản production sau.' : 'No. This version is a school project — runs fully local. Auth comes in production later.'} />
          <FAQItem q={lang === 'vi' ? 'Pair Practice hoạt động như thế nào?' : 'How does Pair Practice work?'}
                   a={lang === 'vi' ? 'Mời 1 người bạn. Cả hai ngồi trong cùng phòng ảo, đổi vai sau 4 câu. AI chấm cả hai → cả hai radar update.' : 'Invite a friend. Both sit in a shared room, swap roles every 4 questions. AI grades both → both radars update.'} />
        </div>
      </div>

      {/* ============ FINAL CTA ============ */}
      <div style={{ maxWidth: 980, margin: '60px auto 80px', padding: '40px 32px', textAlign:'center' }}>
        <div className="card raised" style={{ padding: 48, borderTop: '4px solid #fde047' }}>
          <div className="mono warn-c" style={{ fontSize: 11, letterSpacing:'.32em', fontWeight: 900, marginBottom: 10 }}>{lang === 'vi' ? 'SẴN SÀNG?' : 'READY?'}</div>
          <h2 style={{ fontFamily:'var(--font-sans)', fontSize: 'clamp(2rem, 4vw, 3rem)', fontWeight: 950, letterSpacing:'-.05em', color:'var(--fg-0)', textTransform:'uppercase', margin: '0 0 14px', lineHeight: 1 }}>
            {lang === 'vi' ? <>Radar đầu tiên<br />trong <span className="hot">90 giây</span></> : <>Your first radar<br />in <span className="hot">90 seconds</span></>}
          </h2>
          <div className="muted" style={{ fontSize: 15, lineHeight: 1.6, maxWidth: 560, margin: '0 auto 28px' }}>
            {lang === 'vi' ? 'Chọn vai trò → tự đánh giá 6 thanh trượt → có radar ngay. Sau đó luyện câu hỏi để tinh chỉnh.' : 'Pick a role → self-rate 6 sliders → radar ready. Then practice questions to refine it.'}
          </div>
          <button className="btn primary" style={{ fontSize: 14, padding: '14px 28px' }} onClick={() => onNav('onboarding')}>
            {lang === 'vi' ? 'Bắt đầu miễn phí →' : 'Start free →'}
          </button>
        </div>
      </div>
    </>
  );
}

// Compact step card for the "How it works" row
function LandingStep({ no, color, kicker, title, desc }) {
  return (
    <div className="card raised" style={{ borderTop: `4px solid ${color}`, padding: 22, minHeight: 220 }}>
      <div className="row between" style={{ marginBottom: 14 }}>
        <div className="mono" style={{ color, fontSize: 11, fontWeight: 950, letterSpacing: '.2em' }}>{no} / {kicker}</div>
        <div style={{ color, fontSize: 22, fontWeight: 950 }}>→</div>
      </div>
      <div style={{ fontFamily:'var(--font-sans)', fontSize: 18, fontWeight: 950, color:'var(--fg-0)', textTransform:'uppercase', letterSpacing:'-.02em', lineHeight: 1.15, marginBottom: 10 }}>{title}</div>
      <div className="muted" style={{ fontSize: 13, lineHeight: 1.55 }}>{desc}</div>
    </div>
  );
}

// Compact FAQ item
function FAQItem({ q, a }) {
  const [open, setOpen] = React.useState(false);
  return (
    <div className="card" style={{ padding: 18, cursor:'pointer' }} onClick={() => setOpen(o => !o)}>
      <div className="row between" style={{ alignItems:'flex-start', gap: 14 }}>
        <div style={{ fontFamily:'var(--font-sans)', fontSize: 16, fontWeight: 900, color:'var(--fg-0)', textTransform:'uppercase', letterSpacing:'-.01em', lineHeight: 1.3 }}>{q}</div>
        <div className="mono cyan" style={{ fontSize: 18, transform: open ? 'rotate(45deg)' : 'rotate(0)', transition: 'transform .2s ease' }}>+</div>
      </div>
      {open && <div className="muted" style={{ fontSize: 13, lineHeight: 1.6, marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--line-soft)' }}>{a}</div>}
    </div>
  );
}

// ============================================================
// Onboarding — 2 steps: role pick + intake survey
// ============================================================
function OnboardingScreen({ onNav }) {
  const { state, set, t } = useStore();
  const [picked, setPicked] = React.useState(state.role || null);
  const [name, setName] = React.useState(state.user.name === 'You' ? '' : state.user.name);
  const vi = state.lang === 'vi';

  const finish = () => {
    const displayName = name.trim() || 'User';
    set({
      role: picked,
      user: { ...state.user, name: displayName, avatar: displayName.slice(0,2).toUpperCase() },
    });
    onNav('interview', { mode: 'assessment' });
  };

  return (
    <div className="main" style={{ position:'relative' }}>
      <PageHead
        kicker={t('onb.kicker')}
        title={t('onb.title')}
        right={[<button key="b" className="btn ghost" onClick={() => onNav('landing')}>← {t('common.back')}</button>]}
      />

      {/* Nhập tên */}
      <div style={{ marginBottom: 28, maxWidth: 400 }}>
        <div className="label">{vi ? 'Tên của bạn' : 'Your name'}</div>
        <input className="input" placeholder={vi ? 'Ví dụ: Minh, Lan, ...' : 'e.g. Alex, Sam...'}
               value={name} maxLength={30}
               onChange={e => setName(e.target.value)} />
      </div>

      <div className="muted" style={{ marginBottom: 16, fontSize: 14 }}>{t('onb.sub')}</div>
      <RolePickerMini value={picked} onPick={setPicked} />

      <div className="card" style={{ marginTop: 22, padding:'14px 18px', background:'rgba(0,229,255,.04)', borderColor:'var(--accent-cyan)' }}>
        <div className="mono cyan" style={{ fontSize:10, letterSpacing:'.22em', fontWeight:900, marginBottom:4 }}>
          {vi ? 'TIẾP THEO' : 'NEXT STEP'}
        </div>
        <div style={{ fontSize:13, color:'var(--fg-2)' }}>
          {vi ? 'Bạn sẽ làm 1 câu hỏi đánh giá ban đầu → radar năng lực đầu tiên được tạo.'
              : 'You will answer 1 assessment question → your first competency radar is created.'}
        </div>
      </div>

      <div style={{ marginTop: 24, display:'flex', justifyContent:'flex-end' }}>
        <button className="btn primary"
                disabled={!picked}
                style={{ opacity: picked ? 1 : 0.4 }}
                onClick={() => picked && finish()}>
          {vi ? 'Bắt đầu đánh giá →' : 'Start assessment →'}
        </button>
      </div>
    </div>
  );
}

// ============================================================
// Public Profile (shareable radar)
// ============================================================
function ProfileScreen({ onNav }) {
  const { state, t } = useStore();
  const vi = state.lang === 'vi';
  if (!state.role) return <EmptyState onNav={onNav} message="No role selected" />;
  const vec = currentVector(state);
  if (!vec) return (
    <div style={{ padding: '60px 32px', textAlign:'center' }}>
      <div className="mono" style={{ fontSize:10, color:'var(--fg-5)', letterSpacing:'.22em', textTransform:'uppercase', marginBottom:14 }}>
        {vi ? 'HỒ SƠ · CHƯA CÓ DỮ LIỆU' : 'PROFILE · NO DATA YET'}
      </div>
      <div style={{ fontFamily:'var(--font-sans)', fontSize:28, fontWeight:950, textTransform:'uppercase', letterSpacing:'-.04em', color:'var(--fg-0)', marginBottom:12 }}>
        {vi ? 'Hồ sơ chưa được tạo' : 'Profile not built yet'}
      </div>
      <div className="muted" style={{ fontSize:14, marginBottom:28, maxWidth:480, margin:'0 auto 28px' }}>
        {vi ? 'Hoàn thành ít nhất một phiên phỏng vấn để radar của bạn được tạo và có thể chia sẻ.' : 'Complete at least one interview session to build your radar and enable sharing.'}
      </div>
      <button className="btn primary" onClick={() => onNav('interview', { mode: 'quick' })}>
        {vi ? 'Bắt đầu đánh giá →' : 'Start assessment →'}
      </button>
    </div>
  );
  return (
    <>
      <PageHead
        kicker={t('profile.kicker')}
        title={t('profile.title')}
        right={[
          <button key="c" className="btn compact">📋 {t('common.copyLink') || 'Copy link'}</button>,
          <button key="d" className="btn compact">↓ {t('common.download')}</button>,
        ]}
      />
      <div className="alert">
        <span className="dot"></span>
        <div>{t('profile.hint')}</div>
      </div>
      <div className="split-2" style={{ marginTop: 22, alignItems:'start' }}>
        <div className="card raised role-top" style={{ '--role-color': roleColor(state.role) }}>
          <div className="row" style={{ gap: 16 }}>
            <div style={{ width: 64, height: 64, background: roleColor(state.role), display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'var(--font-mono)', fontSize: 24, fontWeight: 950, color:'#09090b' }}>
              {state.user.avatar}
            </div>
            <div>
              <div className="mono" style={{ fontSize: 11, color: roleColor(state.role), letterSpacing:'.16em', fontWeight: 900 }}>{state.role} · {state.role === 'DA' ? 'Data Analyst' : state.role === 'DE' ? 'Data Engineer' : 'Data Scientist'}</div>
              <div style={{ fontFamily:'var(--font-sans)', fontSize: 28, fontWeight: 950, textTransform:'uppercase', letterSpacing:'-.04em', color:'var(--fg-0)', lineHeight: 1, marginTop: 4 }}>{state.user.name}</div>
              <div className="mono muted" style={{ fontSize: 11, marginTop: 8, letterSpacing:'.12em' }}>STREAK {state.user.streak}d · {state.attempts.length} assessments</div>
            </div>
          </div>
          <div style={{ marginTop: 28 }}>
            <RadarChart axes={SKILL_AXES[state.role]} current={vec} target={ROLE_TARGETS[state.role]} color={roleColor(state.role)} size={340} />
          </div>
        </div>
        <div className="stack">
          <div className="card warn-top">
            <h3 style={{ color:'var(--accent-warn)' }}>SHARE LINK</h3>
            <div className="mono" style={{ fontSize: 12, color:'var(--fg-0)', background:'rgba(0,0,0,.6)', padding:'10px 12px', border:'1px solid var(--line)', letterSpacing:'.04em', marginBottom: 12, wordBreak:'break-all' }}>
              https://internhub.career/share/{state.user.avatar.toLowerCase()}-{state.role.toLowerCase()}-2026
            </div>
            <div className="row wrap" style={{ gap: 8 }}>
              <span className="chip good">PUBLIC</span>
              <span className="chip">READ-ONLY</span>
              <span className="chip warn">EXPIRES IN 90 DAYS</span>
            </div>
          </div>
          <div className="card">
            <h3>VISIBLE ON SHARE</h3>
            <div className="stack" style={{ gap: 6 }}>
              <div className="row" style={{ fontSize: 13, color:'var(--fg-2)' }}><span className="cyan">✓</span>&nbsp;Current radar & vector scores</div>
              <div className="row" style={{ fontSize: 13, color:'var(--fg-2)' }}><span className="cyan">✓</span>&nbsp;Streak + total assessments</div>
              <div className="row" style={{ fontSize: 13, color:'var(--fg-2)' }}><span className="cyan">✓</span>&nbsp;Active role</div>
              <div className="row" style={{ fontSize: 13, color:'var(--fg-5)', marginTop: 10 }}><span className="hot">✗</span>&nbsp;Answers, notes, roadmap</div>
              <div className="row" style={{ fontSize: 13, color:'var(--fg-5)' }}><span className="hot">✗</span>&nbsp;History timeline</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function EmptyState({ message, onNav }) {
  const { t } = useStore();
  return (
    <div className="card raised" style={{ textAlign:'center', padding: 60 }}>
      <div className="mono" style={{ color:'var(--fg-5)', letterSpacing:'.22em', textTransform:'uppercase', fontSize: 11, marginBottom: 14 }}>{message}</div>
      <div style={{ fontFamily:'var(--font-sans)', fontSize: 24, textTransform:'uppercase', color:'var(--fg-0)', fontWeight: 950, letterSpacing:'-.02em', marginBottom: 22 }}>{t('common.empty')}</div>
      <button className="btn primary" onClick={() => onNav('onboarding')}>{t('landing.cta1') || 'Get started'}</button>
    </div>
  );
}

Object.assign(window, { UserGateScreen, LandingScreen, OnboardingScreen, ProfileScreen, EmptyState });
