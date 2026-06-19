// ============================================================
// state.jsx — global store + i18n + mock data + localStorage
// ============================================================

const STORAGE_KEY = 'internhub.v1';

// --------------- DEFAULT STATE (seed) -------------------------
const DEFAULTS = {
  lang: 'en',                      // 'en' | 'vi'
  role: null,                      // 'DA' | 'DE' | 'DS' | null
  userId: null,                    // set after create_user_profile API call
  user: { name: 'You', avatar: 'YO', streak: 7 },
  // attempts: list of { date, role, vector } — populated after onboarding
  attempts: [],
  bookmarks: [],
  completedQs: [],
  notes: [],
  prefs: {
    streamingFeedback: true,
    spacedRepetition: true,
    notifications: false,
    sandboxAutorun: false,
    soundEffects: false,
  },
  customMode: { duration: 30, questionCount: 3, difficulty: 'mixed', skills: ['ALL'] },
  mst: {
    active: false,
    stage: 1,
    s1Ids: [],
    s1Results: [],
    s2Ids: [],
    s2Results: [],
    routing: null,
    done: false,
    startedAt: null,
  },
};

// --------------- I18N DICTIONARY ------------------------------
const I18N = {
  en: {
    appName: 'INTERNHUB',
    appTag: 'CAREER CONSOLE',
    nav: { practice:'PRACTICE', progress:'PROGRESS', community:'COMMUNITY', system:'SYSTEM' },
    nav_items: { home:'Today', interview:'Interview', questions:'Library', dashboard:'Dashboard', roadmap:'KT Model', history:'History', settings:'Settings', profile:'Profile' },
    common: { start:'Start', submit:'Submit', cancel:'Cancel', save:'Save', skip:'Skip', back:'Back', next:'Next', viewAll:'View all', signIn:'Sign in', getStarted:'Get started', tryNow:'Try now', continue:'Continue', upload:'Upload', run:'Run', reset:'Reset', share:'Share', download:'Download', export:'Export', loading:'Loading', empty:'Nothing here yet', copyLink:'Copy link' },
    lang: { en:'EN', vi:'VI' },
    landing: {
      kicker: 'CAREER CONSOLE · LEVEL UP YOUR CAREER',
      titleA: 'AI TECH',
      titleB: 'INTERVIEW PREP',
      lede: 'Assess your competency, practice role-targeted interview questions, and get a sequenced roadmap of skills to improve next.',
      cta1: 'Start free →',
      cta2: 'See how it works',
      featTitle: 'How the cockpit works',
    },
    onb: {
      kicker: 'STEP 01 · CHOOSE TARGET ROLE',
      title: 'Pick your track',
      sub: 'Each role anchors the question bank, target competency vector, and learning roadmap. You can change later in Settings.',
      next: 'Continue to intake →',
      intakeKicker: 'STEP 02 · INTAKE',
      intakeTitle: 'Self-rate your current skills',
      intakeSub: 'Quick sliders so the first radar isn`t empty. The AI uses these as a baseline and refines them after your first interview.',
      finish: 'Build my radar →',
    },
    home: {
      kicker: 'TODAY · YOUR COCKPIT',
      title: 'Welcome back',
      quickDrill: 'Quick drill', focused: 'Focused practice', mock: 'Mock interview', custom: 'Custom session',
      qdDesc: '5 min · 1 question. Daily warmup.',
      fpDesc: '15 min · 3 questions on one skill.',
      mkDesc: '20 min · 10 questions (7 placement + 3 adaptive), covers all skill areas.',
      ctDesc: 'You set the parameters.',
      next: 'Recommended next',
    },
    interview: {
      kicker: 'INTERVIEW SESSION',
      title: 'Interview Workspace',
      submit: 'Submit answer →',
      skip: 'Skip',
      end: 'End session',
      placeholder: '// type your answer here. plain prose or code. shift+enter for newline.',
      sandboxRun: 'Run',
      sandboxOut: 'Sandbox output',
      streaming: 'AI feedback streaming',
      whyKicker: 'WHY THIS QUESTION',
      why: 'You scored 2.5/10 on DL_FUNDAMENTALS last week. This question probes the same skill at intermediate depth.',
    },
    lib: {
      kicker: 'QUESTION LIBRARY',
      title: 'Browse questions',
      filterRole: 'Role', filterDiff: 'Difficulty', filterStatus: 'Status', filterSkill: 'Skill', searchPh: 'search questions, tags, ids…',
    },
    dash: {
      kicker: 'COMPETENCY DASHBOARD',
      title: 'Skill Gap Analysis',
      vector: 'Competency Vector',
      gaps: 'Top Gaps · Ranked',
      legendCur: 'CURRENT', legendTgt: 'TARGET',
      metricOverall: 'OVERALL', metricLocked: 'LOCKED', metricBelow: 'BELOW TARGET', metricCritical: 'CRITICAL',
      vsTarget: 'VS TARGET',
      practiceSkill: 'Practice this skill →',
    },
    roadmap: {
      kicker: 'LEARNING ROADMAP',
      title: 'Skill Recovery Plan',
      pin: 'Pin to calendar',
      nextMs: 'Next milestone',
    },
    history: {
      kicker: 'HISTORY · DELTA OVER TIME',
      title: 'Your trajectory',
      sub: 'Each dot is an assessment. Overlay shows how your radar has shifted week-over-week.',
      delta: 'Δ',
    },
    pair: {
      kicker: 'PAIR PRACTICE',
      title: 'Mock with a friend',
      invite: 'Invite a partner',
      copyLink: 'Copy invite link',
      activeRoom: 'ACTIVE ROOM',
      asker: 'Asker', answerer: 'Answerer',
    },
    notes: { kicker:'NOTES · LINKED TO QUESTIONS', title:'Your notebook' },
    settings: {
      kicker:'SYSTEM SETTINGS', title:'Settings',
      sysGeneral: 'General', sysLang: 'Language', sysLangSub: 'Surface labels, buttons, headings. Question content always stays bilingual.',
      sysRole: 'Active track', sysRoleSub: 'You can also hold multiple tracks at once. Vectors track separately.',
      sysAI: 'AI features', sysAISub: 'Toggle what the LLM does for you.',
      sysAccount: 'Resume & JD', sysAccountSub: 'Upload your resume to auto-detect skills; upload a JD to personalize the target vector.',
      sysSandbox: 'Code sandbox', sysSandboxSub: 'Choose whether SQL/Python runs against sample data automatically when you press Run.',
      sysAutorun: 'Auto-run on Submit',
      sysStreaming: 'Streaming LLM feedback', sysSpaced: 'Spaced repetition', sysWhy: 'Explain "why this question"', sysNotif: 'Email notifications',
      uploadResume: 'Upload resume',
      uploadJD: 'Upload job description',
      resumeHint: 'PDF, DOCX, TXT · max 5 MB · processed locally',
      jdHint: 'Paste URL or upload doc. We extract required skills.',
    },
    profile: { kicker:'PUBLIC PROFILE', title:'Shareable radar', hint:'Anyone with this link can view your current vector. They cannot see your answers, notes, or roadmap.' },
  },
  vi: {
    appName: 'INTERNHUB',
    appTag: 'CAREER CONSOLE',
    nav: { practice:'LUYỆN TẬP', progress:'TIẾN ĐỘ', community:'CỘNG ĐỒNG', system:'HỆ THỐNG' },
    nav_items: { home:'Hôm nay', interview:'Phỏng vấn', questions:'Thư viện', dashboard:'Dashboard', roadmap:'KT Model', history:'Lịch sử', settings:'Cài đặt', profile:'Hồ sơ' },
    common: { start:'Bắt đầu', submit:'Gửi', cancel:'Hủy', save:'Lưu', skip:'Bỏ qua', back:'Quay lại', next:'Tiếp', viewAll:'Xem tất cả', signIn:'Đăng nhập', getStarted:'Bắt đầu', tryNow:'Thử ngay', continue:'Tiếp tục', upload:'Tải lên', run:'Chạy', reset:'Đặt lại', share:'Chia sẻ', download:'Tải về', export:'Xuất', loading:'Đang tải', empty:'Chưa có gì ở đây', copyLink:'Copy link' },
    lang: { en:'EN', vi:'VI' },
    landing: {
      kicker: 'CAREER CONSOLE · NÂNG TẦM SỰ NGHIỆP',
      titleA: 'LUYỆN PHỎNG VẤN',
      titleB: 'AI TECH',
      lede: 'Đánh giá năng lực, luyện câu hỏi phỏng vấn theo từng vai trò, và nhận lộ trình kỹ năng cần cải thiện tiếp theo.',
      cta1: 'Bắt đầu miễn phí →',
      cta2: 'Xem cách hoạt động',
      featTitle: 'Cơ chế hoạt động',
    },
    onb: {
      kicker: 'BƯỚC 01 · CHỌN VAI TRÒ',
      title: 'Chọn track của bạn',
      sub: 'Mỗi vai trò gắn với bộ câu hỏi, vector năng lực mục tiêu, và lộ trình học riêng. Có thể đổi sau ở Cài đặt.',
      next: 'Tiếp tục → đánh giá nhanh',
      intakeKicker: 'BƯỚC 02 · ĐÁNH GIÁ NHANH',
      intakeTitle: 'Tự đánh giá kỹ năng hiện tại',
      intakeSub: 'Vài thanh trượt để radar đầu tiên không bị trống. AI dùng đây làm baseline và tinh chỉnh sau phỏng vấn đầu tiên.',
      finish: 'Tạo radar →',
    },
    home: {
      kicker: 'HÔM NAY · COCKPIT CỦA BẠN',
      title: 'Chào mừng trở lại',
      quickDrill: 'Drill nhanh', focused: 'Luyện trọng tâm', mock: 'Phỏng vấn thử', custom: 'Phiên tự chọn',
      qdDesc: '5 phút · 1 câu hỏi. Warmup hàng ngày.',
      fpDesc: '15 phút · 3 câu trên cùng 1 kỹ năng.',
      mkDesc: '45 phút · 4 câu, có giờ, không skip.',
      ctDesc: 'Bạn tự đặt tham số.',
      next: 'Đề xuất tiếp theo',
    },
    interview: {
      kicker: 'PHIÊN PHỎNG VẤN',
      title: 'Khu làm việc',
      submit: 'Gửi câu trả lời →',
      skip: 'Bỏ qua',
      end: 'Kết thúc',
      placeholder: '// gõ câu trả lời. văn bản hoặc code đều được. shift+enter để xuống dòng.',
      sandboxRun: 'Chạy',
      sandboxOut: 'Output sandbox',
      streaming: 'AI đang phản hồi',
      whyKicker: 'TẠI SAO CÂU NÀY',
      why: 'Tuần trước bạn được 2.5/10 ở DL_FUNDAMENTALS. Câu này dò cùng kỹ năng đó ở mức trung cấp.',
    },
    lib: { kicker:'THƯ VIỆN CÂU HỎI', title:'Duyệt câu hỏi', filterRole:'Vai trò', filterDiff:'Độ khó', filterStatus:'Trạng thái', filterSkill:'Kỹ năng', searchPh:'tìm câu hỏi, tag, id…' },
    dash: {
      kicker: 'DASHBOARD NĂNG LỰC',
      title: 'Phân tích Khoảng cách',
      vector: 'Vector Năng lực',
      gaps: 'Khoảng cách · xếp hạng',
      legendCur: 'HIỆN TẠI', legendTgt: 'MỤC TIÊU',
      metricOverall: 'TỔNG QUAN', metricLocked: 'ĐẠT MỤC TIÊU', metricBelow: 'DƯỚI MỤC TIÊU', metricCritical: 'NGHIÊM TRỌNG',
      vsTarget: 'SO VỚI MỤC TIÊU',
      practiceSkill: 'Luyện kỹ năng này →',
    },
    roadmap: { kicker:'LỘ TRÌNH HỌC', title:'Kế hoạch khôi phục kỹ năng', pin:'Gắn vào lịch', nextMs:'Mốc tiếp theo' },
    history: { kicker:'LỊCH SỬ · ĐỘ THAY ĐỔI', title:'Quỹ đạo của bạn', sub:'Mỗi chấm là một lần đánh giá. Overlay cho thấy radar dịch chuyển theo tuần.', delta:'Δ' },
    pair: { kicker:'LUYỆN CẶP', title:'Phỏng vấn với bạn bè', invite:'Mời partner', copyLink:'Copy link mời', activeRoom:'PHÒNG ĐANG ACTIVE', asker:'Người hỏi', answerer:'Người trả lời' },
    notes: { kicker:'GHI CHÚ · LIÊN KẾT CÂU HỎI', title:'Sổ tay của bạn' },
    settings: {
      kicker:'CÀI ĐẶT HỆ THỐNG', title:'Cài đặt',
      sysGeneral:'Chung', sysLang:'Ngôn ngữ', sysLangSub:'Label, nút bấm, tiêu đề. Nội dung câu hỏi luôn song ngữ.',
      sysRole:'Track đang active', sysRoleSub:'Có thể giữ nhiều track cùng lúc. Vector được track riêng.',
      sysAI:'Tính năng AI', sysAISub:'Toggle các thứ LLM làm cho bạn.',
      sysAccount:'CV & JD', sysAccountSub:'Tải CV để auto-detect skill; tải JD để cá nhân hoá vector mục tiêu.',
      sysSandbox:'Code sandbox', sysSandboxSub:'Bật/tắt tự chạy SQL/Python với dữ liệu mẫu khi Submit.',
      sysAutorun:'Tự chạy khi Submit',
      sysStreaming:'Streaming LLM feedback', sysSpaced:'Spaced repetition', sysWhy:'Giải thích "tại sao câu này"', sysNotif:'Thông báo email',
      uploadResume:'Tải CV',
      uploadJD:'Tải JD',
      resumeHint:'PDF, DOCX, TXT · tối đa 5 MB · xử lý local',
      jdHint:'Paste URL hoặc upload doc. Hệ thống tự trích skill yêu cầu.',
    },
    profile: { kicker:'HỒ SƠ CÔNG KHAI', title:'Radar chia sẻ', hint:'Ai có link đều xem được vector hiện tại. Họ KHÔNG thấy câu trả lời, ghi chú hay lộ trình của bạn.' },
  },
};

