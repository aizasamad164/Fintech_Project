import { useState } from 'react'
import { C } from '../../theme/tokens'
import { RISK_OPTS } from '../../data/options'
import OnboardShell from '../../components/layout/OnboardShell'
import StepBar from '../../components/layout/StepBar'
import { CyanBtn, GhostBtn } from '../../components/ui/Buttons'
import type { Risk } from '../../types/portfolio'

export default function RiskStep({ onNext, onBack }: { onNext: (r: Risk) => void; onBack: () => void }) {
  const [sel, setSel] = useState<Risk | null>(null)
  return (
    <OnboardShell>
      <StepBar step={2} />
      <h1 className="text-3xl sm:text-4xl mb-3 leading-snug fade-up" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>How do you want to approach risk?</h1>
      <p className="text-sm mb-8 fade-up d1 leading-relaxed" style={{ color: C.muted, maxWidth: 420 }}>This shapes which companies we include and how much weight each one gets.</p>
      <div className="grid sm:grid-cols-3 gap-3 mb-8">
        {RISK_OPTS.map((opt, i) => (
          <button key={opt.v} onClick={() => setSel(opt.v)} className={`text-left p-4 rounded-xl transition-all relative fade-up d${i + 1}`}
            style={{ border: `2px solid ${sel === opt.v ? opt.color : C.border}`, backgroundColor: sel === opt.v ? `${opt.color}12` : C.surface }}>
            {sel === opt.v && <div className="absolute top-3 right-3 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold check-pop" style={{ backgroundColor: opt.color, color: C.canvas }}>✓</div>}
            <div className="text-xs font-bold tracking-widest uppercase mb-1.5" style={{ color: opt.color }}>{opt.v}</div>
            <p className="text-xs leading-relaxed mb-3" style={{ color: C.text2 }}>{opt.desc}</p>
            <div className="text-xs font-semibold" style={{ color: opt.color }}>{opt.range}</div>
          </button>
        ))}
      </div>
      <div className="flex gap-3 fade-up d4">
        <GhostBtn onClick={onBack}>Back</GhostBtn>
        <CyanBtn onClick={() => sel && onNext(sel)} disabled={!sel}>Continue with {sel ?? '…'}</CyanBtn>
      </div>
    </OnboardShell>
  )
}
