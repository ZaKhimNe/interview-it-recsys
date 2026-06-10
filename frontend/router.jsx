// ============================================================
// router.jsx — top-level App with hash routing
// ============================================================

const ROUTES = ['landing','onboarding','home','interview','questions','dashboard','roadmap','history','notes','settings','profile','diagnostic'];

function parseHash() {
  const h = (location.hash || '#/landing').replace(/^#\/?/, '');
  const [route, ...rest] = h.split('/');
  return { route: ROUTES.includes(route) ? route : 'landing', sub: rest.join('/') };
}

function App() {
  const [{ route }, setLoc] = React.useState(parseHash);
  const [opts, setOpts] = React.useState(null);

  React.useEffect(() => {
    const handler = () => setLoc(parseHash());
    window.addEventListener('hashchange', handler);
    return () => window.removeEventListener('hashchange', handler);
  }, []);

  const navigate = (r, o) => {
    setOpts(o || null);
    location.hash = `#/${r}`;
  };

  return (
    <StoreProvider>
      <AppShell route={route} opts={opts} onNav={navigate} />
    </StoreProvider>
  );
}

function AppShell({ route, opts, onNav }) {
  const { state } = useStore();

  // Chưa có role → redirect về onboarding
  const effectiveRoute = (!state.role && route !== 'landing' && route !== 'onboarding')
    ? 'onboarding' : route;

  const showSidebar = effectiveRoute !== 'landing' && effectiveRoute !== 'onboarding';
  return (
    <>
      <AnimatedBackground route={effectiveRoute} role={state.role} />
      <div className={`shell ${showSidebar ? '' : 'no-side'}`}>
        {showSidebar && <Sidebar route={effectiveRoute} onNav={onNav} />}
        <main className={`main ${effectiveRoute === 'landing' ? 'wide' : ''}`}>
          {showSidebar && <TopBar route={effectiveRoute} crumb={effectiveRoute.toUpperCase()} />}
          <div className="fadeUp" key={effectiveRoute}>
            {effectiveRoute === 'landing'     && <LandingScreen onNav={onNav} />}
            {effectiveRoute === 'onboarding'  && <OnboardingScreen onNav={onNav} />}
            {effectiveRoute === 'home'        && <HomeScreen onNav={onNav} />}
            {effectiveRoute === 'interview'   && <InterviewScreen onNav={onNav} opts={opts} />}
            {effectiveRoute === 'questions'   && <QuestionsScreen onNav={onNav} />}
            {effectiveRoute === 'dashboard'   && <DashboardScreen onNav={onNav} />}
            {effectiveRoute === 'roadmap'     && <RoadmapScreen onNav={onNav} />}
            {effectiveRoute === 'history'     && <HistoryScreen onNav={onNav} />}
            {effectiveRoute === 'notes'       && <NotesScreen onNav={onNav} />}
            {effectiveRoute === 'settings'    && <SettingsScreen onNav={onNav} />}
            {effectiveRoute === 'profile'     && <ProfileScreen onNav={onNav} />}
            {effectiveRoute === 'diagnostic'  && <DiagnosticScreen onNav={onNav} />}
          </div>
        </main>
      </div>
    </>
  );
}

window.App = App;