// ---------------- MOCK QUESTION BANK ---------------------------
const QUESTIONS = [
  // DA
  { id:'Q_DA_017', role:'DA', tags:['SQL_FUNDAMENTALS','SQL_WINDOW_FUNCTION'], difficulty:'INTERMEDIATE', estMin:8,
    title_en:'Find the second-highest salary in an employees table', title_vi:'Tìm mức lương cao thứ hai trong bảng employees',
    body_en:'Write a SQL query to return the second-highest salary. Walk through your approach and discuss edge cases (ties, NULLs, single row).',
    body_vi:'Viết SQL trả về mức lương cao thứ hai. Giải thích cách tiếp cận và edge case (lương trùng, NULL, 1 row).',
    expert_en:'Use DENSE_RANK over salary DESC; filter rank=2. Discuss why ROW_NUMBER fails on ties and why LIMIT/OFFSET breaks on NULLs.',
    starterCode:'SELECT salary\nFROM (\n  SELECT salary,\n         DENSE_RANK() OVER (ORDER BY salary DESC) AS rk\n  FROM employees\n) t\nWHERE rk = 2;' },
  { id:'Q_DA_001', role:'DA', tags:['STAT_AB_TESTING'], difficulty:'BEGINNER', estMin:5, title_en:'Explain a p-value to a PM', title_vi:'Giải thích p-value cho PM', body_en:'A product manager asks: "What does a p-value of 0.03 mean for our checkout A/B test?" Answer in plain English.', body_vi:'PM hỏi: "p-value 0.03 trong test A/B checkout nghĩa là gì?" Trả lời bằng ngôn ngữ đời thường.', expert_en:'It is the probability of seeing data this extreme if there were truly no difference. 0.03 means we`d see this result by chance 3% of the time. Below 0.05 we usually say "real effect".' },
  { id:'Q_DA_012', role:'DA', tags:['ANALYTICS_FUNNEL','ANALYTICS_COHORT'], difficulty:'INTERMEDIATE', estMin:10, title_en:'Design a checkout funnel report', title_vi:'Thiết kế báo cáo funnel checkout', body_en:'You need to ship a weekly funnel report for the checkout flow (cart → review → pay → confirm). What columns, breakdowns, and visuals would you include?', body_vi:'Cần ra weekly funnel cho luồng checkout (cart → review → pay → confirm). Cột, breakdown, biểu đồ gì?', expert_en:'Step conversion %, drop-off absolute, cohort by acquisition channel, by device, trend line week-over-week, plus a top-5 friction reasons table.' },
  // DE
  { id:'Q_DE_042', role:'DE', tags:['PIPE_ETL','PIPE_ORCHESTRATION','TOOL_AIRFLOW','CLOUD_S3'], difficulty:'ADVANCED', estMin:15, title_en:'Daily 200GB clickstream pipeline', title_vi:'Pipeline clickstream 200GB/ngày', body_en:'You are designing a daily batch pipeline that ingests 200GB of clickstream data from S3 into a Snowflake warehouse. Describe orchestration, partitioning, and retry strategy.', body_vi:'Thiết kế batch pipeline daily nạp 200GB clickstream từ S3 vào Snowflake. Mô tả orchestration, partition, retry.', expert_en:'Partition by date in S3; Airflow DAG with sensor on file landing; staged COPY INTO with VARIANT; clustered table on event_date+user_id; retry with exponential backoff capped at 5; alert on SLA miss at 06:00.' },
  { id:'Q_DE_021', role:'DE', tags:['MODELING_STAR_SCHEMA','DATA_WAREHOUSE'], difficulty:'INTERMEDIATE', estMin:10, title_en:'Star schema for an e-commerce DW', title_vi:'Star schema cho DW e-commerce' },
  // DS
  { id:'Q_DS_088', role:'DS', tags:['METRIC_F1_SCORE','METRIC_ROC_AUC','IMBALANCED_DATA_HANDLING'], difficulty:'INTERMEDIATE', estMin:8, title_en:'95% accuracy on imbalanced data — why is it misleading?', title_vi:'95% accuracy trên data lệch — sao lại misleading?', body_en:'A binary classifier scores 95% accuracy on a 1%-positive dataset. Explain why accuracy lies and which metrics you would use instead.', body_vi:'Classifier nhị phân đạt 95% accuracy trên dataset 1% positive. Giải thích tại sao accuracy lừa và nên dùng metric nào.', expert_en:'A constant "negative" predictor achieves 99%. Use F1, ROC-AUC, PR-AUC. PR-AUC is most informative when positives are rare. Also report confusion matrix and threshold sweep.' },
  { id:'Q_DS_004', role:'DS', tags:['DL_FUNDAMENTALS','DL_OPTIMIZATION'], difficulty:'INTERMEDIATE', estMin:10, title_en:'Vanishing vs exploding gradients', title_vi:'Vanishing vs exploding gradient' },
  { id:'Q_DS_102', role:'DS', tags:['ML_MODEL_SELECTION','EVAL_CROSS_VALIDATION'], difficulty:'BEGINNER', estMin:6, title_en:'When to use k-fold vs stratified k-fold', title_vi:'Khi nào dùng k-fold vs stratified k-fold' },
];

