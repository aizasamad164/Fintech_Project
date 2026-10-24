// App.tsx is the "traffic controller": it only decides WHICH screen to show
// and holds the shared state (budget, risk, sector, pro status).
// All UI lives in pages/ and components/.
import { useCallback, useState, type ReactNode } from 'react'
import type { DashVariant, Portfolio, Risk, Screen, Sector, Tab } from './types/portfolio'
import { LESSONS } from './data/lessons'
import { prefetchPortfolio } from './services/portfolioService'

import NavShell from './components/layout/NavShell'
import Login from './pages/Login'
import BudgetStep from './pages/onboarding/BudgetStep'
import RiskStep from './pages/onboarding/RiskStep'
import SectorStep from './pages/onboarding/SectorStep'
import Processing from './pages/onboarding/Processing'
import Dashboard from './pages/Dashboard'
import Insights from './pages/Insights'
import LearnTab from './pages/learn/LearnTab'
import LessonDetail from './pages/learn/LessonDetail'
import Account from './pages/Account'
import Tracking from './pages/Tracking'
import Advisor from './pages/Advisor'
import Paywall from './pages/pro/Paywall'
import Checkout from './pages/pro/Checkout'
import ProSuccess from './pages/pro/ProSuccess'

export default function App() {
  const [screen, setScreen] = useState<Screen>('login')
  const [tab, setTab] = useState<Tab>('portfolio')
  const [budget, setBudget] = useState(5000)
  const [risk, setRisk] = useState<Risk>('Balanced')
  const [sector, setSector] = useState<Sector>('Technology')
  const [dashVariant, setDashVariant] = useState<DashVariant>('success')
  const [isPro, setIsPro] = useState(false)
  const [lessonId, setLessonId] = useState<number | null>(null)
  // Shared with the Advisor tab: what's on the dashboard, or which saved portfolio to discuss
  const [dashPortfolio, setDashPortfolio] = useState<Portfolio | null>(null)
  const [advisorPortfolioId, setAdvisorPortfolioId] = useState<string | null>(null)

  // Every full-screen change is a push edit: forward slides in from the right,
  // going back slides in from the left.
  const [dir, setDir] = useState<'push-fwd' | 'push-back'>('push-fwd')
  const go = useCallback((next: Screen, back = false) => { setDir(back ? 'push-back' : 'push-fwd'); setScreen(next) }, [])
  const wrap = (node: ReactNode) => <div key={screen} className={dir}>{node}</div>

  const handleViewPortfolio = useCallback((s: Sector, r: Risk) => { setSector(s); setRisk(r); setTab('portfolio') }, [])

  // Onboarding (full-screen, before the nav appears)
  if (screen === 'login') return wrap(<Login onLogin={() => go('budget')} />)
  if (screen === 'budget') return wrap(<BudgetStep onNext={b => { setBudget(b); go('risk') }} />)
  if (screen === 'risk') return wrap(<RiskStep onNext={r => { setRisk(r); go('sector') }} onBack={() => go('budget', true)} />)
  if (screen === 'sector') return wrap(<SectorStep onNext={s => { setSector(s); prefetchPortfolio(budget, risk, s); go('processing') }} onBack={() => go('risk', true)} />)
  if (screen === 'processing') return wrap(<Processing onDone={() => go('nav')} />)

  // Pro flow (full-screen, outside the nav)
  if (screen === 'paywall') return wrap(<Paywall onUpgrade={() => go('checkout')} onBack={() => go('nav', true)} />)
  if (screen === 'checkout') return wrap(<Checkout onSuccess={() => go('pro-success')} onBack={() => go('paywall', true)} />)
  if (screen === 'pro-success') return wrap(<ProSuccess onDone={() => { setIsPro(true); setTab('insights'); go('nav') }} />)

  // Main app with tabs
  return wrap(
    <NavShell tab={tab} setTab={setTab}>
      {tab === 'portfolio' && (
        <Dashboard budget={budget} risk={risk} sector={sector} variant={dashVariant}
          onVariant={setDashVariant} onRisk={setRisk} onSector={setSector} onBudget={setBudget}
          onPortfolio={setDashPortfolio} onOpenTracking={() => setTab('tracking')}
          onAskAdvisor={() => { setAdvisorPortfolioId(null); setTab('advisor') }} />
      )}
      {tab === 'insights' && <Insights isPro={isPro} onUnlock={() => go('paywall')} onViewPortfolio={handleViewPortfolio} />}
      {tab === 'tracking' && <Tracking onBuild={() => setTab('portfolio')}
        onAskAdvisor={id => { setAdvisorPortfolioId(id); setTab('advisor') }} />}
      {tab === 'advisor' && <Advisor dashboard={dashPortfolio} savedPortfolioId={advisorPortfolioId}
        onSavedPortfolioChange={setAdvisorPortfolioId} />}
      {tab === 'learn' && (lessonId !== null
        ? <div key={lessonId} className="push-fwd"><LessonDetail id={lessonId} onBack={() => setLessonId(null)} onNext={() => setLessonId((lessonId + 1) % LESSONS.length)} /></div>
        : <div key="list" className="push-back"><LearnTab onLesson={setLessonId} /></div>)}
      {tab === 'account' && <Account isPro={isPro} onUpgrade={() => go('paywall')} onSignOut={() => { setIsPro(false); go('login', true) }} />}
    </NavShell>
  )
}
