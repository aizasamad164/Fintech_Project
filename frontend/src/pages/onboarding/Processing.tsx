import { useEffect, useRef, useState } from 'react'
import { C, DISPLAY, ORBIT_COLORS } from '../../theme/tokens'
import LiveBackdrop from '../../components/effects/LiveBackdrop'

const PROC_STEPS = ['Fetching market data', 'Scoring candidates', 'Optimizing allocation', 'Writing your explanation']
const RADII = [130, 104, 80, 56]
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
    <div className="relative min-h-screen flex items-center justify-center px-5" style={{ backgroundColor: C.canvas }}>
      <LiveBackdrop />
      <div className="relative flex flex-col items-center text-center w-full max-w-md" style={{ zIndex: 1 }} role="status" aria-live="polite">
        {/* Radar */}
        <div className="relative mb-10 radar-glow">
          <div className="absolute inset-6 rounded-full" style={{ background: `radial-gradient(circle, ${C.cyan}22 0%, transparent 70%)` }} aria-hidden />
          <svg viewBox="0 0 300 300" className="relative w-[260px] h-[260px] sm:w-[300px] sm:h-[300px]" aria-hidden>
            <defs>
              <filter id="ring-glow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="5" result="b" />
                <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
              </filter>
              <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor={C.cyan} stopOpacity="0" />
                <stop offset="100%" stopColor={C.cyan} stopOpacity="0.35" />
              </linearGradient>
            </defs>
            {/* rotating radar sweep */}
            <g className="orbit-fast" style={{ transformOrigin: '150px 150px', animationDuration: '3s' }}>
              <path d="M150 150 L150 12 A138 138 0 0 1 270 82 Z" fill="url(#sweep)" />
            </g>
            {RADII.map((R, i) => {
              const circ = 2 * Math.PI * R
              const on = active >= i
              return (
                <g key={i}>
                  <circle cx={150} cy={150} r={R} fill="none" stroke={C.border} strokeWidth="9" opacity={0.6} />
                  <circle cx={150} cy={150} r={R} fill="none" strokeWidth="9" strokeLinecap="round" filter="url(#ring-glow)"
                    stroke={ORBIT_COLORS[i]} strokeDasharray={circ} strokeDashoffset={on ? 0 : circ}
                    transform="rotate(-90 150 150)"
                    style={{ transition: `stroke-dashoffset ${SWEEP_MS}ms cubic-bezier(0.65, 0, 0.35, 1)` }} />
                </g>
              )
            })}
            <circle cx={150} cy={150} r="6" fill={C.pink} className="breathe" filter="url(#ring-glow)" />
          </svg>
        </div>

        <div className="text-3xl sm:text-4xl mb-8" style={{ fontFamily: DISPLAY, color: C.text }}>Building your portfolio…</div>

        <div className="glass rounded-2xl px-6 py-5 w-full space-y-4 text-left" style={{ border: `1px solid ${C.border}` }}>
          {PROC_STEPS.map((s, i) => {
            const done = i <= active
            return (
              <div key={s} className="flex items-center gap-3 transition-all duration-500" style={{ opacity: done ? 1 : i === active + 1 ? 0.65 : 0.35 }}>
                <div className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center transition-all"
                  style={{ backgroundColor: done ? ORBIT_COLORS[i] : C.border, boxShadow: done ? `0 0 14px ${ORBIT_COLORS[i]}` : 'none' }}>
                  {done && <span className="text-xs font-bold check-pop" style={{ color: C.canvas }}>✓</span>}
                </div>
                <span className="text-base font-bold" style={{ color: done ? C.text : C.text2 }}>{s}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