const SKILL_AXES = {
  DA: ['SQL','BI','STATS','ANALYTICS','PYTHON','STORY'],
  DE: ['PIPELINE','ARCH','BIG DATA','DB INT.','SYS DESIGN','OPS'],
  DS: ['ALGORITHM','METRICS','PREPROC.','DEEP LEARN','NLP','MLOPS'],
};
const SKILL_KEYS = {
  DA: ['SQL_DATABASE','BI_VISUALIZATION','STATISTICS_EXPERIMENTATION','ANALYTICS_BUSINESS','PYTHON_ANALYTICS'],
  DE: ['DATA_PIPELINE','DATA_ARCHITECTURE_MODELING','BIG_DATA_CLOUD_TOOLS','DATABASE_INTERNALS','SYSTEM_ARCHITECTURE'],
  DS: ['ALGORITHM_THEORY','EVALUATION_METRICS','DATA_PREPROCESSING','DEEP_LEARNING','NLP','TIME_SERIES','MLOPS'],
};
const ROLE_TARGETS = {
  DA: [9, 8, 7, 7, 6, 7],
  DE: [9, 8, 8, 7, 7, 7],
  DS: [9, 9, 8, 7, 7, 6],
};

// ---------------------------------------------------------------
// Override với data thật từ Python project (injected bởi app.py)
// ---------------------------------------------------------------
(function() {
  const d = window.__INTERNHUB_DATA__;
  if (!d) return;

  // Câu hỏi thật (60 câu thay vì 6 mock)
  if (d.questions && d.questions.length > 0) {
    QUESTIONS.length = 0;
    QUESTIONS.push(...d.questions);
  }

  // Skill axes thật theo từng role
  if (d.skillAxes) {
    Object.assign(SKILL_AXES, d.skillAxes);
  }

  // Skill keys (machine-readable) từ roleRadars
  if (d.roleRadars) {
    Object.keys(d.roleRadars).forEach(role => {
      const keys = d.roleRadars[role] && d.roleRadars[role].skill_keys;
      if (keys && keys.length) SKILL_KEYS[role] = keys;
    });
  }

  // Target vectors thật (từ JD requirements, scale 0-10)
  if (d.roleTargets) {
    Object.assign(ROLE_TARGETS, d.roleTargets);
  }
})();

