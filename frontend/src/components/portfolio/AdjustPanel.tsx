import { C, riskColor } from '../../theme/tokens'
import { fmt } from '../../utils/format'
import { RISKS, SECTOR_OPTS, isProSector } from '../../data/options'
import type { Risk, Sector } from '../../types/portfolio'

interface Props {
  risk: Risk; sector: Sector; budget: number
  isPro: boolean
  onRisk: (r: Risk) => void; onSector: (s: Sector) => void; onBudget: (b: number) => void
  onLocked: () => void
  onClose: () => void
}

const Label = ({ children }: { children: string }) => (
  <div className="text-sm font-semibold mb-2.5" style={{ color: C.text2 }}>{children}</div>
)

export default function AdjustPanel({ risk, sector, budget, isPro, onRisk, onSector, onBudget, onLocked, onClose }: Props) {
  return (
    <div className="glass rounded-2xl p-5 sm:p-6 mt-4 fade-up" style={{ border: `1px solid ${C.pink}66`, boxShadow: `0 20px 50px -24px ${C.pink}` }}>
      <div className="flex items-center justify-between mb-5">
        <span className="text-base font-semibold" style={{ color: C.text }}>Adjust your portfolio</span>
        <button onClick={onClose} className="pressable text-sm font-semibold px-3 py-1.5 rounded-lg" style={{ color: C.text2, border: `1px solid ${C.border}` }}>Done</button>
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div>
          <Label>Budget</Label>
          <div className="grid grid-cols-3 gap-2">
            {[1000, 2500, 5000, 10000, 25000, 50000].map(a => {
              const on = budget === a
              return (
                <button key={a} onClick={() => onBudget(a)} className="pressable py-2.5 text-sm font-semibold rounded-lg"
                  style={{ border: `1px solid ${on ? C.violet : C.border}`, color: on ? C.canvas : C.text, backgroundColor: on ? C.violet : 'transparent' }}>
                  {fmt(a)}
                </button>
              )
            })}
          </div>
        </div>
        <div>
          <Label>Risk strategy</Label>
          <div className="flex flex-col gap-2">
            {RISKS.map(r => {
              const on = risk === r, c = riskColor(r)
              return (
                <button key={r} onClick={() => onRisk(r)} className="pressable py-2.5 px-4 text-sm font-semibold rounded-lg text-left flex items-center gap-2"
                  style={{ border: `1px solid ${on ? c : C.border}`, color: on ? C.canvas : C.text, backgroundColor: on ? c : 'transparent' }}>
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: on ? C.canvas : c }} />{r}
                </button>
              )
            })}
          </div>
        </div>
        <div>
          <Label>Sector</Label>
          <div className="flex flex-col gap-2">
            {SECTOR_OPTS.map(o => {
              const on = sector === o.v
              const locked = isProSector(o.v) && !isPro
              return (
                <button key={o.v} onClick={() => (locked ? onLocked() : onSector(o.v))}
                  className="pressable py-2.5 px-4 text-sm font-semibold rounded-lg text-left flex items-center justify-between gap-2"
                  style={{ border: `1px solid ${on ? o.color : C.border}`, color: on ? C.canvas : C.text, backgroundColor: on ? o.color : 'transparent' }}>
                  {o.v}
                  {locked && <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded" style={{ color: C.pink, border: `1px solid ${C.pink}66`, letterSpacing: '0.1em' }}>PRO</span>}
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
