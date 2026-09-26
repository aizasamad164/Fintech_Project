import type { ReactNode } from 'react'
import { C, ORBIT_COLORS } from '../../theme/tokens'

export default function LessonThumb({ id }: { id: number }) {
  const W = 64, H = 40
  const bars = [24, 32, 16, 28, 20]
  const graphs: Record<number, ReactNode> = {
    0: <><polyline points="0,36 12,28 24,20 32,24 44,12 56,6 64,4" fill="none" stroke={C.cyan} strokeWidth="2" strokeLinecap="round" /><line x1="20" y1="0" x2="20" y2="40" stroke={C.border} strokeWidth="1" strokeDasharray="3 3" /></>,
    1: <><polyline points="0,30 12,20 24,28 36,16 48,24 64,10" fill="none" stroke={C.teal} strokeWidth="1.5" strokeLinecap="round" /><polyline points="0,36 12,32 24,34 36,28 48,30 64,22" fill="none" stroke={C.violet} strokeWidth="1.5" strokeLinecap="round" /><polyline points="0,24 12,18 24,22 36,14 48,18 64,8" fill="none" stroke={C.muted} strokeWidth="1" strokeLinecap="round" opacity="0.5" /></>,
    2: <><polyline points="0,38 16,34 32,30 48,26 64,22" fill="none" stroke={C.teal} strokeWidth="2" /><polyline points="0,36 16,28 32,20 48,12 64,6" fill="none" stroke={C.cyan} strokeWidth="2" /><polyline points="0,34 16,22 32,10 48,6 64,2" fill="none" stroke={C.amber} strokeWidth="2" /></>,
    3: <>{bars.map((h, i) => <rect key={i} x={i * 14 + 2} y={40 - h} width="10" height={h} fill={ORBIT_COLORS[i % ORBIT_COLORS.length]} rx="2" opacity="0.8" />)}</>,
    4: <><polyline points="0,20 8,32 16,8 24,36 32,4 40,30 48,12 56,28 64,16" fill="none" stroke={C.amber} strokeWidth="2" strokeLinecap="round" /><polyline points="0,24 16,22 32,20 48,22 64,20" fill="none" stroke={C.teal} strokeWidth="1.5" strokeDasharray="4 2" /></>,
    5: <><rect x="0" y="10" width="28" height="30" fill={`${C.cyan}30`} rx="3" /><rect x="32" y="6" width="32" height="34" fill={`${C.violet}30`} rx="3" /><text x="8" y="32" fontSize="8" fill={C.cyan} fontFamily="Inter">45%</text><text x="36" y="28" fontSize="8" fill={C.violet} fontFamily="Inter">55%</text></>,
  }
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} style={{ flexShrink: 0 }}>
      {graphs[id] ?? graphs[0]}
    </svg>
  )
}
