import { C } from '../theme/tokens'

const SETTINGS: [string, string][] = [
  ['Notifications', 'Portfolio updates and market alerts'],
  ['Privacy', 'Data usage and permissions'],
  ['About', 'StockSense v1.0 — educational software'],
]

// TODO (backend): pull the real email + plan from Supabase auth / profiles table.
export default function Account({ isPro, onUpgrade, onSignOut }: { isPro: boolean; onUpgrade: () => void; onSignOut: () => void }) {
  return (
    <div className="px-5 sm:px-8 py-6 max-w-xl mx-auto">
      <h2 className="text-2xl mb-8 fade-up" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>Account</h2>
      <div className="p-4 rounded-xl mb-4 fade-up d1" style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full flex items-center justify-center text-base font-bold" style={{ backgroundColor: `${C.violet}25`, color: C.violet, fontFamily: "'DM Serif Display'" }}>J</div>
          <div>
            <div className="text-sm font-semibold" style={{ color: C.text }}>demo@stocksense.app</div>
            <div className="text-xs mt-0.5 flex items-center gap-1.5" style={{ color: isPro ? C.teal : C.muted }}>
              {isPro ? (<><span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: C.teal }} />Pro member</>) : 'Free plan'}
            </div>
          </div>
        </div>
      </div>
      {!isPro && (
        <div className="p-4 rounded-xl mb-4 fade-up d2" style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold mb-0.5" style={{ color: C.text }}>Upgrade to Pro</div>
              <div className="text-xs" style={{ color: C.muted }}>Unlock all Insights sectors and more</div>
            </div>
            <button onClick={onUpgrade} className="px-4 py-2 rounded-lg text-xs font-semibold transition-all hover:opacity-90"
              style={{ background: 'linear-gradient(90deg, #F535AA, #8B7FF0, #4FD8E8)', color: C.canvas }}>Upgrade · $9/mo</button>
          </div>
        </div>
      )}
      {SETTINGS.map(([title, sub], i) => (
        <div key={title} className={`p-4 rounded-xl mb-3 fade-up d${i + 3}`} style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold" style={{ color: C.text }}>{title}</div>
              <div className="text-xs mt-0.5" style={{ color: C.muted }}>{sub}</div>
            </div>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style={{ color: C.muted }}><path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
          </div>
        </div>
      ))}
      <button onClick={onSignOut} className="w-full py-3 rounded-lg text-sm font-medium mt-4 fade-up d6 transition-all hover:opacity-80"
        style={{ border: `1px solid ${C.border}`, color: C.muted }}>Sign out</button>
      <p className="text-xs text-center mt-6 fade-up d7" style={{ color: C.border }}>For educational purposes only. No real funds or trades.</p>
    </div>
  )
}
