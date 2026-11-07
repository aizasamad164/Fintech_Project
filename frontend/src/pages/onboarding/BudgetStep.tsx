import { useState } from 'react'
import { C, HEADING } from '../../theme/tokens'
import { fmt } from '../../utils/format'
import OnboardShell from '../../components/layout/OnboardShell'
import StepBar from '../../components/layout/StepBar'
import { BigCta } from '../../components/ui/Buttons'

const PRESETS = [500, 1000, 5000, 10000, 25000]

export default function BudgetStep({ onNext }: { onNext: (b: number) => void }) {
  const [val, setVal] = useState('')
  const [err, setErr] = useState('')
  const submit = () => {
    const n = parseFloat(val.replace(/[,$]/g, ''))
    if (isNaN(n) || n < 100) { setErr('Enter at least $100 to build a meaningful portfolio.'); return }
    if (n > 10_000_000) { setErr('Enter an amount up to $10,000,000.'); return }
    onNext(n)
  }
  return (
    <OnboardShell>
      <StepBar step={1} />
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl sm:text-4xl font-semibold mb-3 fade-up" style={{ fontFamily: HEADING, color: C.text, letterSpacing: '-0.025em' }}>
            How much are you starting with?
          </h1>
          <p className="text-base font-medium mx-auto fade-up d1" style={{ color: C.muted, maxWidth: 500 }}>
            Your total practice budget. No brokerage account needed. We'll show you what a portfolio at this amount could look like.
          </p>
        </div>

        <div className="glass rounded-2xl p-6 sm:p-7 fade-up d2" style={{ border: `1px solid ${C.border}` }}>
          <label htmlFor="budget" className="block text-xs font-semibold uppercase mb-2.5" style={{ color: C.muted, letterSpacing: '0.1em' }}>Amount (USD)</label>
          <div className="relative">
            <span className="absolute left-5 top-1/2 -translate-y-1/2 text-2xl font-semibold" style={{ color: C.muted, fontFamily: HEADING }}>$</span>
            <input id="budget" type="number" inputMode="decimal" placeholder="5,000" value={val}
              onChange={e => { setVal(e.target.value); setErr('') }} onKeyDown={e => e.key === 'Enter' && submit()}
              className="w-full pl-11 pr-5 py-4 rounded-xl outline-none transition-all text-3xl font-semibold"
              style={{ backgroundColor: 'rgba(10,16,27,0.75)', border: `1px solid ${val ? C.pink : C.border}`, color: C.text,
                fontFamily: HEADING, letterSpacing: '-0.02em', boxShadow: val ? `0 0 0 3px ${C.pink}22` : 'none' }} autoFocus />
          </div>
          {err && <p className="text-sm font-semibold mt-2.5 fade-in" style={{ color: C.pink }} role="alert">{err}</p>}
          <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 mt-5">
            {PRESETS.map(a => {
              const on = val === String(a)
              return (
                <button key={a} onClick={() => { setVal(String(a)); setErr('') }} className="pressable py-2.5 rounded-lg text-sm font-semibold"
                  style={{ border: `1px solid ${on ? C.pink : C.border}`, color: on ? C.text : C.text2, backgroundColor: on ? `${C.pink}26` : 'rgba(10,16,27,0.55)' }}>
                  {fmt(a)}
                </button>
              )
            })}
          </div>
        </div>

        <div className="flex justify-center mt-8 fade-up d4">
          <BigCta onClick={submit} disabled={!val}>Set budget and continue</BigCta>
        </div>
      </div>
    </OnboardShell>
  )
}
