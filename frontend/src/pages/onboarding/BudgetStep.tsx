import { useState } from 'react'
import { C } from '../../theme/tokens'
import { fmt } from '../../utils/format'
import OnboardShell from '../../components/layout/OnboardShell'
import StepBar from '../../components/layout/StepBar'
import { CyanBtn } from '../../components/ui/Buttons'

export default function BudgetStep({ onNext }: { onNext: (b: number) => void }) {
  const [val, setVal] = useState('')
  const [err, setErr] = useState('')
  const submit = () => {
    const n = parseFloat(val.replace(/[,$]/g, ''))
    if (isNaN(n) || n < 100) { setErr('Enter at least $100 to generate a meaningful portfolio.'); return }
    if (n > 10_000_000) { setErr('Enter an amount up to $10,000,000.'); return }
    onNext(n)
  }
  return (
    <OnboardShell>
      <StepBar step={1} />
      <h1 className="text-3xl sm:text-4xl mb-3 leading-snug fade-up" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>How much are you starting with?</h1>
      <p className="text-sm mb-8 fade-up d1 leading-relaxed" style={{ color: C.muted, maxWidth: 420 }}>This is your total starting budget — no brokerage account needed. We'll show you what a portfolio at this amount could look like.</p>
      <div className="relative mb-3 fade-up d2">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-xl" style={{ color: C.muted, fontFamily: "'DM Serif Display'" }}>$</span>
        <input type="number" placeholder="5000" value={val} onChange={e => { setVal(e.target.value); setErr('') }} onKeyDown={e => e.key === 'Enter' && submit()}
          className="w-full pl-10 pr-4 py-4 text-2xl rounded-lg outline-none transition-all"
          style={{ backgroundColor: C.surface, border: `2px solid ${val ? C.pink : C.border}`, color: C.text, fontFamily: "'DM Serif Display'", boxShadow: val ? `0 0 0 3px ${C.pink}22` : 'none' }} autoFocus />
      </div>
      {err && <p className="text-sm mb-4 fade-in" style={{ color: C.pink }}>{err}</p>}
      <div className="flex flex-wrap gap-2 mb-8 fade-up d3">
        {[500, 1000, 5000, 10000, 25000].map(a => (
          <button key={a} onClick={() => { setVal(String(a)); setErr('') }} className="px-3 py-1.5 text-xs rounded-md transition-all"
            style={{ border: `1px solid ${val === String(a) ? C.pink : C.border}`, color: val === String(a) ? C.pink : C.muted, backgroundColor: val === String(a) ? `${C.pink}18` : 'transparent' }}>
            {fmt(a)}
          </button>
        ))}
      </div>
      <div className="fade-up d4"><CyanBtn onClick={submit}>Set budget and continue</CyanBtn></div>
    </OnboardShell>
  )
}
