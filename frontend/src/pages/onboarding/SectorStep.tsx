import { useState } from 'react'
import { C } from '../../theme/tokens'
import { SECTOR_OPTS } from '../../data/options'
import OnboardShell from '../../components/layout/OnboardShell'
import StepBar from '../../components/layout/StepBar'
import { CyanBtn, GhostBtn } from '../../components/ui/Buttons'
import type { Sector } from '../../types/portfolio'

export default function SectorStep({ onNext, onBack }: { onNext: (s: Sector) => void; onBack: () => void }) {
  const [sel, setSel] = useState<Sector | null>(null)
  return (
    <OnboardShell>
      <StepBar step={3} />
      <h1 className="text-3xl sm:text-4xl mb-3 leading-snug fade-up" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>Which area interests you?</h1>
      <p className="text-sm mb-8 fade-up d1 leading-relaxed" style={{ color: C.muted, maxWidth: 420 }}>Investing in industries you understand makes your portfolio easier to follow.</p>
      <div className="grid sm:grid-cols-2 gap-3 mb-8">
        {SECTOR_OPTS.map((opt, i) => (
          <button key={opt.v} onClick={() => setSel(opt.v)} className={`text-left p-4 rounded-xl transition-all relative fade-up d${i + 1}`}
            style={{ border: `2px solid ${sel === opt.v ? C.cyan : C.border}`, backgroundColor: sel === opt.v ? `${C.cyan}10` : C.surface }}>
            {sel === opt.v && <div className="absolute top-3 right-3 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold check-pop" style={{ backgroundColor: C.cyan, color: C.canvas }}>✓</div>}
            <div className="text-sm font-semibold mb-1" style={{ color: C.text }}>{opt.v}</div>
            <p className="text-xs leading-relaxed mb-2" style={{ color: C.text2 }}>{opt.desc}</p>
            <div className="text-[10px] font-semibold" style={{ color: C.muted, letterSpacing: '0.02em' }}>{opt.eg}</div>
          </button>
        ))}
      </div>
      <div className="flex gap-3 fade-up d5">
        <GhostBtn onClick={onBack}>Back</GhostBtn>
        <CyanBtn onClick={() => sel && onNext(sel)} disabled={!sel}>Generate portfolio</CyanBtn>
      </div>
    </OnboardShell>
  )
}
