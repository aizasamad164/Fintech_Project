import { C } from '../../theme/tokens'
import { fmt } from '../../utils/format'
import { RISKS, SECTORS } from '../../data/options'
import type { Risk, Sector } from '../../types/portfolio'

interface Props {
  risk: Risk; sector: Sector; budget: number
  onRisk: (r: Risk) => void; onSector: (s: Sector) => void; onBudget: (b: number) => void
  onClose: () => void
}

const label = { color: C.muted, fontFamily: 'Inter', letterSpacing: '0.05em' }

export default function AdjustPanel({ risk, sector, budget, onRisk, onSector, onBudget, onClose }: Props) {
  return (
    <div className="rounded-xl p-5 mt-3 fade-up" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
      <div className="flex items-center justify-between mb-5">
        <span className="text-sm font-semibold" style={{ color: C.text, fontFamily: 'Inter' }}>Adjust portfolio</span>
        <button onClick={onClose} className="text-xs px-2 py-1 rounded" style={{ color: C.muted, fontFamily: 'Inter' }}>Close ×</button>
      </div>
      <div className="space-y-5">
        <div>
          <div className="text-xs font-semibold mb-2" style={label}>BUDGET</div>
          <div className="flex gap-2 flex-wrap">
            {[1000, 5000, 10000, 25000, 50000].map(a => (
              <button key={a} onClick={() => onBudget(a)} className="px-3 py-1.5 text-xs rounded-lg transition-all"
                style={{ border: `1px solid ${budget === a ? C.violet : C.border}`, color: budget === a ? C.violet : C.muted, backgroundColor: budget === a ? `${C.violet}15` : 'transparent', fontFamily: 'Inter' }}>
                {fmt(a)}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-xs font-semibold mb-2" style={label}>RISK STRATEGY</div>
          <div className="flex rounded-lg overflow-hidden" style={{ border: `1px solid ${C.border}` }}>
            {RISKS.map((r, i) => (
              <button key={r} onClick={() => onRisk(r)} className="flex-1 py-2 text-xs font-medium transition-all"
                style={{ backgroundColor: risk === r ? C.cyan : 'transparent', color: risk === r ? C.canvas : C.muted, fontFamily: 'Inter', fontWeight: risk === r ? 700 : 400, borderRight: i < 2 ? `1px solid ${C.border}` : 'none' }}>
                {r}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-xs font-semibold mb-2" style={label}>SECTOR</div>
          <div className="flex flex-wrap gap-2">
            {SECTORS.map(s => (
              <button key={s} onClick={() => onSector(s)} className="px-3 py-1.5 text-xs rounded-lg transition-all"
                style={{ border: `1px solid ${sector === s ? C.cyan : C.border}`, color: sector === s ? C.cyan : C.muted, backgroundColor: sector === s ? `${C.cyan}15` : 'transparent', fontFamily: 'Inter', fontWeight: sector === s ? 600 : 400 }}>
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
