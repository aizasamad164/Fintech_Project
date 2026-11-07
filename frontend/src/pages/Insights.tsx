import { useEffect, useState } from 'react'
import { C, DISPLAY, riskColor } from '../theme/tokens'
import { getInsights } from '../services/insightsService'
import type { InsightRow } from '../data/insights'
import TagChip from '../components/ui/TagChip'
import PageHeader from '../components/ui/PageHeader'
import TrendSpark from '../components/charts/TrendSpark'
import type { Risk, Sector } from '../types/portfolio'

interface Props { isPro: boolean; onUnlock: () => void; onViewPortfolio: (sector: Sector, risk: Risk) => void }

const Lock = () => (
  <svg width="12" height="13" viewBox="0 0 12 14" fill="none" aria-hidden><rect x="2" y="5" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.6" /><path d="M4 5V4a2 2 0 014 0v1" stroke="currentColor" strokeWidth="1.6" /></svg>
)
const pct = (n: number) => `${n >= 0 ? '+' : ''}${n}%`

export default function Insights({ isPro, onUnlock, onViewPortfolio }: Props) {
  const [rows, setRows] = useState<InsightRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let off = false
    getInsights().then(r => { if (!off) setRows(r) }).catch(e => { if (!off) setError(e.message) })
    return () => { off = true }
  }, [])

  const header = <PageHeader title="Insights" subtitle="Which sector and strategy would have done best over the past 12 months, all ranked in one place." />

  if (error || !rows || rows.length === 0) {
    return (
      <div className="px-4 sm:px-8 py-8 max-w-5xl mx-auto">
        {header}
        {error
          ? <p className="text-base font-semibold" style={{ color: C.text2 }} role="alert">Couldn't load insights: {error}</p>
          : <div className="space-y-3">
              <p className="text-base font-semibold" style={{ color: C.text2 }}>Comparing every sector and strategy… the first load takes a few seconds.</p>
              {[0, 1, 2, 3, 4].map(i => <div key={i} className="h-24 rounded-2xl animate-pulse" style={{ backgroundColor: C.card }} />)}
            </div>}
      </div>
    )
  }

  // Free users only see the best combination they can actually open
  const best = rows.find(r => isPro || !r.locked) ?? rows[0]
  const bestColor = riskColor(best.bestRisk)
  return (
    <div className="px-4 sm:px-8 py-8 max-w-5xl mx-auto">
      {header}

      {/* Winner */}
      <section className="relative overflow-hidden rounded-3xl p-6 sm:p-8 mb-10 fade-up d1"
        style={{ background: `linear-gradient(135deg, ${bestColor}3a 0%, rgba(19,29,48,0.85) 70%)`, border: `2px solid ${bestColor}88`, boxShadow: `0 30px 70px -30px ${bestColor}` }}>
        <div className="text-sm font-bold uppercase mb-2" style={{ color: C.text2, letterSpacing: '0.09em' }}>
          {isPro ? 'Best combination right now' : 'Best combination on your plan'}
        </div>
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-2">
          <span className="text-3xl sm:text-4xl" style={{ fontFamily: DISPLAY, color: C.text }}>{best.sector} · {best.bestRisk}</span>
          <span className="text-3xl font-bold" style={{ color: best.bestReturn >= 0 ? C.teal : C.pink }}>{pct(best.bestReturn)}</span>
        </div>
        <p className="text-base font-semibold mt-3 max-w-2xl" style={{ color: C.text2 }}>
          Of the combinations on your plan, this one had the highest return over the past 12 months. Past results don't predict what happens next.
        </p>
        <button onClick={() => onViewPortfolio(best.sector, best.bestRisk)} className="cta mt-5 px-6 py-3 rounded-2xl text-base font-bold"
          style={{ backgroundColor: bestColor, color: C.canvas, ['--glow' as string]: bestColor }}>
          View this portfolio →
        </button>
      </section>

      <h2 className="text-2xl font-bold mb-4" style={{ color: C.text }}>All sectors, ranked</h2>
      <div className="space-y-3">
        {rows.map((row, i) => {
          const locked = row.locked && !isPro
          const color = riskColor(row.bestRisk)
          return (
            <button key={row.sector} onClick={() => (locked ? onUnlock() : onViewPortfolio(row.sector, row.bestRisk))}
              className={`fill-hover glass w-full text-left rounded-2xl p-5 flex items-center gap-4 fade-up d${Math.min(i + 2, 8)}`}
              style={{ ['--fill' as string]: locked ? C.pink : color, border: `2px solid ${C.border}` }}>
              <div className="w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center text-lg font-bold on-fill-bg"
                style={{ backgroundColor: i === 0 ? C.cyan : C.border, color: i === 0 ? C.canvas : C.text }}>{i + 1}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="text-lg font-bold" style={{ color: C.text }}>{row.sector}</span>
                  <TagChip label={row.bestRisk} color={color} />
                  {row.locked && <span className="inline-flex items-center gap-1 text-xs font-bold" style={{ color: C.pink }}><Lock /> Pro</span>}
                </div>
                <div className="text-sm font-semibold" style={{ color: C.muted }}>Best strategy for this sector</div>
              </div>
              <div className="flex items-center gap-4 flex-shrink-0" aria-hidden={locked}
                style={{ filter: locked ? 'blur(6px)' : 'none', userSelect: locked ? 'none' : 'auto' }}>
                <span className="spark hidden sm:inline"><TrendSpark trend={row.trend} up={row.bestReturn >= 0} W={90} H={32} /></span>
                <span className="text-2xl font-bold w-24 text-right" style={{ color: row.bestReturn >= 0 ? C.teal : C.pink }}>{locked ? '+00.0%' : pct(row.bestReturn)}</span>
              </div>
              <span className="text-sm font-bold flex-shrink-0 hidden md:block w-28 text-right" style={{ color: locked ? C.pink : color }}>
                {locked ? 'Unlock →' : 'View →'}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