const AVATAR_COLORS = ['#00e5ff','#ff7a1a','#a3ff12','#ff3366','#fde047','#67e8f9','#f9a8d4','#a78bfa'];

// --------------- CONTEXT --------------------------------------
const StoreContext = React.createContext(null);

const MST_KEY = 'internhub.mst.v1';

function saveMst(mst) {
  try { localStorage.setItem(MST_KEY, JSON.stringify(mst)); } catch(e) {}
}
function loadMst() {
  try { const r = localStorage.getItem(MST_KEY); return r ? JSON.parse(r) : null; } catch(e) { return null; }
}

function loadInitial() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    const base = raw ? { ...DEFAULTS, ...JSON.parse(raw) } : { ...DEFAULTS };
    // Restore mst from localStorage if session lost it
    if (!base.mst?.done) {
      const savedMst = loadMst();
      if (savedMst?.done) base.mst = savedMst;
    }
    return base;
  } catch (e) {}
  return DEFAULTS;
}

function StoreProvider({ children }) {
  const [state, setState] = React.useState(loadInitial);
  const [hl, setHl] = React.useState({ skillIdx: null, roadmapStep: null });

  React.useEffect(() => {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) {}
    if (state.mst?.done) saveMst(state.mst);
  }, [state]);

  const set = React.useCallback((patch) => {
    setState(s => typeof patch === 'function' ? patch(s) : ({ ...s, ...patch }));
  }, []);

  const t = React.useCallback((path) => {
    const dict = I18N[state.lang] || I18N.en;
    return path.split('.').reduce((acc, k) => (acc && acc[k] != null ? acc[k] : path), dict);
  }, [state.lang]);

  const value = { state, set, t, hl, setHl };
  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

