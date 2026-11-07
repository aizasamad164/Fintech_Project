import { C } from '../../theme/tokens'

export default function StepBar({ step }: { step: 1 | 2 | 3 }) {
  const labels = ['Budget', 'Strategy', 'Sector']
  return (
    <div className="flex items-center justify-center gap-3 mb-10">
      {labels.map((l, i) => {
        const n = i + 1, done = n < step, active = n === step
        return (
          <div key={l} className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all"
                style={{ backgroundColor: done ? C.cyan : active ? C.pink : 'transparent', border: done || active ? 'none' : `2px solid ${C.border}`,
                  color: done || active ? C.canvas : C.muted, boxShadow: active ? `0 0 18px ${C.pink}80` : 'none' }}>
                {done ? '✓' : n}
              </div>
              <span className="text-sm font-bold hidden sm:block" style={{ color: active ? C.text : C.muted }}>{l}</span>
            </div>
            {n < 3 && <div className="w-10 h-0.5 rounded-full" style={{ backgroundColor: n < step ? C.cyan : C.border }} />}
          </div>
        )
      })}
    </div>
  )
}
