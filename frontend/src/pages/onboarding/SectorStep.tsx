import { useState } from 'react'
import { C, DISPLAY } from '../../theme/tokens'
import { SECTOR_OPTS, isProSector } from '../../data/options'
import OnboardShell from '../../components/layout/OnboardShell'
import StepBar from '../../components/layout/StepBar'
import { BigCta, GhostBtn } from '../../components/ui/Buttons'
import type { Sector } from '../../types/portfolio'

interface Props {
  onNext: (s: Sector) => void
  onBack: () => void
  isPro: boolean
  onLocked: () => void   // opens the Pro paywall
}

export default function SectorStep({ onNext, onBack, isPro, onLocked }: Props) {
  const [sel, setSel] = useState<Sector | null>(null)
  const selColor = SECTOR_OPTS.find(o => o.v === sel)?.color ?? C.cyan
  return (
    <OnboardShell>
      <StepBar step={3} />
      <div className="text-center mb-8">
        <h1 className="leading-tight mb-3 fade-up" style={{ fontFamily: DISPLAY, color: C.text, fontSize: 'clamp(2.2rem, 5.5vw, 3.2rem)' }}>
          Which area interests you?
        </h1>
        <p className="text-lg font-semibold fade-up d1" style={{ color: C.text2 }}>Investing in industries you understand makes your portfolio easier to follow.</p>
      </div>

      <div className="flex flex-col gap-3" role="radiogroup" aria-label="Sector">
        {SECTOR_OPTS.map((opt, i) => {
          const locked = isProSector(opt.v) && !isPro
          const on = sel === opt.v
          return (
            <button key={opt.v} role="radio" aria-checked={on} data-active={on}
              onClick={() => (locked ? onLocked() : setSel(opt.v))}
              className={`fill-hover glass w-full text-left rounded-2xl px-6 py-5 flex items-center gap-5 fade-up d${Math.min(i + 2, 8)}`}
              style={{ ['--fill' as string]: opt.color, border: `2px solid ${C.border}` }}>
              <span className="on-fill-bar w-3 self-stretch rounded-full flex-shrink-0" style={{ backgroundColor: opt.color }} aria-hidden />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="text-xl font-bold" style={{ color: C.text }}>{opt.v}</span>
                  {isProSector(opt.v) && (
                    <span className="on-fill-bg inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full"
                      style={{ color: C.pink, backgroundColor: `${C.pink}22`, border: `1px solid ${C.pink}55` }}>
                      <svg width="10" height="11" viewBox="0 0 12 14" fill="none" aria-hidden><rect x="2" y="5" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.6" /><path d="M4 5V4a2 2 0 014 0v1" stroke="currentColor" strokeWidth="1.6" /></svg>
                      {isPro ? 'Pro' : 'Pro only'}
                    </span>
                  )}
                </div>
                <p className="text-base font-medium leading-relaxed" style={{ color: C.text2 }}>{opt.desc}</p>
                <div className="text-sm font-bold mt-1.5" style={{ color: C.muted }}>e.g. {opt.eg}</div>
              </div>
              {locked
                ? <span className="text-sm font-bold flex-shrink-0 hidden sm:block" style={{ color: C.pink }}>Unlock →</span>
                : <span className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold"
                    style={{ border: `2px solid ${on ? C.canvas : C.border}`, color: C.canvas }}>{on ? '✓' : ''}</span>}
            </button>
          )
        })}
      </div>

      <div className="flex flex-col-reverse sm:flex-row items-center justify-center gap-3 mt-10 fade-up d7">
        <GhostBtn onClick={onBack}>← Back</GhostBtn>
        <BigCta onClick={() => sel && onNext(sel)} disabled={!sel} color={selColor}>
          {sel ? 'Generate my portfolio ✦' : 'Choose a sector'}
        </BigCta>
      </div>
    </OnboardShell>
  )
}
