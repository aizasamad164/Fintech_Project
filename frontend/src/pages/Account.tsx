import { C, HEADING } from '../theme/tokens'
import PageHeader from '../components/ui/PageHeader'

const SETTINGS: [string, string, string][] = [
  ['Notifications', 'Portfolio updates and market alerts', C.cyan],
  ['Privacy', 'Data usage and permissions', C.violet],
  ['About', 'StockSense v1.0, educational software', C.teal],
]

// TODO (backend): pull the real email + plan from Supabase auth / profiles table.
export default function Account({ isPro, onUpgrade, onSignOut }: { isPro: boolean; onUpgrade: () => void; onSignOut: () => void }) {
  return (
    <div className="px-4 sm:px-8 py-8 max-w-3xl mx-auto">
      <PageHeader title="Account" />

      <section className="glass rounded-2xl p-6 mb-5 flex items-center gap-4 fade-up d1" style={{ border: `1px solid ${C.border}` }}>
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl" style={{ backgroundColor: C.violet, color: C.canvas, fontFamily: HEADING, fontWeight: 600, letterSpacing: '-0.025em' }}>D</div>
        <div>
          <div className="text-lg font-semibold" style={{ color: C.text }}>demo@stocksense.app</div>
          <div className="text-base font-bold mt-1 flex items-center gap-2" style={{ color: isPro ? C.teal : C.muted }}>
            {isPro && <span className="w-2 h-2 rounded-full" style={{ backgroundColor: C.teal }} />}{isPro ? 'Pro member' : 'Free plan'}
          </div>
        </div>
      </section>

      {!isPro && (
        <section className="relative overflow-hidden rounded-2xl p-6 mb-5 flex flex-wrap items-center justify-between gap-4 fade-up d2"
          style={{ background: 'linear-gradient(120deg, #F535AA33, #9A8FFF22, #4FD8E81a)', border: `2px solid ${C.pink}66` }}>
          <div>
            <div className="text-lg font-semibold mb-1" style={{ color: C.text }}>Upgrade to Pro</div>
            <div className="text-base font-semibold" style={{ color: C.text2 }}>Unlock Healthcare, Multi-Sector and the full Insights ranking</div>
          </div>
          <button onClick={onUpgrade} className="cta px-6 py-3 rounded-xl text-[0.95rem] font-semibold"
            style={{ background: 'linear-gradient(90deg, #F535AA, #9A8FFF, #4FD8E8)', color: C.canvas, ['--glow' as string]: C.pink }}>Upgrade · $9/mo</button>
        </section>
      )}

      <div className="space-y-3">
        {SETTINGS.map(([title, sub, accent], i) => (
          <button key={title} className={`tint-fill glass w-full text-left rounded-2xl p-5 flex items-center justify-between fade-up d${i + 3}`}
            style={{ ['--fill' as string]: accent, border: `2px solid ${C.border}` }}>
            <div>
              <div className="text-base font-semibold" style={{ color: C.text }}>{title}</div>
              <div className="text-sm font-semibold mt-0.5" style={{ color: C.text2 }}>{sub}</div>
            </div>
            <svg width="20" height="20" viewBox="0 0 16 16" fill="none" style={{ color: C.text2 }} aria-hidden><path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
          </button>
        ))}
      </div>
      <button onClick={onSignOut} className="pressable w-full py-3.5 rounded-xl text-[0.95rem] font-semibold mt-6 fade-up d6"
        style={{ border: `2px solid ${C.border}`, color: C.text2, backgroundColor: 'rgba(19,29,48,0.6)' }}>Sign out</button>
    </div>
  )
}
