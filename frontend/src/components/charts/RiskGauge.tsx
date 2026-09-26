import { useEffect, useState } from 'react'
import { C } from '../../theme/tokens'

export default function RiskGauge({ rating, animate }: { rating: number; animate: boolean }) {
  const [settled, setSettled] = useState(false)
  useEffect(() => {
    if (animate) { const t = setTimeout(() => setSettled(true), 500); return () => clearTimeout(t) }
  }, [animate])
  const W = 240, H = 130, cx = W / 2, cy = H - 12, R = 88, NL = 68
  const finalAngle = Math.PI * (1 - (rating - 1) / 4)
  const needleAngle = settled ? finalAngle : Math.PI
  const nx = cx + NL * Math.cos(needleAngle), ny = cy - NL * Math.sin(needleAngle)
  const pt = (a: number) => ({ x: cx + R * Math.cos(a), y: cy - R * Math.sin(a) })
  const a0 = pt(Math.PI), a1 = pt(2 * Math.PI / 3), a2 = pt(Math.PI / 3), a3 = pt(0)
  const arc = (p: typeof a0, q: typeof a0) => `M ${p.x} ${p.y} A ${R} ${R} 0 0 0 ${q.x} ${q.y}`
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[240px]">
      <path d={`M ${a0.x} ${a0.y} A ${R} ${R} 0 0 0 ${a3.x} ${a3.y}`} fill="none" stroke={C.border} strokeWidth="10" strokeLinecap="round" />
      <path d={arc(a0, a1)} fill="none" stroke={C.teal} strokeWidth="10" strokeLinecap="round" />
      <path d={arc(a1, a2)} fill="none" stroke={C.cyan} strokeWidth="10" />
      <path d={arc(a2, a3)} fill="none" stroke={C.amber} strokeWidth="10" strokeLinecap="round" />
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={C.text} strokeWidth="2.5" strokeLinecap="round"
        style={{ transition: settled ? 'all 1.2s cubic-bezier(0.34,1.56,0.64,1)' : 'none' }} />
      <circle cx={cx} cy={cy} r="7" fill={C.card} stroke={C.border} strokeWidth="2" />
      <circle cx={cx} cy={cy} r="3" fill={C.text2} />
      <text x={a0.x - 4} y={cy + 16} textAnchor="end" fontSize="9" fill={C.muted} fontFamily="Inter">Low</text>
      <text x={cx} y={cy - R - 8} textAnchor="middle" fontSize="9" fill={C.muted} fontFamily="Inter">Moderate</text>
      <text x={a3.x + 4} y={cy + 16} textAnchor="start" fontSize="9" fill={C.muted} fontFamily="Inter">Elevated</text>
    </svg>
  )
}
