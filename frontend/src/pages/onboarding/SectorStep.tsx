import { useState } from 'react'
import { C, HEADING } from '../../theme/tokens'
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

const Lock = () => (
  <svg width="10" height="11" viewBox="0 0 12 14" fill="none" aria-hidden><rect x="2" y="5" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.6" /><path d="M4 5V4a2 2 0 014 0v1" stroke="currentColor" strokeWidth="1.6" /></svg>
)

export default function SectorStep({ onNext, onBack, isPro, onLocked }: Props) {
  const [sel, setSel] = useState<Sector | null>(null)
  const selColor = SECTOR_OPTS.find(o => o.v === sel)?.color ?? C.cyan
  return (
    <OnboardShell>
      <StepBar step={3} />
      <div className="text-center mb-8">
        <h1 className="text-3xl sm:text-4xl font-semibold mb-3 fade-up" style={{ fontFamily: HEADING, color: C.text, letterSpacing: '-0.025em' }}>
          Which area interests you?
        </h1>
        <p className="text-base font-medium fade-up d1" style={{ color: C.muted }}>Investing in industries you understand makes your portfolio easier to follow.</p>
      </div>

      <div className="flex flex-col gap-3" role="radiogroup" aria-label="Sector">
        {SECTOR_OPTS.map((opt, i) => {
          const locked = isProSector(opt.v) && !isPro
          const on = sel === opt.v
          return (
            <button key={opt.v} role="radio" aria-checked={on} data-active={on}
              onClick={() => (locked ? onLocked() : setSel(opt.v))}
              className={`tint-fill glass w-full text-left rounded-xl px-5 sm:px-6 py-4 flex items-center gap-5 fade-up d${Math.min(i + 2, 8)}`}
              style={{ ['--fill' as string]: opt.color, border: `1px solid ${C.border}` }}>
              <span className="w-1 self-stretch rounded-full flex-shrink-0" style={{ backgroundColor: opt.color }} aria-hidden />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2.5 mb-0.5 flex-wrap">
                  <span className="text-lg font-semibold" style={{ fontFamily: HEADING, color: C.text, letterSpacing: '-0.01em' }}>{opt.v}</span>
                  {isProSector(opt.v) && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase px-2 py-0.5 rounded"
                      style={{ color: C.pink, backgroundColor: `${C.pink}1a`, border: `1px solid ${C.pink}55`, letterSpacing: '0.1em' }}>
                      <Lock /> Pro
                    </span>
                  )}
                </div>
                <p className="text-sm font-medium leading-relaxed" style={{ color: C.text2 }}>{opt.desc}</p>
                <div className="text-xs font-semibold mt-1" style={{ color: C.muted, letterSpacing: '0.03em' }}>{opt.eg}</div>
              </div>
              {locked
                ? <span className="text-xs font-semibold uppercase flex-shrink-0 hidden sm:block" style={{ color: C.pink, letterSpacing: '0.1em' }}>Unlock</span>
                : <span className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold"
                    style={{ border: `1.5px solid ${on ? opt.color : C.border}`, backgroundColor: on ? opt.color : 'transparent', color: C.canvas }}>{on ? '✓' : ''}</span>}
            </button>
          )
        })}
      </div>

      <div className="flex flex-col-reverse sm:flex-row items-center justify-center gap-3 mt-9 fade-up d7">
        <GhostBtn onClick={onBack}>Back</GhostBtn>
        <BigCta onClick={() => sel && onNext(sel)} disabled={!sel} color={selColor}>
          {sel ? 'Generate my portfolio' : 'Choose a sector'}
        </BigCta>
      </div>
    </OnboardShell>
  )
}
