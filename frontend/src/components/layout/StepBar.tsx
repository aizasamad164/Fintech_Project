import { C } from '../../theme/tokens'

export default function StepBar({ step }: { step: 1 | 2 | 3 }) {
  const labels = ['Budget', 'Strategy', 'Sector']
  return (
    <div className="flex items-center gap-2 mb-10">
      {labels.map((l, i) => {
        const n = i + 1, done = n < step, active = n === step
        return (
          <div key={l} className="flex items-center gap-2">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all"
                style={{ backgroundColor: done ? C.cyan : active ? C.violet : 'transparent', border: done || active ? 'none' : `1px solid ${C.border}`, color: done || active ? C.canvas : C.muted, fontFamily: 'Inter' }}>
                {done ? '✓' : n}
              </div>
              <span className="text-sm hidden sm:block" style={{ color: active ? C.text : C.muted, fontFamily: 'Inter', fontWeight: active ? 500 : 400 }}>{l}</span>
            </div>
            {n < 3 && <div className="w-8 h-px" style={{ backgroundColor: n < step ? C.cyan : C.border }} />}
          </div>
        )
      })}
    </div>
  )
}
