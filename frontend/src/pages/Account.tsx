import { useState } from 'react'
import { C, HEADING } from '../theme/tokens'
import PageHeader from '../components/ui/PageHeader'
import { cancelSubscription, type BillingStatus } from '../services/billingService'

const SETTINGS: [string, string, string][] = [
  ['Notifications', 'Portfolio updates and market alerts', C.cyan],
  ['Privacy', 'Data usage and permissions', C.violet],
  ['About', 'StockSense v1.0, educational software', C.teal],
]

interface Props {
  isPro: boolean
  email: string | null
  demo: boolean
  billing: BillingStatus | null
  onBilling: (b: BillingStatus) => void
  onUpgrade: () => void
  onSignOut: () => void
}

const day = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : null)

export default function Account({ isPro, email, demo, billing, onBilling, onUpgrade, onSignOut }: Props) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const initial = (email ?? 'D').trim().charAt(0).toUpperCase()

  const cancel = async () => {
    if (!window.confirm('Cancel Pro? You keep it until the end of the current billing period.')) return
    setBusy(true); setError(null)
    try { onBilling(await cancelSubscription()) } catch (e) { setError(e instanceof Error ? e.message : 'Could not cancel.') } finally { setBusy(false) }
  }

  return (
    <div className="px-4 sm:px-8 py-8 max-w-3xl mx-auto">
      <PageHeader title="Account" />

      <section className="glass rounded-2xl p-6 mb-5 flex items-center gap-4 fade-up d1" style={{ border: `1px solid ${C.border}` }}>
        <div className="w-14 h-14 rounded-xl flex items-center justify-center text-xl" style={{ backgroundColor: C.violet, color: C.canvas, fontFamily: HEADING, fontWeight: 600 }}>{initial}</div>
        <div className="min-w-0">
          <div className="text-lg font-semibold truncate" style={{ color: C.text }}>{demo ? 'Demo user' : email ?? 'Signed in'}</div>
          <div className="text-sm font-semibold mt-0.5 flex items-center gap-2" style={{ color: isPro ? C.teal : C.muted }}>
            {isPro && <span className="w-2 h-2 rounded-full" style={{ backgroundColor: C.teal }} />}
            {isPro ? `Pro member${billing?.simulated ? ' (simulated)' : ''}` : 'Free plan'}
            {demo && <span style={{ color: C.muted }}>· demo mode, data stays in this browser</span>}
          </div>
        </div>
      </section>

      {isPro ? (
        <section className="glass rounded-2xl p-6 mb-5 flex flex-wrap items-center justify-between gap-4 fade-up d2" style={{ border: `1px solid ${C.teal}66` }}>
          <div>
            <div className="text-base font-semibold" style={{ color: C.text }}>StockSense Pro · $9/month</div>
            <div className="text-sm font-medium mt-0.5" style={{ color: C.text2 }}>
              {billing?.cancel_at_period_end
                ? `Cancelled. Pro stays on until ${day(billing.current_period_end) ?? 'the end of this period'}.`
                : billing?.current_period_end ? `Renews on ${day(billing.current_period_end)}.` : 'Active.'}
            </div>
          </div>
          {!billing?.cancel_at_period_end && (
            <button onClick={cancel} disabled={busy} className="pressable px-5 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-60"
              style={{ border: `1px solid ${C.border}`, color: C.text2 }}>{busy ? 'Cancelling…' : 'Cancel subscription'}</button>
          )}
        </section>
      ) : (
        <section className="relative overflow-hidden rounded-2xl p-6 mb-5 flex flex-wrap items-center justify-between gap-4 fade-up d2"
          style={{ background: 'linear-gradient(120deg, #F535AA26, #9A8FFF1a, #4FD8E814)', border: `1px solid ${C.pink}66` }}>
          <div>
            <div className="text-base font-semibold mb-0.5" style={{ color: C.text }}>Upgrade to Pro</div>
            <div className="text-sm font-medium" style={{ color: C.text2 }}>Unlock Healthcare, Multi-Sector and the full Insights ranking</div>
          </div>
          <button onClick={onUpgrade} className="cta px-6 py-3 rounded-xl text-[0.95rem] font-semibold"
            style={{ background: 'linear-gradient(90deg, #F535AA, #9A8FFF, #4FD8E8)', color: C.canvas, ['--glow' as string]: C.pink }}>Upgrade · $9/mo</button>
        </section>
      )}
      {error && <p className="text-sm font-semibold mb-4" style={{ color: C.pink }} role="alert">{error}</p>}

      <div className="space-y-3">
        {SETTINGS.map(([title, sub, accent], i) => (
          <button key={title} className={`tint-fill glass w-full text-left rounded-2xl p-5 flex items-center justify-between fade-up d${i + 3}`}
            style={{ ['--fill' as string]: accent, border: `1px solid ${C.border}` }}>
            <div>
              <div className="text-base font-semibold" style={{ color: C.text }}>{title}</div>
              <div className="text-sm font-medium mt-0.5" style={{ color: C.text2 }}>{sub}</div>
            </div>
            <svg width="20" height="20" viewBox="0 0 16 16" fill="none" style={{ color: C.text2 }} aria-hidden><path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
          </button>
        ))}
      </div>
      <button onClick={onSignOut} className="pressable w-full py-3.5 rounded-xl text-[0.95rem] font-semibold mt-6 fade-up d6"
        style={{ border: `1px solid ${C.border}`, color: C.text2, backgroundColor: 'rgba(19,29,48,0.6)' }}>{demo ? 'Leave demo mode' : 'Sign out'}</button>
    </div>
  )
}
