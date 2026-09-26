import { useEffect, useRef, useState } from 'react'
import { C, ORBIT_COLORS } from '../../theme/tokens'

const PROC_STEPS = ['Fetching market data', 'Scoring candidates', 'Optimizing allocation', 'Writing your explanation']
const RADII = [80, 62, 46, 32]
const STEP_MS = 800   // gap between each ring starting
const SWEEP_MS = 900  // time for one ring to draw a full 360°
const HOLD_MS = 450   // pause on the completed instrument before leaving

export default function Processing({ onDone }: { onDone: () => void }) {
  const [active, setActive] = useState(-1)
  const doneRef = useRef(onDone)
  doneRef.current = onDone
  useEffect(() => {
    const timers = PROC_STEPS.map((_, i) => setTimeout(() => setActive(i), 100 + i * STEP_MS))
    // Leave only after the LAST ring has finished its full sweep
    const lastStart = 100 + (PROC_STEPS.length - 1) * STEP_MS
    const done = setTimeout(() => doneRef.current(), lastStart + SWEEP_MS + HOLD_MS)
    return () => { timers.forEach(clearTimeout); clearTimeout(done) }
  }, [])
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-5" style={{ backgroundColor: C.canvas }}>
      <div className="w-full max-w-sm">
        <div className="mb-10 flex justify-center">
          <svg viewBox="0 0 200 200" width="200" height="200" aria-hidden>
            {RADII.map((R, i) => {
              const circ = 2 * Math.PI * R
              const on = active >= i
              return (
                <g key={i}>
                  <circle cx={100} cy={100} r={R} fill="none" stroke={C.border} strokeWidth="7" opacity={0.5} />
                  <circle cx={100} cy={100} r={R} fill="none" strokeWidth="7" strokeLinecap="round"
                    stroke={ORBIT_COLORS[i]} strokeDasharray={circ} strokeDashoffset={on ? 0 : circ}
                    transform="rotate(-90 100 100)"
                    style={{ transition: `stroke-dashoffset ${SWEEP_MS}ms cubic-bezier(0.65, 0, 0.35, 1)` }} />
                </g>
              )
            })}
            <circle cx={100} cy={100} r="3" fill={C.pink} className="breathe" />
          </svg>
        </div>
        <div className="text-xl mb-8 text-center" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>Building your portfolio…</div>
        <div className="space-y-4">
          {PROC_STEPS.map((s, i) => {
            const done = i <= active
            return (
              <div key={s} className="flex items-center gap-3 transition-all duration-500" style={{ opacity: done ? 1 : i === active + 1 ? 0.6 : 0.25 }}>
                <div className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center transition-all" style={{ backgroundColor: done ? ORBIT_COLORS[i] : C.border }}>
                  {done && <span className="text-[10px] font-bold check-pop" style={{ color: C.canvas }}>✓</span>}
                </div>
                <span className="text-sm" style={{ color: done ? C.text : C.text2, fontWeight: done ? 500 : 400 }}>{s}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
