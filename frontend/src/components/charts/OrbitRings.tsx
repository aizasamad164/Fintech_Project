import { useEffect, useState } from 'react'
import { ORBIT_COLORS, C } from '../../theme/tokens'
import type { PortfolioStock } from '../../types/portfolio'

// Rings only — no text on or near the rings. Labels live in <AllocationLegend />.
export default function OrbitRings({ stocks, animate }: { stocks: PortfolioStock[]; animate: boolean }) {
  const [revealed, setRevealed] = useState(false)
  useEffect(() => {
    if (animate) { const t = setTimeout(() => setRevealed(true), 200); return () => clearTimeout(t) }
  }, [animate])
  const SIZE = 260, cx = SIZE / 2, cy = SIZE / 2, SW = 9
  const RADII = [118, 99, 80, 61, 42, 23]
  return (
    <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="w-full max-w-[260px]" role="img"
      aria-label={`Allocation: ${stocks.map(s => `${s.ticker} ${s.allocation}%`).join(', ')}`}>
      <circle cx={cx} cy={cy} r="3" fill={C.muted} opacity={0.5} />
      {stocks.map((s, i) => {
        const R = RADII[i] ?? RADII[RADII.length - 1], circ = 2 * Math.PI * R
        const arcLen = Math.max((s.allocation / 100) * circ, 4)
        return (
          <g key={s.ticker}>
            <circle cx={cx} cy={cy} r={R} fill="none" stroke={C.border} strokeWidth={SW} opacity={0.6} />
            <circle cx={cx} cy={cy} r={R} fill="none" stroke={ORBIT_COLORS[i % ORBIT_COLORS.length]}
              strokeWidth={SW} strokeLinecap="round"
              strokeDasharray={`${arcLen} ${circ - arcLen}`} strokeDashoffset={revealed ? 0 : arcLen}
              transform={`rotate(-90 ${cx} ${cy})`} className="orbit-arc" style={{ transitionDelay: `${i * 0.12}s` }} />
          </g>
        )
      })}
    </svg>
  )
}
