import { C } from '../../theme/tokens'
import type { ModelScope, PortfolioOptions } from '../../types/portfolio'

const MODELS: { v: ModelScope; label: string; hint: string }[] = [
  { v: 'sector', label: 'Sector models', hint: 'A specialised model for each sector.' },
  { v: 'global', label: 'Global model', hint: 'One model that compares stocks from every sector together.' },
]

const Label = ({ children }: { children: string }) => (
  <div className="text-[11px] font-semibold uppercase mb-2" style={{ color: C.muted, letterSpacing: '0.1em' }}>{children}</div>
)

/** Two optional choices shared by onboarding and the Adjust panel:
 *  which model family scores the stocks, and the Shariah-compliant-only filter. */
export default function ModelOptions({ value, onChange }: { value: PortfolioOptions; onChange: (o: PortfolioOptions) => void }) {
  const hint = MODELS.find(m => m.v === value.model)?.hint
  return (
    <div className="grid gap-5 sm:grid-cols-2">
      <div>
        <Label>Prediction model</Label>
        <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Prediction model">
          {MODELS.map(m => {
            const on = value.model === m.v
            return (
              <button key={m.v} role="radio" aria-checked={on} onClick={() => onChange({ ...value, model: m.v })}
                className="pressable py-2.5 rounded-lg text-sm font-semibold"
                style={{ border: `1px solid ${on ? C.cyan : C.border}`, color: on ? C.text : C.text2, backgroundColor: on ? `${C.cyan}22` : 'rgba(10,16,27,0.55)' }}>
                {m.label}
              </button>
            )
          })}
        </div>
        <p className="text-xs font-medium mt-2" style={{ color: C.muted }}>{hint}</p>
      </div>

      <div>
        <Label>Shariah screening</Label>
        <button onClick={() => onChange({ ...value, shariah: !value.shariah })} role="switch" aria-checked={value.shariah}
          className="pressable w-full flex items-center gap-3 text-left px-3.5 py-2.5 rounded-lg"
          style={{ border: `1px solid ${value.shariah ? C.teal : C.border}`, backgroundColor: value.shariah ? `${C.teal}1c` : 'rgba(10,16,27,0.55)' }}>
          <span className="relative w-9 h-5 rounded-full flex-shrink-0 transition-colors" style={{ backgroundColor: value.shariah ? C.teal : C.border }} aria-hidden>
            <span className="absolute top-0.5 w-4 h-4 rounded-full transition-all" style={{ left: value.shariah ? 18 : 2, backgroundColor: C.text }} />
          </span>
          <span className="text-sm font-semibold" style={{ color: C.text }}>Shariah-compliant stocks only</span>
        </button>
        <p className="text-xs font-medium mt-2" style={{ color: C.muted }}>Optional. Uses third-party screening, not a religious ruling.</p>
      </div>
    </div>
  )
}
