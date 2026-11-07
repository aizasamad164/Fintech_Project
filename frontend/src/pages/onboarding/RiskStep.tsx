import { useState } from 'react'
import { C, HEADING } from '../../theme/tokens'
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
        <h1 className="text-3xl sm:text-4xl font-semibold mb-3 fade-up" style={{ fontFamily: HEADING, color: C.text, letterSpacing: '-0.025em' }}>
          How do you want to approach risk?
        </h1>
        <p className="text-base font-medium fade-up d1" style={{ color: C.muted }}>This decides which companies we include and how much money each one gets.</p>
      </div>

      <div className="flex flex-col gap-3" role="radiogroup" aria-label="Risk strategy">
        {RISK_OPTS.map((opt, i) => {
          const on = sel === opt.v
          return (
            <button key={opt.v} role="radio" aria-checked={on} onClick={() => setSel(opt.v)} data-active={on}
              className={`tint-fill glass w-full text-left rounded-xl px-5 sm:px-6 py-5 flex items-center gap-5 fade-up d${i + 2}`}
              style={{ ['--fill' as string]: opt.color, border: `1px solid ${C.border}` }}>
              <div className="flex items-end gap-1 flex-shrink-0" aria-hidden>
                {[1, 2, 3].map(b => (
                  <span key={b} className="w-1.5 rounded-sm" style={{ height: 8 + b * 7, backgroundColor: b <= METER[opt.v] ? opt.color : C.border }} />
                ))}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-lg font-semibold mb-0.5" style={{ fontFamily: HEADING, color: C.text, letterSpacing: '-0.01em' }}>{opt.v}</div>
                <p className="text-sm font-medium leading-relaxed" style={{ color: C.text2 }}>{opt.desc}</p>
              </div>
              <div className="hidden sm:block text-right flex-shrink-0 w-28">
                <div className="text-[10px] font-semibold uppercase" style={{ color: C.muted, letterSpacing: '0.12em' }}>Typical range</div>
                <div className="text-base font-semibold" style={{ color: opt.color }}>{opt.range.replace(' est. return', '')}</div>
              </div>
              <span className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold"
                style={{ border: `1.5px solid ${on ? opt.color : C.border}`, backgroundColor: on ? opt.color : 'transparent', color: C.canvas }}>{on ? '✓' : ''}</span>
            </button>
          )
        })}
      </div>

      <div className="flex flex-col-reverse sm:flex-row items-center justify-center gap-3 mt-9 fade-up d6">
        <GhostBtn onClick={onBack}>Back</GhostBtn>
        <BigCta onClick={() => sel && onNext(sel)} disabled={!sel} color={selColor}>
          {sel ? `Continue with ${sel}` : 'Choose a strategy'}
        </BigCta>
      </div>
    </OnboardShell>
  )
}
