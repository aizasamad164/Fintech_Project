import { C } from '../../theme/tokens'

export default function StepBar({ step }: { step: 1 | 2 | 3 }) {
  const labels = ['Budget', 'Strategy', 'Sector']
  return (
    <div className="flex items-center justify-center gap-3 mb-9" aria-label={`Step ${step} of 3`}>
      {labels.map((l, i) => {
        const n = i + 1, done = n < step, active = n === step
        return (
          <div key={l} className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-semibold transition-all"
                style={{ backgroundColor: done ? C.cyan : active ? C.pink : 'transparent', border: done || active ? 'none' : `1px solid ${C.border}`,
                  color: done || active ? C.canvas : C.muted, boxShadow: active ? `0 0 14px ${C.pink}70` : 'none' }}>
                {done ? '✓' : n}
              </div>
              <span className="text-xs font-semibold uppercase hidden sm:block" style={{ color: active ? C.text : C.muted, letterSpacing: '0.1em' }}>{l}</span>
            </div>
            {n < 3 && <div className="w-10 h-px" style={{ backgroundColor: n < step ? C.cyan : C.border }} />}
          </div>
        )
      })}
    </div>
  )
}
