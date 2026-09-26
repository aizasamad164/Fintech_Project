import { C } from '../../theme/tokens'

type Ann = { x: number; y: number; label: string; side: 'top' | 'bottom' }

export default function LessonHeroGraph({ id }: { id: number }) {
  const W = 520, H = 180, PL = 40, PB = 30, PT = 20, PR = 20
  const b = H - PB
  const configs: Record<number, { pts: string; annotations: Ann[]; color: string }> = {
    0: { color: C.cyan, pts: `${PL},${b - 20} ${PL + 60},${b - 50} ${PL + 120},${b - 40} ${PL + 180},${b - 80} ${PL + 240},${b - 70} ${PL + 300},${b - 120} ${PL + 360},${b - 110} ${W - PR},${b - 145}`,
      annotations: [{ x: PL + 120, y: b - 55, label: 'Support', side: 'bottom' }, { x: PL + 240, y: b - 85, label: 'Breakout', side: 'top' }, { x: PL + 360, y: b - 125, label: 'Uptrend', side: 'top' }] },
    1: { color: C.teal, pts: `${PL},${b - 60} ${PL + 80},${b - 80} ${PL + 160},${b - 50} ${PL + 240},${b - 90} ${PL + 320},${b - 70} ${W - PR},${b - 100}`,
      annotations: [{ x: PL + 80, y: b - 95, label: 'Diversified peak', side: 'top' }, { x: PL + 240, y: b - 105, label: 'Smoother curve', side: 'top' }] },
    2: { color: C.violet, pts: `${PL},${b - 90} ${PL + 90},${b - 80} ${PL + 180},${b - 70} ${PL + 270},${b - 60} ${W - PR},${b - 50}`,
      annotations: [{ x: PL + 90, y: b - 95, label: 'Conservative', side: 'top' }, { x: PL + 270, y: b - 75, label: 'Balanced', side: 'bottom' }] },
    3: { color: C.pink, pts: `${PL},${b - 40} ${PL + 80},${b - 80} ${PL + 160},${b - 60} ${PL + 240},${b - 110} ${W - PR},${b - 130}`,
      annotations: [{ x: PL + 80, y: b - 95, label: 'High P/E', side: 'top' }, { x: PL + 240, y: b - 125, label: 'Growth priced in', side: 'top' }] },
    4: { color: C.pink, pts: `${PL},${b - 90} ${PL + 60},${b - 130} ${PL + 120},${b - 40} ${PL + 180},${b - 150} ${PL + 240},${b - 30} ${PL + 300},${b - 120} ${W - PR},${b - 100}`,
      annotations: [{ x: PL + 60, y: b - 145, label: 'High volatility', side: 'top' }, { x: PL + 180, y: b - 165, label: 'Peak swing', side: 'top' }] },
    5: { color: C.cyan, pts: `${PL},${b - 80} ${PL + 80},${b - 100} ${PL + 160},${b - 90} ${PL + 240},${b - 120} ${W - PR},${b - 110}`,
      annotations: [{ x: PL + 160, y: b - 105, label: 'Rebalance point', side: 'top' }, { x: PL + 80, y: b - 115, label: 'Drift', side: 'bottom' }] },
  }
  const cfg = configs[id] ?? configs[0]
  const ptsArr = cfg.pts.split(' ').map(p => { const [xx, yy] = p.split(','); return { x: parseFloat(xx), y: parseFloat(yy) } })
  const areaD = `M ${ptsArr[0].x},${b} ${ptsArr.map(p => `L ${p.x},${p.y}`).join(' ')} L ${ptsArr[ptsArr.length - 1].x},${b} Z`
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
      <defs>
        <linearGradient id="lg2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={cfg.color} stopOpacity="0.2" /><stop offset="100%" stopColor={cfg.color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <line x1={PL} y1={PT} x2={PL} y2={b} stroke={C.border} strokeWidth="1" />
      <line x1={PL} y1={b} x2={W - PR} y2={b} stroke={C.border} strokeWidth="1" />
      <path d={areaD} fill="url(#lg2)" />
      <polyline points={cfg.pts} fill="none" stroke={cfg.color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      {cfg.annotations.map((ann, i) => (
        <g key={i}>
          <line x1={ann.x} y1={ann.side === 'top' ? ann.y - 10 : ann.y + 2} x2={ann.x} y2={ann.side === 'top' ? ann.y - 22 : ann.y + 14}
            stroke={cfg.color} strokeWidth="1" strokeDasharray="3 2" opacity="0.6" />
          <rect x={ann.x - 36} y={ann.side === 'top' ? ann.y - 36 : ann.y + 14} width="72" height="16" rx="3" fill={`${cfg.color}20`} />
          <text x={ann.x} y={ann.side === 'top' ? ann.y - 25 : ann.y + 25} textAnchor="middle" fontSize="9" fill={cfg.color} fontFamily="inherit" fontWeight="600">{ann.label}</text>
        </g>
      ))}
      {ptsArr.map((p, i) => i % 2 === 0 && <circle key={i} cx={p.x} cy={p.y} r="2.5" fill={cfg.color} opacity="0.7" />)}
    </svg>
  )
}