function useStore() { return React.useContext(StoreContext); }

// helpers
function roleColor(r) { return { DA:'#00e5ff', DE:'#ff7a1a', DS:'#a3ff12' }[r] || '#00e5ff'; }
function avatarColor(name) { const h = [...(name||'')].reduce((a,c) => a + c.charCodeAt(0), 0); return AVATAR_COLORS[h % AVATAR_COLORS.length]; }

// ── API bridge ─────────────────────────────────────────────────
const API_BASE = 'http://localhost:8000/api';

async function callAPI(endpoint, payload = null, method = null) {
  try {
    const opts = {
      method: method || (payload ? 'POST' : 'GET'),
      headers: { 'Content-Type': 'application/json' },
    };
    if (payload) opts.body = JSON.stringify(payload);
    const res = await fetch(`${API_BASE}${endpoint}`, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    return await res.json();
  } catch (e) {
    console.warn('[callAPI] error:', endpoint, e.message);
    throw e;
  }
}

function currentVector(state) {
  if (!state.role) return null;
  const last = [...state.attempts].reverse().find(a => a.role === state.role);
  return last ? last.vector : null;
}


// ── MST helpers ────────────────────────────────────────────────

function calcDelta(score, difficultyScore) {
  const map = {
    1:[0.1,0.3],2:[0.15,0.4],3:[0.2,0.5],4:[0.25,0.6],5:[0.3,0.7],
    6:[0.35,0.8],7:[0.4,0.9],8:[0.5,1.0],9:[0.6,1.2],10:[0.7,1.5]
  };
  const [minD, maxD] = map[difficultyScore] || [0.1, 0.3];
  if (score >= 0.8) return minD + (maxD - minD) * (score - 0.8) / 0.2;
  if (score < 0.4)  return -(minD + (0.4 - score) / 0.4 * minD);
  return (score - 0.5) * minD;
}

function scoreAnswer(question, { answer, selectedOption, boolAnswer, blankAnswers, code }) {
  const qt = question.questionType;
  if (qt === 'MC_SINGLE') {
    const correct = selectedOption === question.correctOptionId;
    return { score: correct ? 1.0 : 0.0, isCorrect: correct };
  }
  if (qt === 'TRUE_FALSE') {
    const correct = boolAnswer === question.correctAnswer;
    return { score: correct ? 1.0 : 0.0, isCorrect: correct };
  }
  if (qt === 'FILL_BLANK') {
    const acc = question.acceptedAnswers || [];
    if (!acc.length) return { score: 0.5, isCorrect: null };
    const matched = blankAnswers.filter((b, i) =>
      acc[i] && acc[i].some(a => b.trim().toLowerCase() === a.trim().toLowerCase())
    ).length;
    const score = matched / acc.length;
    return { score, isCorrect: score >= 0.6 };
  }
  // THEORY / CODING / PRACTICE / CODING_EXERCISE:
  // screens-practice.jsx calls /api/grade async; screens-diagnostic uses this sync fallback.
  return { score: 0.5, isCorrect: null };
}

function mstAvgScore(results) {
  if (!results || !results.length) return 0;
  return results.reduce((s, r) => s + r.score, 0) / results.length;
}

function mstRouting(avgScore) {
  if (avgScore > 0.7)  return 'STRONG';
  if (avgScore >= 0.4) return 'MID';
  return 'WEAK';
}

function pickStage1(role) {
  // Phase 1: 7 câu, phủ đều KC theo role
  // DA/DE: 5 KC → 5 câu vòng 1 + 2 câu lặp từ top-2 KC (câu khác)
  // DS:    7 KC → đúng 1 câu per KC
  // Strict type slots: ít nhất 1 OBJECTIVE + 1 THEORY + 1 PRACTICE + 1 CODING trong 7 câu
  const S1 = 7;
  const kcs = (SKILL_KEYS[role] || []);
  const usedIds = new Set();
  const picked = [];

  const OBJECTIVE = ['MC_SINGLE', 'TRUE_FALSE', 'FILL_BLANK'];
  const strictFilled = { OBJECTIVE: false, THEORY: false, PRACTICE: false, CODING: false };
  const needStrict = (q) => {
    if (OBJECTIVE.includes(q.questionType) && !strictFilled.OBJECTIVE) return 10;
    if (q.questionType === 'THEORY'   && !strictFilled.THEORY)   return 10;
    if (q.questionType === 'PRACTICE' && !strictFilled.PRACTICE) return 10;
    if ((q.questionType === 'CODING' || q.questionType === 'CODING_EXERCISE') && !strictFilled.CODING) return 10;
    return 0;
  };
  const markStrict = (q) => {
    if (OBJECTIVE.includes(q.questionType)) strictFilled.OBJECTIVE = true;
    if (q.questionType === 'THEORY')   strictFilled.THEORY   = true;
    if (q.questionType === 'PRACTICE') strictFilled.PRACTICE = true;
    if (q.questionType === 'CODING' || q.questionType === 'CODING_EXERCISE') strictFilled.CODING = true;
  };

  const pickFromKC = (kc) => {
    const pool = QUESTIONS
      .filter(q => q.role === role && q.skillGroups && q.skillGroups.includes(kc) && !usedIds.has(q.id))
      .sort(() => Math.random() - 0.5);
    if (!pool.length) return null;
    const scored = pool.map(q => ({ q, s: needStrict(q) })).sort((a, b) => b.s - a.s);
    return scored[0].q;
  };

  // Vòng 1: 1 câu per KC
  for (const kc of kcs) {
    if (picked.length >= S1) break;
    const q = pickFromKC(kc);
    if (q) { picked.push(q); usedIds.add(q.id); markStrict(q); }
  }

  // Vòng 2: DA/DE cần thêm 2 câu → lặp top-2 KC (câu khác)
  if (picked.length < S1) {
    const extraKCs = kcs.slice(0, 2);
    for (const kc of extraKCs) {
      if (picked.length >= S1) break;
      const q = pickFromKC(kc);
      if (q) { picked.push(q); usedIds.add(q.id); markStrict(q); }
    }
  }

  // Fallback cuoi
  if (picked.length < S1) {
    const rest = QUESTIONS
      .filter(q => q.role === role && !usedIds.has(q.id))
      .sort(() => Math.random() - 0.5);
    for (const q of rest) {
      if (picked.length >= S1) break;
      picked.push(q); usedIds.add(q.id);
    }
  }

  return picked.slice(0, S1).sort(() => Math.random() - 0.5);
}

function pickStage2(role, routing, excludeIds, weakGroups) {
  // Phase 2: 3 cau chuyen sau dua tren ket qua Phase 1
  const S2 = 3;
  weakGroups = weakGroups || [];
  const kcs = (SKILL_KEYS[role] || []);
  const usedIds = new Set(excludeIds);
  const picked = [];

  const weakCount = {};
  for (const kc of weakGroups) weakCount[kc] = (weakCount[kc] || 0) + 1;

  const priorityKCs = [...kcs].sort((a, b) => (weakCount[b] || 0) - (weakCount[a] || 0));

  const diffOrder = routing === 'STRONG' ? ['ADVANCED', 'INTERMEDIATE', 'BEGINNER']
                  : routing === 'WEAK'   ? ['INTERMEDIATE', 'BEGINNER', 'ADVANCED']
                  :                        ['INTERMEDIATE', 'ADVANCED', 'BEGINNER'];

  for (const kc of priorityKCs) {
    if (picked.length >= S2) break;
    const pool = QUESTIONS
      .filter(q => q.role === role && !usedIds.has(q.id) && q.skillGroups && q.skillGroups.includes(kc))
      .sort(() => Math.random() - 0.5);
    if (!pool.length) continue;
    let chosen = null;
    for (const d of diffOrder) {
      chosen = pool.find(q => q.difficulty === d);
      if (chosen) break;
    }
    chosen = chosen || pool[0];
    picked.push(chosen); usedIds.add(chosen.id);
  }

  // Fallback: bat ky cau nao cua role chua dung
  if (picked.length < S2) {
    const rest = QUESTIONS
      .filter(q => q.role === role && !usedIds.has(q.id))
      .sort(() => Math.random() - 0.5);
    for (const q of rest) {
      if (picked.length >= S2) break;
      picked.push(q); usedIds.add(q.id);
    }
  }

  return picked.slice(0, S2).sort(() => Math.random() - 0.5);
}

// ── Shared KT pipeline (EMA -> DKT -> Blend 70/30) ──────────────
// Dung CHUNG cho finalize (screens-diagnostic) va KT MODEL (RoadmapScreen)
// de con so dong bo nhau tuyet doi.
function _ema(cur, score){ const a=0.35; return Math.round((a*score+(1-a)*cur)*100)/100; }
function _dkt(prior, score, hist){
  const lr=Math.min(0.4, 0.15+hist*0.02);
  const target=score>0.6?Math.min(prior+lr*(1-prior),0.98):Math.max(prior-lr*prior,0.02);
  const obs=score>0.5?0.9:0.1;
  return Math.round((obs*target)/(obs*target+(1-obs)*(1-target))*100)/100;
}
function _blend(kt, ema){ return Math.round((0.7*kt+0.3*ema)*100)/100; }

// events: [{kc, score}] theo thu tu; prevVec: {kc: 0..1} hoac null
// tra ve {ema, kt, blend} moi cai la {kc: 0..1}
function mstSkillVector(role, events, prevVec){
  const kcs = SKILL_KEYS[role] || [];
  const ema={}, kt={}, blend={};
  kcs.forEach(k => { const v = (prevVec && prevVec[k]!=null) ? prevVec[k] : 0.3; ema[k]=kt[k]=blend[k]=v; });
  let hist=0;
  for(const ev of (events||[])){
    const kc=ev.kc;
    if(ema[kc]==null){ ema[kc]=kt[kc]=blend[kc]=0.3; }
    hist++;
    ema[kc]=_ema(ema[kc], ev.score);
    kt[kc] = hist>=3 ? _dkt(kt[kc], ev.score, hist) : ema[kc];
    blend[kc]=_blend(kt[kc], ema[kc]);
  }
  return { ema, kt, blend, kcs };
}

Object.assign(window, {
  StoreContext, StoreProvider, useStore,
  I18N, QUESTIONS, SKILL_AXES, SKILL_KEYS, ROLE_TARGETS, DEFAULTS,
  roleColor, avatarColor, currentVector, callAPI,
  calcDelta, scoreAnswer, mstAvgScore, mstRouting, pickStage1, pickStage2,
  mstSkillVector,
});
