import { useEffect, useRef, useState } from 'react'
import { C, ORBIT_COLORS } from '../../theme/tokens'

const PROC_STEPS = ['Fetching market data', 'Scoring candidates', 'Optimizing allocation', 'Writing your explanation']

export default function Processing({ onDone }: { onDone: () => void }) {
  const [active, setActive] = useState(-1)
  const doneRef = useRef(onDone)
  doneRef.current = onDone
  useEffect(() => {
    const timers = PROC_STEPS.map((_, i) => setTimeout(() => setActive(i), (i + 1) * 650))
    const done = setTimeout(() => doneRef.current(), PROC_STEPS.length * 650 + 700)
    return () => { timers.forEach(clearTimeout); clearTimeout(done) }
  }, [])
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-5" style={{ backgroundColor: C.canvas }}>
      <div className="w-full max-w-sm">
        <div className="mb-10 flex justify-center">
          <svg viewBox="0 0 200 200" width="200" height="200">
            {[80, 62, 46, 32].map((R, i) => (
              <circle key={i} cx={100} cy={100} r={R} fill="none" strokeWidth="7"
                strokeDasharray={`${active >= i ? 40 - i * 8 : 0} ${2 * Math.PI * R}`}
                transform="rotate(-90 100 100)"
                style={{ transition: 'stroke-dasharray 0.8s ease-out', stroke: active >= i ? ORBIT_COLORS[i] : C.border }} />
            ))}
            <circle cx={100} cy={100} r="3" fill={C.muted} opacity="0.4" />
          </svg>
        </div>
        <div className="text-xl mb-8 text-center" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>Building your portfolio…</div>
        <div className="space-y-4">
          {PROC_STEPS.map((s, i) => {
            const done = i <= active
            return (
              <div key={s} className="flex items-center gap-3 transition-all duration-500" style={{ opacity: done ? 1 : i === active + 1 ? 0.6 : 0.25 }}>
                <div className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center transition-all" style={{ backgroundColor: done ? C.cyan : C.border }}>
                  {done && <span className="text-[10px] font-bold check-pop" style={{ color: C.canvas }}>✓</span>}
                </div>
                <span className="text-sm" style={{ color: done ? C.text : C.text2, fontFamily: 'Inter', fontWeight: done ? 500 : 400 }}>{s}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
