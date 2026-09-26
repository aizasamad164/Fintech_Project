import { C, riskColor } from '../theme/tokens'
import { INSIGHT_SECTORS } from '../data/insights'
import TagChip from '../components/ui/TagChip'
import SectionLabel from '../components/ui/SectionLabel'
import TrendSpark from '../components/charts/TrendSpark'
import type { Risk, Sector } from '../types/portfolio'

interface Props { isPro: boolean; onUnlock: () => void; onViewPortfolio: (sector: Sector, risk: Risk) => void }

export default function Insights({ isPro, onUnlock, onViewPortfolio }: Props) {
  const best = INSIGHT_SECTORS[0]
  return (
    <div className="px-5 sm:px-8 py-6 max-w-3xl mx-auto">
      <div className="mb-8 fade-up p-5 rounded-xl" style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}>
        <SectionLabel className="mb-2">Best combination right now</SectionLabel>
        <div className="flex items-baseline gap-3 flex-wrap">
          <span className="text-2xl" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>{best.sector} · {best.bestRisk}</span>
          <span className="text-xl font-semibold" style={{ fontFamily: "'DM Serif Display'", color: C.teal }}>+{best.bestReturn}%</span>
        </div>
        <p className="text-sm mt-2" style={{ color: C.muted, fontFamily: 'Inter' }}>Across all sector and strategy combinations, this pairing has the highest projected 1-year yield based on current market data.</p>
        <button onClick={() => onViewPortfolio(best.sector, best.bestRisk)} className="mt-3 text-sm font-semibold transition-all hover:opacity-80"
          style={{ color: C.cyan, fontFamily: 'Inter', borderBottom: `1px solid ${C.cyan}50` }}>
          View this portfolio
        </button>
      </div>

      <SectionLabel className="mb-4">All sectors ranked by yield</SectionLabel>
      <div className="space-y-3">
        {INSIGHT_SECTORS.map((row, i) => {
          const locked = row.locked && !isPro
          return (
            <div key={row.sector} className={`p-4 rounded-xl fade-up d${i + 1}`} style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}>
              <div className="flex items-center gap-4">
                <div className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold"
                  style={{ backgroundColor: i === 0 ? C.cyan : C.border, color: i === 0 ? C.canvas : C.muted, fontFamily: 'Inter' }}>{i + 1}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-semibold" style={{ color: C.text, fontFamily: 'Inter' }}>{row.sector}</span>
                    <TagChip label={row.bestRisk} color={riskColor(row.bestRisk)} />
                    {locked && (
                      <span className="flex items-center gap-1 text-[10px]" style={{ color: C.muted, fontFamily: 'Inter' }}>
                        <svg width="10" height="10" viewBox="0 0 12 14" fill="none"><rect x="2" y="5" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2" /><path d="M4 5V4a2 2 0 014 0v1" stroke="currentColor" strokeWidth="1.2" /></svg>
                        Pro
                      </span>
                    )}
                  </div>
                  <div className="text-xs" style={{ color: C.muted, fontFamily: 'Inter' }}>Best strategy for this sector</div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0" style={{ filter: locked ? 'blur(5px)' : 'none', userSelect: locked ? 'none' : 'auto', pointerEvents: locked ? 'none' : 'auto' }}>
                  <TrendSpark trend={row.trend} up={true} W={72} H={28} />
                  <span className="text-base font-semibold w-16 text-right" style={{ color: C.teal, fontFamily: "'DM Serif Display'" }}>+{row.bestReturn}%</span>
                </div>
                {locked ? (
                  <button onClick={onUnlock} className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all hover:opacity-90"
                    style={{ backgroundColor: `${C.violet}20`, color: C.violet, border: `1px solid ${C.violet}40`, fontFamily: 'Inter' }}>Unlock with Pro</button>
                ) : (
                  <button onClick={() => onViewPortfolio(row.sector, row.bestRisk)} className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all hover:opacity-80"
                    style={{ color: C.cyan, border: `1px solid ${C.cyan}40`, fontFamily: 'Inter' }}>View portfolio</button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
