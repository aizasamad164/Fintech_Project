import { C } from '../../theme/tokens'
import type { ModelScope, PortfolioOptions } from '../../types/portfolio'

const MODELS: { v: ModelScope; label: string; hint: string }[] = [
  { v: 'sector', label: 'Sector models', hint: 'A specialised model for each sector.' },
  { v: 'global', label: 'Global model', hint: 'One model that compares stocks from every sector together.' },
]

const label = { color: C.muted, letterSpacing: '0.05em' }

/** Two optional choices shared by onboarding and the Adjust panel:
 *  which model family scores the stocks, and the Shariah-compliant-only filter. */
export default function ModelOptions({ value, onChange }: { value: PortfolioOptions; onChange: (o: PortfolioOptions) => void }) {
  const hint = MODELS.find(m => m.v === value.model)?.hint
  return (
    <div className="space-y-5">
      <div>
        <div className="text-xs font-semibold mb-2" style={label}>PREDICTION MODEL</div>
        <div className="flex rounded-lg overflow-hidden" style={{ border: `1px solid ${C.border}` }}>
          {MODELS.map((m, i) => (
            <button key={m.v} onClick={() => onChange({ ...value, model: m.v })} className="flex-1 py-2 text-xs font-medium transition-all"
              style={{ backgroundColor: value.model === m.v ? C.cyan : 'transparent', color: value.model === m.v ? C.canvas : C.muted,
                       fontWeight: value.model === m.v ? 700 : 400, borderRight: i < MODELS.length - 1 ? `1px solid ${C.border}` : 'none' }}>
              {m.label}
            </button>
          ))}
        </div>
        <p className="text-[11px] mt-1.5" style={{ color: C.muted }}>{hint}</p>
      </div>

      <div>
        <div className="text-xs font-semibold mb-2" style={label}>SHARIAH</div>
        <button onClick={() => onChange({ ...value, shariah: !value.shariah })} aria-pressed={value.shariah}
          className="w-full flex items-center gap-3 text-left px-3 py-2.5 rounded-lg transition-all"
          style={{ border: `1px solid ${value.shariah ? C.teal : C.border}`, backgroundColor: value.shariah ? `${C.teal}12` : 'transparent' }}>
          <span className="w-4 h-4 rounded flex-shrink-0 flex items-center justify-center text-[10px] font-bold"
            style={{ backgroundColor: value.shariah ? C.teal : 'transparent', border: `1px solid ${value.shariah ? C.teal : C.border}`, color: C.canvas }}>
            {value.shariah ? '✓' : ''}
          </span>
          <span>
            <span className="block text-xs font-semibold" style={{ color: C.text }}>Shariah-compliant stocks only</span>
            <span className="block text-[11px]" style={{ color: C.muted }}>Optional. Uses third-party screening, not a religious ruling.</span>
          </span>
        </button>
      </div>
    </div>
  )
}
