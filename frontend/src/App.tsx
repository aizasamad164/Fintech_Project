// App.tsx is the "traffic controller": it only decides WHICH screen to show
// and holds the shared state (budget, risk, sector, pro status).
// All UI lives in pages/ and components/.
import { useCallback, useState } from 'react'
import type { DashVariant, Risk, Screen, Sector, Tab } from './types/portfolio'
import { LESSONS } from './data/lessons'

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

  const handleViewPortfolio = useCallback((s: Sector, r: Risk) => { setSector(s); setRisk(r); setTab('portfolio') }, [])

  // Onboarding (full-screen, before the nav appears)
  if (screen === 'login') return <Login onLogin={() => setScreen('budget')} />
  if (screen === 'budget') return <BudgetStep onNext={b => { setBudget(b); setScreen('risk') }} />
  if (screen === 'risk') return <RiskStep onNext={r => { setRisk(r); setScreen('sector') }} onBack={() => setScreen('budget')} />
  if (screen === 'sector') return <SectorStep onNext={s => { setSector(s); setScreen('processing') }} onBack={() => setScreen('risk')} />
  if (screen === 'processing') return <Processing onDone={() => setScreen('nav')} />

  // Pro flow (full-screen, outside the nav)
  if (screen === 'paywall') return <Paywall onUpgrade={() => setScreen('checkout')} onBack={() => setScreen('nav')} />
  if (screen === 'checkout') return <Checkout onSuccess={() => setScreen('pro-success')} onBack={() => setScreen('paywall')} />
  if (screen === 'pro-success') return <ProSuccess onDone={() => { setIsPro(true); setTab('insights'); setScreen('nav') }} />

  // Main app with tabs
  return (
    <NavShell tab={tab} setTab={setTab}>
      {tab === 'portfolio' && (
        <Dashboard budget={budget} risk={risk} sector={sector} variant={dashVariant}
          onVariant={setDashVariant} onRisk={setRisk} onSector={setSector} onBudget={setBudget} />
      )}
      {tab === 'insights' && <Insights isPro={isPro} onUnlock={() => setScreen('paywall')} onViewPortfolio={handleViewPortfolio} />}
      {tab === 'learn' && (lessonId !== null
        ? <LessonDetail id={lessonId} onBack={() => setLessonId(null)} onNext={() => setLessonId((lessonId + 1) % LESSONS.length)} />
        : <LearnTab onLesson={setLessonId} />)}
      {tab === 'account' && <Account isPro={isPro} onUpgrade={() => setScreen('paywall')} onSignOut={() => { setIsPro(false); setScreen('login') }} />}
    </NavShell>
  )
}
