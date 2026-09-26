import { C } from '../../theme/tokens'

export default function TrendSpark({ trend, up, W = 80, H = 28 }: { trend: number[]; up: boolean; W?: number; H?: number }) {
  const min = Math.min(...trend), max = Math.max(...trend), rng = max - min || 1
  const coords = trend.map((v, i) => ({ x: (i / (trend.length - 1)) * W, y: H - ((v - min) / rng) * H * 0.85 - H * 0.075 }))
  const pts = coords.map(p => `${p.x},${p.y}`).join(' ')
  const last = coords[coords.length - 1]
  const color = up ? C.teal : C.pink
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={last.x} cy={last.y} r="2.5" fill={color} />
    </svg>
  )
}
