import { useEffect, useLayoutEffect, useRef, useState, type AnimationEvent } from 'react'
import { C, DISPLAY, ORBIT_COLORS, riskColor } from '../theme/tokens'
import { fmt } from '../utils/format'
import { useGeneratedPortfolio } from '../hooks/useGeneratedPortfolio'
import TagChip from '../components/ui/TagChip'
import SectionLabel from '../components/ui/SectionLabel'
import AdjustPanel from '../components/portfolio/AdjustPanel'
import HoldingItem from '../components/portfolio/HoldingItem'
import OrbitRings from '../components/charts/OrbitRings'
import AllocationLegend from '../components/charts/AllocationLegend'
import RiskGauge from '../components/charts/RiskGauge'
import HistChart from '../components/charts/HistChart'
import StockDetail from './StockDetail'
import type { DashVariant, Risk, Sector } from '../types/portfolio'

interface Props {
  budget: number; risk: Risk; sector: Sector; variant: DashVariant
  onVariant: (v: DashVariant) => void
  onRisk: (r: Risk) => void; onSector: (s: Sector) => void; onBudget: (b: number) => void
}

type Detail = { ticker: string; origin: string; phase: 'open' | 'closing'; returnScroll: number }

const tile = { backgroundColor: C.surface, border: `1px solid ${C.border}` }

