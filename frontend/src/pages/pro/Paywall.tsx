import { C } from '../../theme/tokens'
import { BackLink } from '../../components/ui/Buttons'

const PERKS = ['Full Insights rankings — all 4 sectors unlocked', 'Side-by-side sector comparison tool', 'Historical data going back 5 years', 'Early access to new sectors as they launch', 'Priority support']

export default function Paywall({ onUpgrade, onBack }: { onUpgrade: () => void; onBack: () => void }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-5 py-12" style={{ backgroundColor: C.canvas }}>
      <div className="w-full max-w-sm">
        <BackLink onClick={onBack} />
        <div className="mb-2 fade-up">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold mb-4"
            style={{ border: `1px solid ${C.violet}50`, color: C.violet, backgroundColor: `${C.violet}12`, fontFamily: 'Inter' }}>
            <svg width="10" height="10" viewBox="0 0 12 14" fill="none"><rect x="2" y="5" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.5" /><path d="M4 5V4a2 2 0 014 0v1" stroke="currentColor" strokeWidth="1.5" /></svg>
            StockSense Pro
          </div>
          <h2 className="text-3xl mb-1" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>Unlock the full picture</h2>
          <div className="flex items-baseline gap-1 mt-3 mb-5">
            <span className="text-4xl font-semibold" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>$9</span>
            <span className="text-sm" style={{ color: C.muted, fontFamily: 'Inter' }}>/month · cancel anytime</span>
          </div>
        </div>
        <ul className="space-y-3 mb-8 fade-up d2">
          {PERKS.map((p, i) => (
            <li key={i} className="flex items-start gap-3 text-sm" style={{ color: C.text2, fontFamily: 'Inter' }}>
              <span className="w-4 h-4 rounded-full flex-shrink-0 flex items-center justify-center text-[9px] font-bold mt-0.5" style={{ backgroundColor: C.teal, color: C.canvas }}>✓</span>
              {p}
            </li>
          ))}
        </ul>
        {/* THE ONLY GRADIENT IN THE APP */}
        <button onClick={onUpgrade}
          className="w-full py-3.5 rounded-lg text-sm font-semibold transition-all hover:opacity-90 active:scale-[0.98] fade-up d3"
          style={{ background: 'linear-gradient(90deg, #8B7FF0 0%, #4FD8E8 100%)', color: C.canvas, fontFamily: 'Inter' }}>
          Upgrade to Pro — $9/month
        </button>
        <p className="text-xs text-center mt-3 fade-up d4" style={{ color: C.muted, fontFamily: 'Inter' }}>No commitments. Cancel from your account page at any time.</p>
        <p className="text-xs text-center mt-6 fade-up d5" style={{ color: C.border, fontFamily: 'Inter' }}>This is a simulated educational app. No real payment is processed.</p>
      </div>
    </div>
  )
}
