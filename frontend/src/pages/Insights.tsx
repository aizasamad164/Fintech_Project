import { C, riskColor } from '../theme/tokens'
import { useEffect, useState } from 'react'
import { getInsights } from '../services/insightsService'
import type { InsightRow } from '../data/insights'
import TagChip from '../components/ui/TagChip'
import SectionLabel from '../components/ui/SectionLabel'
import TrendSpark from '../components/charts/TrendSpark'
import type { Risk, Sector } from '../types/portfolio'

interface Props { isPro: boolean; onUnlock: () => void; onViewPortfolio: (sector: Sector, risk: Risk) => void }

export default function Insights({ isPro, onUnlock, onViewPortfolio }: Props) {
  const [rows, setRows] = useState<InsightRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let off = false
    getInsights().then(r => { if (!off) setRows(r) }).catch(e => { if (!off) setError(e.message) })
    return () => { off = true }
  }, [])

  if (error || !rows || rows.length === 0) {
    return (
      <div className="px-5 sm:px-8 py-6 max-w-3xl mx-auto">
        <SectionLabel className="mb-3">All sectors ranked by yield</SectionLabel>
        {error
          ? <p className="text-sm" style={{ color: C.text2 }}>Couldn't load insights: {error}</p>
          : <div className="space-y-3">
              <p className="text-sm" style={{ color: C.muted }}>Comparing every sector and strategy… the first load takes a few seconds.</p>
              {[0, 1, 2, 3, 4].map(i => <div key={i} className="h-16 rounded-xl animate-pulse" style={{ backgroundColor: C.card }} />)}
            </div>}
      </div>
    )
  }

  // Free users only see the best combination they can actually open
  const best = rows.find(r => isPro || !r.locked) ?? rows[0]
  return (
    <div className="px-5 sm:px-8 py-6 max-w-3xl mx-auto">
      <div className="mb-8 fade-up p-5 rounded-xl" style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}>
        <SectionLabel className="mb-2">{isPro ? 'Best combination right now' : 'Best combination on your plan'}</SectionLabel>
        <div className="flex items-baseline gap-3 flex-wrap">
          <span className="text-2xl" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>{best.sector} · {best.bestRisk}</span>
          <span className="text-xl font-semibold" style={{ fontFamily: "'DM Serif Display'", color: C.teal }}>{best.bestReturn >= 0 ? '+' : ''}{best.bestReturn}%</span>
        </div>
        <p className="text-sm mt-2" style={{ color: C.muted }}>Across all sector and strategy combinations, this pairing has the highest projected 1-year yield based on the past 12 months of prices.</p>
        <button onClick={() => onViewPortfolio(best.sector, best.bestRisk)} className="mt-3 text-sm font-semibold transition-all hover:opacity-80"
          style={{ color: C.cyan, borderBottom: `1px solid ${C.cyan}50` }}>
          View this portfolio
        </button>
      </div>

      <SectionLabel className="mb-4">All sectors ranked by yield</SectionLabel>
      <div className="space-y-3">
        {rows.map((row, i) => {
          const locked = row.locked && !isPro
          return (
            <div key={row.sector} className={`p-4 rounded-xl fade-up d${i + 1}`} style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}>
              <div className="flex items-center gap-4">
                <div className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold"
                  style={{ backgroundColor: i === 0 ? C.cyan : C.border, color: i === 0 ? C.canvas : C.muted }}>{i + 1}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-semibold" style={{ color: C.text }}>{row.sector}</span>
                    <TagChip label={row.bestRisk} color={riskColor(row.bestRisk)} />
                    {locked && (
                      <span className="flex items-center gap-1 text-[10px]" style={{ color: C.pink }}>
                        <svg width="10" height="10" viewBox="0 0 12 14" fill="none"><rect x="2" y="5" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2" /><path d="M4 5V4a2 2 0 014 0v1" stroke="currentColor" strokeWidth="1.2" /></svg>
                        Pro
                      </span>
                    )}
                  </div>
                  <div className="text-xs" style={{ color: C.muted }}>Best strategy for this sector</div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0" style={{ filter: locked ? 'blur(5px)' : 'none', userSelect: locked ? 'none' : 'auto', pointerEvents: locked ? 'none' : 'auto' }}>
                  <TrendSpark trend={row.trend} up={row.bestReturn >= 0} W={72} H={28} />
                  <span className="text-base font-semibold w-16 text-right" style={{ color: row.bestReturn >= 0 ? C.teal : C.pink, fontFamily: "'DM Serif Display'" }}>{row.bestReturn >= 0 ? '+' : ''}{row.bestReturn}%</span>
                </div>
                {locked ? (
                  <button onClick={onUnlock} className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all hover:opacity-90"
                    style={{ backgroundColor: `${C.pink}1c`, color: C.pink, border: `1px solid ${C.pink}45` }}>Unlock with Pro</button>
                ) : (
                  <button onClick={() => onViewPortfolio(row.sector, row.bestRisk)} className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all hover:opacity-80"
                    style={{ color: C.cyan, border: `1px solid ${C.cyan}40` }}>View portfolio</button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
