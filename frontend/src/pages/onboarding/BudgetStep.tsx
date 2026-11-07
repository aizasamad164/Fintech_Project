import { useState } from 'react'
import { C, DISPLAY } from '../../theme/tokens'
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
      <div className="text-center">
        <h1 className="leading-tight mb-4 fade-up" style={{ fontFamily: DISPLAY, color: C.text, fontSize: 'clamp(2.4rem, 6vw, 3.6rem)' }}>
          How much are you starting with?
        </h1>
        <p className="text-lg font-semibold mb-10 mx-auto leading-relaxed fade-up d1" style={{ color: C.text2, maxWidth: 520 }}>
          Your total practice budget. No brokerage account needed; we'll show you what a portfolio at this amount could look like.
        </p>
      </div>

      <div className="glass rounded-3xl p-6 sm:p-8 fade-up d2" style={{ border: `1px solid ${C.border}` }}>
        <label htmlFor="budget" className="block text-sm font-bold mb-3" style={{ color: C.muted }}>Amount in US dollars</label>
        <div className="relative mb-3">
          <span className="absolute left-5 top-1/2 -translate-y-1/2 text-4xl" style={{ color: C.muted, fontFamily: DISPLAY }}>$</span>
          <input id="budget" type="number" inputMode="decimal" placeholder="5,000" value={val}
            onChange={e => { setVal(e.target.value); setErr('') }} onKeyDown={e => e.key === 'Enter' && submit()}
            className="w-full pl-14 pr-5 py-5 rounded-2xl outline-none transition-all"
            style={{ backgroundColor: 'rgba(10,16,27,0.8)', border: `2px solid ${val ? C.pink : C.border}`, color: C.text,
              fontFamily: DISPLAY, fontSize: '2.6rem', boxShadow: val ? `0 0 0 4px ${C.pink}26` : 'none' }} autoFocus />
        </div>
        {err && <p className="text-base font-bold mb-2 fade-in" style={{ color: C.pink }} role="alert">{err}</p>}
        <div className="text-sm font-bold mt-5 mb-3" style={{ color: C.muted }}>Or pick a starting amount</div>
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
          {PRESETS.map(a => {
            const on = val === String(a)
            return (
              <button key={a} onClick={() => { setVal(String(a)); setErr('') }} className="pressable py-3 rounded-xl text-base font-bold"
                style={{ border: `2px solid ${on ? C.pink : C.border}`, color: on ? C.canvas : C.text, backgroundColor: on ? C.pink : 'rgba(10,16,27,0.6)' }}>
                {fmt(a)}
              </button>
            )
          })}
        </div>
      </div>

      <div className="flex justify-center mt-10 fade-up d4">
        <BigCta onClick={submit} disabled={!val}>Set budget and continue →</BigCta>
      </div>
    </OnboardShell>
  )
}
