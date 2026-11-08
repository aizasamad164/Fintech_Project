import { useLayoutEffect, useRef, type ReactNode } from 'react'
import { C, HEADING } from '../../theme/tokens'
import LiveBackdrop from '../effects/LiveBackdrop'
import type { Tab } from '../../types/portfolio'

const NAV_TABS: { id: Tab; label: string; icon: ReactNode }[] = [
  { id: 'portfolio', label: 'Portfolio', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="2" y="10" width="4" height="8" rx="1" fill="currentColor" opacity="0.6" /><rect x="8" y="6" width="4" height="12" rx="1" fill="currentColor" /><rect x="14" y="2" width="4" height="16" rx="1" fill="currentColor" opacity="0.8" /></svg> },
  { id: 'insights', label: 'Insights', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2L12.5 8H18L13.5 11.5L15.5 18L10 14.5L4.5 18L6.5 11.5L2 8H7.5L10 2Z" fill="currentColor" opacity="0.85" /></svg> },
  { id: 'tracking', label: 'Tracking', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M2 15L7 9L11 12L18 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /><circle cx="18" cy="4" r="1.8" fill="currentColor" /></svg> },
  { id: 'shariah', label: 'Shariah', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M12.5 3.2A7 7 0 1 0 16.8 12.5 5.6 5.6 0 0 1 12.5 3.2Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" /><path d="M15 5.2l.55 1.15 1.25.18-.9.88.21 1.25L15 8.07l-1.11.59.21-1.25-.9-.88 1.25-.18z" fill="currentColor" /></svg> },
  { id: 'advisor', label: 'Advisor', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 4.5C3 3.7 3.7 3 4.5 3H15.5C16.3 3 17 3.7 17 4.5V12.5C17 13.3 16.3 14 15.5 14H8L4 17V14H4.5C3.7 14 3 13.3 3 12.5V4.5Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /><circle cx="7" cy="8.5" r="1" fill="currentColor" /><circle cx="10" cy="8.5" r="1" fill="currentColor" /><circle cx="13" cy="8.5" r="1" fill="currentColor" /></svg> },
  { id: 'learn', label: 'Learn', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M2 5C2 4 3 3 4 3H16C17 3 18 4 18 5V13C18 14 17 15 16 15H11L10 18L9 15H4C3 15 2 14 2 13V5Z" stroke="currentColor" strokeWidth="1.5" fill="none" /><line x1="5" y1="7" x2="15" y2="7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /><line x1="5" y1="10" x2="12" y2="10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg> },
  { id: 'account', label: 'Account', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="7" r="3" stroke="currentColor" strokeWidth="1.5" /><path d="M3 18C3 14.686 6.134 12 10 12C13.866 12 17 14.686 17 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg> },
]

const ORDER: Tab[] = ['portfolio', 'insights', 'tracking', 'shariah', 'advisor', 'learn', 'account']

export default function NavShell({ tab, setTab, children, isPro = false }: { tab: Tab; setTab: (t: Tab) => void; children: ReactNode; isPro?: boolean }) {
  // Moving right in the tab order pushes in from the right, and vice versa
  const prev = useRef(tab)
  const dir = ORDER.indexOf(tab) >= ORDER.indexOf(prev.current) ? 'push-fwd' : 'push-back'
  const scrollRef = useRef<HTMLDivElement>(null)
  useLayoutEffect(() => {
    if (prev.current !== tab && scrollRef.current) scrollRef.current.scrollTop = 0
    prev.current = tab
  }, [tab])
  return (
    <div className="relative flex flex-col h-screen overflow-hidden" style={{ backgroundColor: C.canvas }}>
      <LiveBackdrop intensity="subtle" />

      {/* ── Top bar ───────────────────────────────────────────────────── */}
      <header className="relative glass flex items-center gap-4 px-4 sm:px-6 h-16 flex-shrink-0"
        style={{ zIndex: 20, borderBottom: `1px solid ${C.border}` }}>
        <button onClick={() => setTab('portfolio')} className="flex items-center gap-2.5 flex-shrink-0" aria-label="StockSense home">
          <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden>
            <circle cx="14" cy="14" r="12" fill="none" stroke={C.cyan} strokeWidth="2.5" strokeDasharray="44 32" strokeLinecap="round" transform="rotate(-90 14 14)" />
            <circle cx="14" cy="14" r="7" fill="none" stroke={C.pink} strokeWidth="2.5" strokeDasharray="20 24" strokeLinecap="round" />
            <circle cx="14" cy="14" r="2" fill={C.text} />
          </svg>
          <span className="text-xl hidden sm:block" style={{ fontFamily: HEADING, fontWeight: 600, letterSpacing: '-0.025em', color: C.text }}>StockSense</span>
        </button>

        {/* Desktop tabs */}
        <nav className="hidden lg:flex items-center gap-1 mx-auto rounded-2xl p-1" style={{ backgroundColor: 'rgba(10,16,27,0.6)', border: `1px solid ${C.border}` }}>
          {NAV_TABS.map(t => {
            const on = tab === t.id
            return (
              <button key={t.id} onClick={() => setTab(t.id)} aria-current={on ? 'page' : undefined}
                className="relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all"
                style={{ backgroundColor: on ? C.cyan : 'transparent', color: on ? C.canvas : C.text2,
                  boxShadow: on ? `0 6px 20px -6px ${C.cyan}` : 'none' }}>
                <span style={{ color: on ? C.canvas : C.muted }}>{t.icon}</span>
                {t.label}
              </button>
            )
          })}
        </nav>

        <div className="ml-auto lg:ml-0 flex items-center gap-2 flex-shrink-0">
          <span className="text-xs font-bold px-3 py-1.5 rounded-full"
            style={isPro
              ? { background: 'linear-gradient(90deg, #F535AA, #9A8FFF, #4FD8E8)', color: C.canvas }
              : { color: C.muted, border: `1px solid ${C.border}` }}>
            {isPro ? 'PRO' : 'Free plan'}
          </span>
        </div>
      </header>

      {/* Mobile tabs: scrollable strip under the top bar */}
      <nav className="relative lg:hidden glass flex gap-1 overflow-x-auto px-3 py-2 flex-shrink-0" style={{ zIndex: 19, borderBottom: `1px solid ${C.border}` }}>
        {NAV_TABS.map(t => {
          const on = tab === t.id
          return (
            <button key={t.id} onClick={() => setTab(t.id)} aria-current={on ? 'page' : undefined}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-bold whitespace-nowrap transition-all"
              style={{ backgroundColor: on ? C.cyan : 'transparent', color: on ? C.canvas : C.text2 }}>
              <span style={{ color: on ? C.canvas : C.muted }}>{t.icon}</span>
              {t.label}
            </button>
          )
        })}
      </nav>

      {/* Content */}
      <div ref={scrollRef} data-scroll-root className="relative flex-1 overflow-y-auto overflow-x-hidden" style={{ zIndex: 1 }}>
        <div key={tab} className={dir}>{children}</div>
        <p className="text-center text-xs font-semibold py-8 px-4" style={{ color: C.muted, opacity: 0.8 }}>
          For educational use only. No funds held, no trades executed.
        </p>
      </div>
    </div>
  )
}
