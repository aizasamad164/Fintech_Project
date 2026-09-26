import { useEffect, useState } from 'react'
import { ORBIT_COLORS, C } from '../../theme/tokens'
import type { PortfolioStock } from '../../types/portfolio'

export default function OrbitRings({ stocks, animate }: { stocks: PortfolioStock[]; animate: boolean }) {
  const [revealed, setRevealed] = useState(false)
  useEffect(() => {
    if (animate) { const t = setTimeout(() => setRevealed(true), 200); return () => clearTimeout(t) }
  }, [animate])
  const SIZE = 260, cx = SIZE / 2, cy = SIZE / 2, RADII = [114, 93, 72, 53, 36], SW = 9
  return (
    <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="w-full max-w-[280px] mx-auto">
      <circle cx={cx} cy={cy} r="4" fill={C.muted} opacity={0.5} />
      {stocks.map((s, i) => {
        const R = RADII[i] || RADII[RADII.length - 1], circ = 2 * Math.PI * R
        const arcLen = Math.max((s.allocation / 100) * circ, 4), gap = circ - arcLen
        const color = ORBIT_COLORS[i % ORBIT_COLORS.length]
        return (
          <g key={s.ticker}>
            <circle cx={cx} cy={cy} r={R} fill="none" stroke={C.border} strokeWidth={SW} />
            <circle cx={cx} cy={cy} r={R} fill="none" stroke={color}
              strokeWidth={SW} strokeLinecap="round"
              strokeDasharray={`${arcLen} ${gap}`} strokeDashoffset={revealed ? 0 : arcLen}
              transform={`rotate(-90 ${cx} ${cy})`} className="orbit-arc" style={{ transitionDelay: `${i * 0.12}s` }} />
            {revealed && (
              <text x={cx + (R + SW) * Math.cos(-Math.PI / 2 + (s.allocation / 100) * Math.PI)}
                y={cy + (R + SW) * Math.sin(-Math.PI / 2 + (s.allocation / 100) * Math.PI)}
                textAnchor="middle" dominantBaseline="middle" fontSize="9"
                fill={color} fontFamily="Inter" fontWeight="600" opacity="0.85">
                {s.ticker}
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}
