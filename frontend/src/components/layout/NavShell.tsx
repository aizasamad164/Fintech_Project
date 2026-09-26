import { useLayoutEffect, useRef, type ReactNode } from 'react'
import { C } from '../../theme/tokens'
import type { Tab } from '../../types/portfolio'

const NAV_TABS: { id: Tab; label: string; icon: ReactNode }[] = [
  { id: 'portfolio', label: 'Portfolio', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="2" y="10" width="4" height="8" rx="1" fill="currentColor" opacity="0.6" /><rect x="8" y="6" width="4" height="12" rx="1" fill="currentColor" /><rect x="14" y="2" width="4" height="16" rx="1" fill="currentColor" opacity="0.8" /></svg> },
  { id: 'insights', label: 'Insights', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2L12.5 8H18L13.5 11.5L15.5 18L10 14.5L4.5 18L6.5 11.5L2 8H7.5L10 2Z" fill="currentColor" opacity="0.85" /></svg> },
  { id: 'learn', label: 'Learn', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M2 5C2 4 3 3 4 3H16C17 3 18 4 18 5V13C18 14 17 15 16 15H11L10 18L9 15H4C3 15 2 14 2 13V5Z" stroke="currentColor" strokeWidth="1.5" fill="none" /><line x1="5" y1="7" x2="15" y2="7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /><line x1="5" y1="10" x2="12" y2="10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg> },
  { id: 'account', label: 'Account', icon: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="7" r="3" stroke="currentColor" strokeWidth="1.5" /><path d="M3 18C3 14.686 6.134 12 10 12C13.866 12 17 14.686 17 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg> },
]

const ORDER: Tab[] = ['portfolio', 'insights', 'learn', 'account']

export default function NavShell({ tab, setTab, children }: { tab: Tab; setTab: (t: Tab) => void; children: ReactNode }) {
  // Moving right in the tab order pushes in from the right, and vice versa
  const prev = useRef(tab)
  const dir = ORDER.indexOf(tab) >= ORDER.indexOf(prev.current) ? 'push-fwd' : 'push-back'
  const scrollRef = useRef<HTMLDivElement>(null)
  useLayoutEffect(() => {
    if (prev.current !== tab && scrollRef.current) scrollRef.current.scrollTop = 0
    prev.current = tab
  }, [tab])
  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: C.canvas }}>
      {/* Desktop left rail */}
      <div className="hidden lg:flex flex-col w-56 flex-shrink-0" style={{ backgroundColor: C.surface, borderRight: `1px solid ${C.border}` }}>
        <div className="px-5 py-5" style={{ borderBottom: `1px solid ${C.border}` }}>
          <div className="text-lg font-semibold" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>StockSense</div>
          <div className="text-[10px] mt-0.5" style={{ color: C.muted }}>Educational only</div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className="relative w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all"
              style={{ backgroundColor: tab === t.id ? `${C.cyan}15` : 'transparent', color: tab === t.id ? C.cyan : C.muted, fontWeight: tab === t.id ? 600 : 400 }}>
              {tab === t.id && <span className="absolute left-0 top-2 bottom-2 w-[3px] rounded-full" style={{ backgroundColor: C.pink, boxShadow: `0 0 8px ${C.pink}` }} />}
              <span style={{ color: tab === t.id ? C.cyan : C.muted }}>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </nav>
        <div className="px-5 py-4" style={{ borderTop: `1px solid ${C.border}` }}>
          <div className="text-[10px]" style={{ color: C.border, lineHeight: 1.5 }}>For educational use only. No funds held, no trades executed.</div>
        </div>
      </div>

      {/* Content */}
      <div ref={scrollRef} data-scroll-root className="flex-1 overflow-y-auto overflow-x-hidden pb-16 lg:pb-0">
        <div key={tab} className={dir}>{children}</div>
      </div>

      {/* Mobile bottom tab bar */}
      <div className="fixed bottom-0 left-0 right-0 flex lg:hidden" style={{ backgroundColor: C.surface, borderTop: `1px solid ${C.border}`, zIndex: 50 }}>
        {NAV_TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className="flex-1 flex flex-col items-center gap-1 py-2 transition-all"
            style={{ color: tab === t.id ? C.cyan : C.muted }}>
            {t.icon}
            <span className="text-[10px]" style={{ fontWeight: tab === t.id ? 600 : 400 }}>{t.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
