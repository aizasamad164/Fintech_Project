import { useState } from 'react'
import { C } from '../../theme/tokens'
import { BackLink } from '../../components/ui/Buttons'

// TODO (backend): replace pay() with a real payment gateway session (e.g. Stripe Checkout)
// and only call onSuccess after the backend confirms the subscription.
export default function Checkout({ onSuccess, onBack }: { onSuccess: () => void; onBack: () => void }) {
  const [card, setCard] = useState('')
  const [exp, setExp] = useState('')
  const [cvc, setCvc] = useState('')
  const [paying, setPaying] = useState(false)
  const pay = () => { setPaying(true); setTimeout(onSuccess, 1200) }
  const input = (filled: string) => ({ backgroundColor: C.surface, border: `1px solid ${filled ? C.cyan : C.border}`, color: C.text, fontFamily: 'Inter' })
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-5 py-12" style={{ backgroundColor: C.canvas }}>
      <div className="w-full max-w-sm">
        <BackLink onClick={onBack} />
        <div className="p-4 rounded-xl mb-6 fade-up" style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold" style={{ color: C.text, fontFamily: 'Inter' }}>StockSense Pro</div>
              <div className="text-xs mt-0.5" style={{ color: C.muted, fontFamily: 'Inter' }}>Monthly subscription · cancel anytime</div>
            </div>
            <div className="text-lg font-semibold" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>$9.00</div>
          </div>
          <div className="mt-3 pt-3 flex items-center justify-between text-xs" style={{ borderTop: `1px solid ${C.border}`, color: C.muted, fontFamily: 'Inter' }}>
            <span>Total due today</span><span style={{ color: C.text, fontWeight: 600 }}>$9.00</span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-5 fade-up d1">
          <button onClick={pay} className="flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all hover:opacity-90"
            style={{ backgroundColor: '#000', color: '#fff', fontFamily: 'Inter' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
            Apple Pay
          </button>
          <button onClick={pay} className="flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all hover:opacity-90"
            style={{ backgroundColor: C.surface, border: `1px solid ${C.border}`, color: C.text, fontFamily: 'Inter' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
            Google Pay
          </button>
        </div>
        <div className="flex items-center gap-3 mb-5 fade-up d2">
          <div className="flex-1 h-px" style={{ backgroundColor: C.border }} />
          <span className="text-xs" style={{ color: C.muted, fontFamily: 'Inter' }}>or pay by card</span>
          <div className="flex-1 h-px" style={{ backgroundColor: C.border }} />
        </div>
        <div className="space-y-3 mb-5 fade-up d3">
          <input placeholder="Card number" value={card} onChange={e => setCard(e.target.value)} maxLength={19} className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-all" style={input(card)} />
          <div className="grid grid-cols-2 gap-3">
            <input placeholder="MM / YY" value={exp} onChange={e => setExp(e.target.value)} maxLength={7} className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-all" style={input(exp)} />
            <input placeholder="CVC" value={cvc} onChange={e => setCvc(e.target.value)} maxLength={4} type="password" className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-all" style={input(cvc)} />
          </div>
        </div>
        <button onClick={pay} disabled={paying}
          className="w-full py-3.5 rounded-lg text-sm font-semibold transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-60 fade-up d4"
          style={{ backgroundColor: paying ? C.border : C.cyan, color: C.canvas, fontFamily: 'Inter' }}>
          {paying ? 'Processing…' : 'Confirm payment — $9.00'}
        </button>
        <div className="flex items-center justify-center gap-2 mt-4 fade-up d5">
          <svg width="12" height="12" viewBox="0 0 12 14" fill="none"><rect x="2" y="5" width="8" height="8" rx="1.5" stroke={C.muted} strokeWidth="1.2" /><path d="M4 5V4a2 2 0 014 0v1" stroke={C.muted} strokeWidth="1.2" /></svg>
          <span className="text-xs" style={{ color: C.muted, fontFamily: 'Inter' }}>Simulated only — no real payment processed</span>
        </div>
      </div>
    </div>
  )
}
