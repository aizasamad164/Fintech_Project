import { useState } from 'react'
import { C, DISPLAY } from '../../theme/tokens'
import { RISK_OPTS } from '../../data/options'
import OnboardShell from '../../components/layout/OnboardShell'
import StepBar from '../../components/layout/StepBar'
import { BigCta, GhostBtn } from '../../components/ui/Buttons'
import type { Risk } from '../../types/portfolio'

const METER: Record<Risk, number> = { Conservative: 1, Balanced: 2, Aggressive: 3 }

export default function RiskStep({ onNext, onBack }: { onNext: (r: Risk) => void; onBack: () => void }) {
  const [sel, setSel] = useState<Risk | null>(null)
  const selColor = RISK_OPTS.find(o => o.v === sel)?.color ?? C.cyan
  return (
    <OnboardShell>
      <StepBar step={2} />
      <div className="text-center mb-8">
        <h1 className="leading-tight mb-3 fade-up" style={{ fontFamily: DISPLAY, color: C.text, fontSize: 'clamp(2.2rem, 5.5vw, 3.2rem)' }}>
          How do you want to approach risk?
        </h1>
        <p className="text-lg font-semibold fade-up d1" style={{ color: C.text2 }}>This decides which companies we include and how much money each one gets.</p>
      </div>

      <div className="flex flex-col gap-4" role="radiogroup" aria-label="Risk strategy">
        {RISK_OPTS.map((opt, i) => {
          const on = sel === opt.v
          return (
            <button key={opt.v} role="radio" aria-checked={on} onClick={() => setSel(opt.v)} data-active={on}
              className={`fill-hover glass w-full text-left rounded-2xl px-6 py-5 sm:py-6 flex items-center gap-5 fade-up d${i + 2}`}
              style={{ ['--fill' as string]: opt.color, border: `2px solid ${C.border}` }}>
              {/* risk meter: 1-3 bars */}
              <div className="flex items-end gap-1 flex-shrink-0" aria-hidden>
                {[1, 2, 3].map(b => (
                  <span key={b} className={`w-2.5 rounded-sm ${b <= METER[opt.v] ? 'on-fill-bar' : 'on-fill-track'}`} style={{ height: 10 + b * 9, backgroundColor: b <= METER[opt.v] ? opt.color : C.border }} />
                ))}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-2xl font-bold mb-1" style={{ color: opt.color }}>{opt.v}</div>
                <p className="text-base font-medium leading-relaxed" style={{ color: C.text2 }}>{opt.desc}</p>
              </div>
              <div className="hidden sm:block text-right flex-shrink-0">
                <div className="text-xs font-bold uppercase" style={{ color: C.muted, letterSpacing: '0.08em' }}>Typical range</div>
                <div className="text-lg font-bold" style={{ color: opt.color }}>{opt.range.replace(' est. return', '')}</div>
              </div>
              <span className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold"
                style={{ border: `2px solid ${on ? C.canvas : C.border}`, color: C.canvas }}>{on ? '✓' : ''}</span>
            </button>
          )
        })}
      </div>

      <div className="flex flex-col-reverse sm:flex-row items-center justify-center gap-3 mt-10 fade-up d6">
        <GhostBtn onClick={onBack}>← Back</GhostBtn>
        <BigCta onClick={() => sel && onNext(sel)} disabled={!sel} color={selColor}>
          {sel ? `Continue with ${sel} →` : 'Choose a strategy'}
        </BigCta>
      </div>
    </OnboardShell>
  )
}
