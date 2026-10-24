import { C } from '../../theme/tokens'
import { fmt } from '../../utils/format'

export default function HistChart({ historical }: { historical: { month: string; value: number }[] }) {
  const W = 560, H = 160, PL = 70, PB = 30, PR = 16, PT = 12
  const vals = historical.map(m => m.value)
  const min = Math.min(...vals) * 0.97, max = Math.max(...vals) * 1.02, rng = max - min || 1
  const x = (i: number) => PL + (i / (vals.length - 1)) * (W - PL - PR)
  const y = (v: number) => PT + ((max - v) / rng) * (H - PT - PB)
  const linePts = vals.map((v, i) => `${x(i)},${y(v)}`).join(' ')
  const areaD = `M ${x(0)},${H - PB} ${vals.map((v, i) => `L ${x(i)},${y(v)}`).join(' ')} L ${x(vals.length - 1)},${H - PB} Z`
  const ticks = [0.2, 0.5, 0.8].map(p => min + rng * p)
  const lineColor = vals[vals.length - 1] >= vals[0] ? C.cyan : C.pink
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
      <defs>
        <linearGradient id="hg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={lineColor} stopOpacity="0.18" /><stop offset="100%" stopColor={lineColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={PL} y1={y(t)} x2={W - PR} y2={y(t)} stroke={C.border} strokeWidth="1" />
          <text x={PL - 6} y={y(t) + 4} textAnchor="end" fontSize="10" fill={C.muted} fontFamily="inherit">{fmt(t, true)}</text>
        </g>
      ))}
      <path d={areaD} fill="url(#hg)" />
      <polyline points={linePts} fill="none" stroke={lineColor} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      {historical.map((m, i) => i % 2 === 0 && (
        <text key={i} x={x(i)} y={H - 8} textAnchor="middle" fontSize="10" fill={C.muted} fontFamily="inherit">{m.month}</text>
      ))}
      <circle cx={x(vals.length - 1)} cy={y(vals[vals.length - 1])} r="4" fill={lineColor} />
    </svg>
  )
}
