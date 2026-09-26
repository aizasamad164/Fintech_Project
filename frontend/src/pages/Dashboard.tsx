import { useEffect, useState } from 'react'
import { C, ORBIT_COLORS, riskColor } from '../theme/tokens'
import { fmt } from '../utils/format'
import { useGeneratedPortfolio } from '../hooks/useGeneratedPortfolio'
import TagChip from '../components/ui/TagChip'
import SectionLabel from '../components/ui/SectionLabel'
import AdjustPanel from '../components/portfolio/AdjustPanel'
import HoldingItem from '../components/portfolio/HoldingItem'
import OrbitRings from '../components/charts/OrbitRings'
import RiskGauge from '../components/charts/RiskGauge'
import HistChart from '../components/charts/HistChart'
import type { DashVariant, Risk, Sector } from '../types/portfolio'

interface Props {
  budget: number; risk: Risk; sector: Sector; variant: DashVariant
  onVariant: (v: DashVariant) => void
  onRisk: (r: Risk) => void; onSector: (s: Sector) => void; onBudget: (b: number) => void
}

export default function Dashboard({ budget, risk, sector, variant, onVariant, onRisk, onSector, onBudget }: Props) {
  const { portfolio, loading, error } = useGeneratedPortfolio(budget, risk, sector)
  const [animKey, setAnimKey] = useState(0)
  const [adjustOpen, setAdjustOpen] = useState(false)
  useEffect(() => { if (portfolio) setAnimKey(k => k + 1) }, [portfolio])

  const header = (
    <>
      <div className="flex flex-wrap items-center gap-2 mb-2 fade-in">
        <TagChip label={fmt(budget)} color={C.violet} />
        <TagChip label={risk} color={riskColor(risk)} />
        <TagChip label={sector} color={C.cyan} />
        {variant === 'stale' && <TagChip label="⚠ saved data" color={C.amber} />}
        <button onClick={() => setAdjustOpen(o => !o)} className="inline-flex items-center px-2.5 py-1 text-xs rounded-full font-medium transition-all"
          style={{ backgroundColor: adjustOpen ? `${C.violet}25` : `${C.violet}12`, color: C.violet, border: `1px solid ${C.violet}40`, fontFamily: 'Inter' }}>
          {adjustOpen ? 'Close adjust' : 'Adjust'}
        </button>
      </div>
      {adjustOpen && <AdjustPanel risk={risk} sector={sector} budget={budget} onRisk={onRisk} onSector={onSector} onBudget={onBudget} onClose={() => setAdjustOpen(false)} />}
      {variant === 'stale' && (
        <div className="mt-3 px-4 py-2 rounded-lg text-xs fade-in" style={{ backgroundColor: `${C.amber}12`, border: `1px solid ${C.amber}30`, color: C.muted, fontFamily: 'Inter' }}>
          Last updated Aug 30, 2026 — showing saved data. Live prices may differ.
        </div>
      )}
    </>
  )

  if (error) {
    return (
      <div className="px-5 sm:px-8 py-6 max-w-5xl mx-auto">
        {header}
        <div className="mt-8 p-4 rounded-lg text-sm" style={{ backgroundColor: `${C.amber}12`, border: `1px solid ${C.amber}30`, color: C.text2, fontFamily: 'Inter' }}>
          Couldn't build this portfolio: {error}. Check that the backend is running, then change any setting to try again.
        </div>
      </div>
    )
  }

  if (!portfolio) {
    return (
      <div className="px-5 sm:px-8 py-6 max-w-5xl mx-auto">
        {header}
        <p className="mt-8 text-sm" style={{ color: C.muted, fontFamily: 'Inter' }}>Building your portfolio…</p>
      </div>
    )
  }

  const up = portfolio.weightedReturn >= 0
  return (
    <div className="px-5 sm:px-8 py-6 max-w-5xl mx-auto">
      {header}
      <div key={animKey} className="mt-8 grid lg:grid-cols-[300px_1fr] gap-8" style={{ opacity: loading ? 0.5 : 1, transition: 'opacity 0.2s' }}>
        {/* Left column */}
        <div>
          <div className="mb-6 fade-up">
            <SectionLabel className="mb-1">Projected value · 1 year</SectionLabel>
            <div className="text-5xl leading-tight mb-1" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>{fmt(portfolio.projectedValue)}</div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-semibold" style={{ fontFamily: "'DM Serif Display'", color: up ? C.teal : C.amber }}>{up ? '+' : ''}{portfolio.weightedReturn.toFixed(1)}%</span>
              <span className="text-sm" style={{ color: C.muted, fontFamily: 'Inter' }}>weighted avg. return</span>
            </div>
          </div>
          <div className="mb-6 scale-up d2">
            <SectionLabel className="mb-3">Allocation instrument</SectionLabel>
            <OrbitRings stocks={portfolio.stocks} animate={true} />
            <div className="mt-3 space-y-1.5">
              {portfolio.stocks.map((s, i) => (
                <div key={s.ticker} className="flex items-center gap-2 text-xs" style={{ fontFamily: 'Inter' }}>
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: ORBIT_COLORS[i % ORBIT_COLORS.length] }} />
                  <span style={{ color: C.text, fontWeight: 600 }}>{s.ticker}</span>
                  <div className="flex-1 h-px mx-1" style={{ backgroundColor: C.border }} />
                  <span style={{ color: C.muted }}>{s.allocation}%</span>
                  <span style={{ color: C.muted }}>·</span>
                  <span style={{ color: C.text2 }}>{fmt(s.dollars)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="fade-up d4">
            <SectionLabel className="mb-3">Risk rating</SectionLabel>
            <RiskGauge rating={portfolio.riskRating} animate={true} />
            <div className="mt-1 text-center text-xs" style={{ color: C.muted, fontFamily: 'Inter' }}>
              {portfolio.riskRating <= 2 ? 'Low risk' : portfolio.riskRating <= 3 ? 'Moderate risk' : 'Elevated risk'} · rating {portfolio.riskRating}/5
            </div>
          </div>
        </div>

        {/* Right column */}
        <div>
          <div className="mb-8">
            <SectionLabel className="pb-3 mb-1" ruled>Holdings ({portfolio.stocks.length})</SectionLabel>
            {portfolio.stocks.map((s, i) => <HoldingItem key={s.ticker} stock={s} color={ORBIT_COLORS[i % ORBIT_COLORS.length]} index={i} />)}
          </div>

          <div className="mb-8 fade-up d5">
            <div className="flex items-baseline justify-between pb-3 mb-4" style={{ borderBottom: `1px solid ${C.border}` }}>
              <SectionLabel>12-month performance (illustrative)</SectionLabel>
              <div className="text-sm" style={{ fontFamily: 'Inter', color: C.muted }}>
                <span style={{ color: C.text2 }}>{fmt(budget)}</span>{' → '}
                <span style={{ color: up ? C.teal : C.amber, fontWeight: 600 }}>{fmt(portfolio.projectedValue)}</span>
              </div>
            </div>
            <HistChart historical={portfolio.historical} />
          </div>

          <div className="mb-6 fade-up d6">
            <SectionLabel className="pb-3 mb-4" ruled>Plain-English read</SectionLabel>
            {variant === 'no-explanation' || portfolio.explanation.length === 0 ? (
              <div className="px-4 py-4 rounded-lg" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
                <p className="text-sm leading-relaxed" style={{ color: C.muted, fontFamily: 'Inter' }}>
                  We couldn't generate a custom explanation for this combination — here's the standard read: a <span style={{ color: C.text2 }}>{risk.toLowerCase()}</span> allocation in <span style={{ color: C.text2 }}>{sector}</span> spreads your investment across {portfolio.stocks.length} holdings, weighted toward {portfolio.stocks[0].name} at {portfolio.stocks[0].allocation}%. Historical performance for this mix has returned approximately <span style={{ color: up ? C.teal : C.amber }}>{portfolio.weightedReturn.toFixed(1)}%</span> over the past 12 months.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {portfolio.explanation.map((b, i) => (
                  <div key={i} className="flex gap-3">
                    <div className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold mt-0.5" style={{ backgroundColor: C.cyan, color: C.canvas, fontFamily: 'Inter' }}>{i + 1}</div>
                    <p className="text-sm leading-relaxed" style={{ color: C.text2, fontFamily: 'Inter' }}>{b}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="pt-5 fade-up d7" style={{ borderTop: `1px solid ${C.border}` }}>
            <p className="text-xs leading-relaxed" style={{ color: C.muted, fontFamily: 'Inter', maxWidth: 560 }}>
              <strong style={{ color: C.text2, fontWeight: 600 }}>For educational purposes only.</strong>{' '}This tool does not execute trades, hold funds, or provide licensed financial advice. All portfolios are illustrative — historical returns do not guarantee future results. Consult a licensed financial advisor before investing.
            </p>
          </div>

          {/* Demo-only state switcher — remove before release */}
          <div className="mt-8 pt-4 flex items-center gap-2 flex-wrap" style={{ borderTop: `1px solid ${C.border}` }}>
            <span className="text-[10px] uppercase tracking-widest" style={{ color: C.border, fontFamily: 'Inter' }}>View state:</span>
            {(['success', 'no-explanation', 'stale'] as DashVariant[]).map(v => (
              <button key={v} onClick={() => onVariant(v)} className="text-[10px] px-2 py-1 rounded transition-all"
                style={{ fontFamily: 'Inter', border: `1px solid ${variant === v ? C.violet : C.border}`, color: variant === v ? C.violet : C.border, backgroundColor: variant === v ? `${C.violet}12` : 'transparent' }}>
                {v === 'success' ? 'Success' : v === 'no-explanation' ? 'No explanation' : 'Stale data'}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