export default function Dashboard({ budget, risk, sector, variant, onVariant, onRisk, onSector, onBudget }: Props) {
  const { portfolio, loading, error } = useGeneratedPortfolio(budget, risk, sector)
  const [animKey, setAnimKey] = useState(0)
  const [adjustOpen, setAdjustOpen] = useState(false)
  const [detail, setDetail] = useState<Detail | null>(null)
  const rootRef = useRef<HTMLDivElement>(null)
  const restoreScroll = useRef<number | null>(null)
  useEffect(() => { if (portfolio) setAnimKey(k => k + 1) }, [portfolio])

  const scrollRoot = () => rootRef.current?.closest('[data-scroll-root]') as HTMLElement | null

  // Tap a holding → remember where it sat on screen, zoom the detail out of that spot
  const openDetail = (ticker: string, el: HTMLElement) => {
    const root = scrollRoot()
    const r = el.getBoundingClientRect()
    const top = root ? root.getBoundingClientRect().top : 0
    const x = r.left + r.width / 2 - (root?.getBoundingClientRect().left ?? 0)
    const y = r.top + r.height / 2 - top
    setDetail({ ticker, origin: `${x}px ${y}px`, phase: 'open', returnScroll: root?.scrollTop ?? 0 })
    if (root) root.scrollTop = 0
  }
  const closeDetail = () => setDetail(d => (d ? { ...d, phase: 'closing' } : d))
  const finishClose = (e: AnimationEvent) => {
    // ignore animations bubbling up from children; only our own zoom-out counts
    if (e.target !== e.currentTarget || detail?.phase !== 'closing') return
    restoreScroll.current = detail.returnScroll
    setDetail(null)
  }
  useLayoutEffect(() => {
    if (!detail && restoreScroll.current !== null) {
      const root = scrollRoot()
      if (root) root.scrollTop = restoreScroll.current
      restoreScroll.current = null
    }
  }, [detail])

  // ── Detail view ─────────────────────────────────────────────────────────
  if (detail && portfolio) {
    const i = portfolio.stocks.findIndex(s => s.ticker === detail.ticker)
    if (i >= 0) {
      return (
        <div ref={rootRef} className={detail.phase === 'open' ? 'zoom-in' : 'zoom-out'}
          style={{ transformOrigin: detail.origin }} onAnimationEnd={finishClose}>
          <StockDetail stock={portfolio.stocks[i]} color={ORBIT_COLORS[i % ORBIT_COLORS.length]} onBack={closeDetail} />
        </div>
      )
    }
  }

  const header = (
    <>
      <div className="flex flex-wrap items-center gap-2 mb-2 fade-in">
        <TagChip label={fmt(budget)} color={C.violet} />
        <TagChip label={risk} color={riskColor(risk)} />
        <TagChip label={sector} color={C.cyan} />
        {variant === 'stale' && <TagChip label="Saved data" color={C.pink} />}
        <button onClick={() => setAdjustOpen(o => !o)} className="pressable inline-flex items-center px-2.5 py-1 text-xs rounded-full font-medium"
          style={{ backgroundColor: adjustOpen ? `${C.pink}25` : `${C.pink}12`, color: C.pink, border: `1px solid ${C.pink}40` }}>
          {adjustOpen ? 'Close adjust' : 'Adjust'}
        </button>
      </div>
      {adjustOpen && <AdjustPanel risk={risk} sector={sector} budget={budget} onRisk={onRisk} onSector={onSector} onBudget={onBudget} onClose={() => setAdjustOpen(false)} />}
      {variant === 'stale' && (
        <div className="mt-3 px-4 py-2 rounded-lg text-xs fade-in" style={{ backgroundColor: `${C.pink}12`, border: `1px solid ${C.pink}30`, color: C.muted }}>
          Last updated Aug 30, 2026 — showing saved data. Live prices may differ.
        </div>
      )}
    </>
  )

  if (error || !portfolio) {
    return (
      <div ref={rootRef} className="px-5 sm:px-8 py-6 max-w-6xl mx-auto">
        {header}
        {error
          ? <div className="mt-8 p-4 rounded-lg text-sm" style={{ backgroundColor: `${C.pink}12`, border: `1px solid ${C.pink}30`, color: C.text2 }}>
              Couldn't build this portfolio: {error}. Check that the backend is running, then change any setting to try again.
            </div>
          : <p className="mt-8 text-sm" style={{ color: C.muted }}>Building your portfolio…</p>}
      </div>
    )
  }

  const up = portfolio.weightedReturn >= 0
  const top = portfolio.stocks[0]
  const riskWord = portfolio.riskRating <= 2 ? 'Low' : portfolio.riskRating <= 3 ? 'Moderate' : 'Elevated'
  const riskTone = portfolio.riskRating >= 4 ? C.pink : portfolio.riskRating >= 3 ? C.cyan : C.teal

  return (
    <div ref={rootRef} className="px-5 sm:px-8 py-6 max-w-6xl mx-auto">
      {header}

      <div key={animKey} className="mt-6 grid grid-cols-1 lg:grid-cols-12 gap-5 lg:gap-6" style={{ opacity: loading ? 0.5 : 1, transition: 'opacity 0.2s' }}>

        {/* ── Hero: bare, oversized — the headline number owns the page ── */}
        <section className="lg:col-span-7 flex flex-col justify-center py-2 fade-up">
          <SectionLabel className="mb-2">Projected value · 1 year</SectionLabel>
          <div className="leading-none mb-3" style={{ fontFamily: DISPLAY, color: C.text, fontSize: 'clamp(3rem, 7vw, 5.25rem)' }}>{fmt(portfolio.projectedValue)}</div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
            <span className="text-2xl font-semibold" style={{ color: up ? C.teal : C.pink }}>{up ? '+' : ''}{portfolio.weightedReturn.toFixed(1)}%</span>
            <span className="text-sm" style={{ color: C.muted }}>from {fmt(budget)} · weighted average of the past 12 months</span>
          </div>
          <div className="mt-6 flex flex-wrap gap-6 text-sm">
            <div><div className="text-[11px]" style={{ color: C.muted }}>Holdings</div><div className="font-semibold" style={{ color: C.text }}>{portfolio.stocks.length}</div></div>
            <div><div className="text-[11px]" style={{ color: C.muted }}>Largest position</div><div className="font-semibold" style={{ color: C.text }}>{top.ticker} · {top.allocation}%</div></div>
            <div><div className="text-[11px]" style={{ color: C.muted }}>Strategy</div><div className="font-semibold" style={{ color: riskColor(risk) }}>{risk}</div></div>
          </div>
        </section>

        {/* ── Risk tile: compact instrument with a tone-matched glow ── */}
        <section className="lg:col-span-5 rounded-2xl p-5 flex flex-col items-center justify-center fade-up d2 relative overflow-hidden" style={tile}>
          <div className="absolute inset-x-0 -bottom-16 h-32 pointer-events-none" style={{ background: `radial-gradient(ellipse at center, ${riskTone}26, transparent 70%)` }} aria-hidden />
          <SectionLabel className="self-start mb-2">Risk rating</SectionLabel>
          <RiskGauge rating={portfolio.riskRating} animate={true} />
          <div className="text-sm mt-1" style={{ color: C.text2 }}><span style={{ color: riskTone, fontWeight: 600 }}>{riskWord} risk</span> · {portfolio.riskRating}/5</div>
        </section>

        {/* ── Allocation instrument: rings + legend, no text on the rings ── */}
        <section className="lg:col-span-5 rounded-2xl p-5 scale-up d3" style={tile}>
          <SectionLabel className="mb-4">Allocation instrument</SectionLabel>
          <div className="flex flex-col sm:flex-row lg:flex-col xl:flex-row items-center gap-6">
            <div className="w-full max-w-[200px] flex-shrink-0"><OrbitRings stocks={portfolio.stocks} animate={true} /></div>
            <AllocationLegend stocks={portfolio.stocks} />
          </div>
        </section>

        {/* ── Performance ── */}
        <section className="lg:col-span-7 rounded-2xl p-5 fade-up d4" style={tile}>
          <div className="flex items-baseline justify-between mb-4 gap-4 flex-wrap">
            <SectionLabel>12-month performance (illustrative)</SectionLabel>
            <div className="text-sm" style={{ color: C.muted }}>
              <span style={{ color: C.text2 }}>{fmt(budget)}</span>{' → '}
              <span style={{ color: up ? C.teal : C.pink, fontWeight: 600 }}>{fmt(portfolio.projectedValue)}</span>
            </div>
          </div>
          <HistChart historical={portfolio.historical} />
        </section>

        {/* ── Holdings: the working area, widest column ── */}
        <section className="lg:col-span-8">
          <SectionLabel className="mb-3">Holdings ({portfolio.stocks.length}) · tap one for details</SectionLabel>
          <div className="space-y-3">
            {portfolio.stocks.map((s, i) => (
              <HoldingItem key={s.ticker} stock={s} color={ORBIT_COLORS[i % ORBIT_COLORS.length]} index={i} onOpen={el => openDetail(s.ticker, el)} />
            ))}
          </div>
        </section>

        {/* ── Plain-English read: pinned alongside holdings on desktop ── */}
        <aside className="lg:col-span-4">
          <div className="lg:sticky lg:top-6 space-y-4 fade-up d6">
            <div className="rounded-2xl p-5" style={{ backgroundColor: C.card, borderLeft: `3px solid ${C.violet}` }}>
              <div className="text-sm font-semibold mb-3" style={{ color: C.text }}>Plain-English read</div>
              {variant === 'no-explanation' || portfolio.explanation.length === 0 ? (
                <p className="text-sm leading-relaxed" style={{ color: C.muted }}>
                  We couldn't generate a custom explanation for this combination. The standard read: a <span style={{ color: C.text2 }}>{risk.toLowerCase()}</span> allocation in <span style={{ color: C.text2 }}>{sector}</span> across {portfolio.stocks.length} holdings, weighted toward {top.name} at {top.allocation}%, which returned about <span style={{ color: up ? C.teal : C.pink }}>{portfolio.weightedReturn.toFixed(1)}%</span> over the past 12 months.
                </p>
              ) : (
                <ol className="space-y-3">
                  {portfolio.explanation.map((b, i) => (
                    <li key={i} className="flex gap-3">
                      <span className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold mt-0.5" style={{ backgroundColor: i === 0 ? C.pink : C.cyan, color: C.canvas }}>{i + 1}</span>
                      <p className="text-sm leading-relaxed" style={{ color: C.text2 }}>{b}</p>
                    </li>
                  ))}
                </ol>
              )}
            </div>
            <p className="text-xs leading-relaxed px-1" style={{ color: C.muted }}>
              <strong style={{ color: C.text2, fontWeight: 600 }}>For educational purposes only.</strong>{' '}This tool does not execute trades, hold funds, or provide licensed financial advice. Historical returns do not guarantee future results.
            </p>
          </div>
        </aside>

        {/* Demo-only state switcher — remove before release */}
        <div className="lg:col-span-12 pt-4 flex items-center gap-2 flex-wrap" style={{ borderTop: `1px solid ${C.border}` }}>
          <span className="text-[10px] uppercase tracking-widest" style={{ color: C.muted, opacity: 0.6 }}>View state:</span>
          {(['success', 'no-explanation', 'stale'] as DashVariant[]).map(v => (
            <button key={v} onClick={() => onVariant(v)} className="text-[10px] px-2 py-1 rounded transition-all"
              style={{ border: `1px solid ${variant === v ? C.violet : C.border}`, color: variant === v ? C.violet : C.muted, backgroundColor: variant === v ? `${C.violet}12` : 'transparent' }}>
              {v === 'success' ? 'Success' : v === 'no-explanation' ? 'No explanation' : 'Stale data'}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
