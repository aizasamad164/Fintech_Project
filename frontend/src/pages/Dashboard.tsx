import { useEffect, useLayoutEffect, useRef, useState, type AnimationEvent } from 'react'
import { C, riskColor, HEADING } from '../theme/tokens'
import { fmt } from '../utils/format'
import { useGeneratedPortfolio } from '../hooks/useGeneratedPortfolio'
import TagChip from '../components/ui/TagChip'
import SectionLabel from '../components/ui/SectionLabel'
import AdjustPanel from '../components/portfolio/AdjustPanel'
import StockCard from '../components/portfolio/StockCard'
import OrbitRings from '../components/charts/OrbitRings'
import AllocationLegend from '../components/charts/AllocationLegend'
import RiskGauge from '../components/charts/RiskGauge'
import HistChart from '../components/charts/HistChart'
import StockDetail from './StockDetail'
import { savePortfolio } from '../services/trackingService'
import { DEFAULT_OPTIONS, type DashVariant, type Portfolio, type PortfolioOptions, type Risk, type Sector } from '../types/portfolio'

interface Props {
  budget: number; risk: Risk; sector: Sector; variant: DashVariant
  opts?: PortfolioOptions; onOpts?: (o: PortfolioOptions) => void   // model scope + Shariah filter
  onVariant: (v: DashVariant) => void
  onRisk: (r: Risk) => void; onSector: (s: Sector) => void; onBudget: (b: number) => void
  onPortfolio?: (p: Portfolio | null) => void   // lets the Advisor tab see what's on screen
  onOpenTracking?: () => void
  onAskAdvisor?: () => void
  isPro?: boolean
  onLocked?: () => void            // opens the Pro paywall
}

type Detail = { ticker: string; origin: string; phase: 'open' | 'closing'; returnScroll: number }

const tile = { border: `1px solid ${C.border}` }

export default function Dashboard({ budget, risk, sector, opts = DEFAULT_OPTIONS, onOpts = () => {}, variant, onVariant, onRisk, onSector, onBudget, onPortfolio, onOpenTracking, onAskAdvisor, isPro = false, onLocked = () => {} }: Props) {
  const { portfolio, loading, error } = useGeneratedPortfolio(budget, risk, sector, opts)
  const [animKey, setAnimKey] = useState(0)
  const [adjustOpen, setAdjustOpen] = useState(false)
  const [detail, setDetail] = useState<Detail | null>(null)
  const rootRef = useRef<HTMLDivElement>(null)
  const restoreScroll = useRef<number | null>(null)
  useEffect(() => { if (portfolio) setAnimKey(k => k + 1); onPortfolio?.(portfolio) }, [portfolio]) // eslint-disable-line react-hooks/exhaustive-deps

  // Save → Tracking. Reset whenever a different portfolio is generated.
  const [save, setSave] = useState<{ state: 'idle' | 'saving' | 'saved' | 'error'; msg?: string }>({ state: 'idle' })
  useEffect(() => { setSave({ state: 'idle' }) }, [portfolio])
  const doSave = async () => {
    if (!portfolio) return
    setSave({ state: 'saving' })
    try {
      const date = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      await savePortfolio(portfolio, `${risk} ${sector} · ${date}`)
      setSave({ state: 'saved' })
    } catch (e) {
      setSave({ state: 'error', msg: e instanceof Error ? e.message : 'Could not save' })
    }
  }

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
          <StockDetail stock={portfolio.stocks[i]} color={riskColor(portfolio.stocks[i].riskClass)} budget={budget} months={portfolio.historical.map(h => h.month)} onBack={closeDetail} />
        </div>
      )
    }
  }

  // ── Action buttons (always visible, big) ──────────────────────────────
  const actions = (
    <div className="flex flex-col sm:flex-row lg:flex-col gap-3 w-full lg:w-64 flex-shrink-0">
      <button onClick={() => setAdjustOpen(o => !o)} aria-expanded={adjustOpen}
        className="cta flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-[0.95rem] font-semibold"
        style={{ backgroundColor: adjustOpen ? C.canvas : C.pink, color: adjustOpen ? C.pink : C.canvas,
          border: `2px solid ${C.pink}`, ['--glow' as string]: C.pink }}>
        <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden><path d="M3 6h9M15 6h2M3 14h2M8 14h9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /><circle cx="13.5" cy="6" r="2" stroke="currentColor" strokeWidth="2" /><circle cx="6.5" cy="14" r="2" stroke="currentColor" strokeWidth="2" /></svg>
        {adjustOpen ? 'Close adjust' : 'Adjust portfolio'}
      </button>
      {portfolio && (save.state === 'saved'
        ? <button onClick={onOpenTracking} className="cta flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-[0.95rem] font-semibold"
            style={{ backgroundColor: C.teal, color: C.canvas, ['--glow' as string]: C.teal }}>
            ✓ Saved · open Tracking
          </button>
        : <button onClick={doSave} disabled={save.state === 'saving'}
            className="cta flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-[0.95rem] font-semibold disabled:opacity-60"
            style={{ backgroundColor: C.cyan, color: C.canvas }}>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden><path d="M5 3h8l3 3v11H5z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" /><path d="M8 3v4h4V3M8 17v-5h5v5" stroke="currentColor" strokeWidth="2" /></svg>
            {save.state === 'saving' ? 'Saving…' : 'Save & track'}
          </button>)}
    </div>
  )

  const chips = (
    <div className="flex flex-wrap items-center gap-2">
      <TagChip label={fmt(budget)} color={C.violet} />
      <TagChip label={risk} color={riskColor(risk)} />
      <TagChip label={sector} color={C.cyan} />
      {opts.model === 'global' && <TagChip label="Global model" color={C.violet} />}
      {opts.shariah && <TagChip label="Shariah-compliant" color={C.teal} />}
      {variant === 'stale' && <TagChip label="Saved data" color={C.pink} />}
      {portfolio?.asOf && <span className="text-xs font-semibold ml-1" style={{ color: C.muted }}>Prices as of {portfolio.asOf}</span>}
    </div>
  )

  const extras = (
    <>
      {save.state === 'error' && <div className="mt-3 text-sm font-bold" style={{ color: C.pink }} role="alert">Couldn't save: {save.msg}</div>}
      {adjustOpen && <AdjustPanel risk={risk} sector={sector} budget={budget} isPro={isPro} opts={opts} onOpts={onOpts} onLocked={onLocked}
        onRisk={onRisk} onSector={onSector} onBudget={onBudget} onClose={() => setAdjustOpen(false)} />}
      {portfolio?.shariah && (
        <div className="glass mt-4 px-5 py-4 rounded-2xl flex flex-wrap items-start gap-3 fade-in" style={{ border: `1px solid ${C.teal}66` }}>
          <span className="text-[11px] font-semibold uppercase px-2 py-1 rounded" style={{ color: C.canvas, backgroundColor: C.teal, letterSpacing: '0.1em' }}>Shariah screened</span>
          <p className="flex-1 min-w-[240px] text-sm font-medium leading-relaxed" style={{ color: C.text2 }}>
            Only Shariah-compliant stocks were considered{portfolio.shariah.asOf ? ` (screening as of ${portfolio.shariah.asOf})` : ''}.{' '}
            {portfolio.shariah.excludedCount} stock{portfolio.shariah.excludedCount === 1 ? ' was' : 's were'} left out. <span style={{ color: C.muted }}>{portfolio.shariah.disclaimer}</span>
          </p>
        </div>
      )}
      {portfolio?.notes?.filter(n => !n.startsWith('Shariah filter removed')).map(n => (
        <div key={n} className="mt-3 px-4 py-2.5 rounded-xl text-sm font-semibold fade-in" style={{ backgroundColor: `${C.pink}18`, border: `1px solid ${C.pink}55`, color: C.text2 }}>{n}</div>
      ))}
      {variant === 'stale' && (
        <div className="mt-3 px-4 py-2.5 rounded-xl text-sm font-semibold fade-in" style={{ backgroundColor: `${C.pink}18`, border: `1px solid ${C.pink}55`, color: C.text2 }}>
          Last updated Aug 30, 2026: showing saved data. Live prices may differ.
        </div>
      )}
    </>
  )

  if (error || !portfolio) {
    return (
      <div ref={rootRef} className="px-4 sm:px-8 py-6 max-w-7xl mx-auto">
        <section className="glass rounded-2xl p-6 sm:p-8 flex flex-col lg:flex-row gap-6 lg:items-center" style={tile}>
          <div className="flex-1">
            {chips}
            {error
              ? <p className="mt-5 text-base font-semibold" style={{ color: C.text2 }} role="alert">
                  Couldn't build this portfolio: {error}. Check that the backend is running, then change any setting to try again.
                </p>
              : <div className="mt-5 space-y-3" aria-label="Building your portfolio">
                  <div className="h-4 w-48 rounded animate-pulse" style={{ backgroundColor: C.border }} />
                  <div className="h-16 w-72 rounded-xl animate-pulse" style={{ backgroundColor: C.border }} />
                </div>}
          </div>
          {actions}
        </section>
        {extras}
      </div>
    )
  }

  const up = portfolio.weightedReturn >= 0
  const top = portfolio.stocks[0]
  const riskWord = portfolio.riskRating <= 2 ? 'Low' : portfolio.riskRating <= 3 ? 'Moderate' : 'Elevated'
  const riskTone = portfolio.riskRating >= 4 ? C.pink : portfolio.riskRating >= 3 ? C.cyan : C.teal

  return (
    <div ref={rootRef} className="px-4 sm:px-8 py-6 max-w-7xl mx-auto">
      <div key={animKey} style={{ opacity: loading ? 0.5 : 1, transition: 'opacity 0.2s' }}>

        {/* ── 1. Hero: projected value + the two main buttons ─────────── */}
        <section className="glass relative overflow-hidden rounded-2xl p-6 sm:p-8 flex flex-col lg:flex-row gap-6 lg:items-center fade-up"
          style={{ border: `1px solid ${C.border}`, boxShadow: `0 30px 80px -40px ${riskColor(risk)}` }}>
          <div className="absolute -top-24 -right-16 w-80 h-80 rounded-full pointer-events-none" aria-hidden
            style={{ background: `radial-gradient(circle, ${riskColor(risk)}2e 0%, transparent 70%)` }} />
          <div className="relative flex-1 min-w-0">
            {chips}
            <div className="text-sm font-bold uppercase mt-5 mb-2" style={{ color: C.muted, letterSpacing: '0.09em' }}>
              If this mix repeats last year, in 1 year you'd have
            </div>
            <div className="leading-none mb-3" style={{ fontFamily: HEADING, fontWeight: 600, letterSpacing: '-0.025em', color: C.text, fontSize: 'clamp(2.5rem, 4.5vw, 3.6rem)' }}>{fmt(portfolio.projectedValue)}</div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <span className="text-lg font-semibold px-2.5 py-1 rounded-lg" style={{ color: C.canvas, backgroundColor: up ? C.teal : C.pink }}>
                {up ? '+' : ''}{portfolio.weightedReturn.toFixed(1)}%
              </span>
              <span className="text-base font-semibold" style={{ color: C.text2 }}>
                from your {fmt(budget)} · {portfolio.stocks.length} stocks · largest: {top.ticker} ({top.allocation}%)
              </span>
            </div>
          </div>
          <div className="relative">{actions}</div>
        </section>
        {extras}

        {/* ── 2. The three instruments, side by side ──────────────────── */}
        <div className="grid gap-5 mt-6 md:grid-cols-2 xl:grid-cols-3">
          <section className="glass rounded-2xl p-5 scale-up d2" style={tile}>
            <SectionLabel className="mb-1">Where your money goes</SectionLabel>
            <p className="text-sm font-semibold mb-4" style={{ color: C.muted }}>Share of your {fmt(budget)} in each stock</p>
            <div className="flex flex-col sm:flex-row md:flex-col items-center gap-5">
              <div className="w-full max-w-[190px] flex-shrink-0"><OrbitRings stocks={portfolio.stocks} animate={true} /></div>
              <AllocationLegend stocks={portfolio.stocks} />
            </div>
          </section>

          <section className="glass rounded-2xl p-5 flex flex-col fade-up d3 relative overflow-hidden" style={tile}>
            <div className="absolute inset-x-0 -bottom-16 h-40 pointer-events-none" style={{ background: `radial-gradient(ellipse at center, ${riskTone}33, transparent 70%)` }} aria-hidden />
            <SectionLabel className="mb-1">Risk rating</SectionLabel>
            <p className="text-sm font-semibold mb-2" style={{ color: C.muted }}>How much this mix tends to swing</p>
            <div className="flex-1 flex flex-col items-center justify-center">
              <RiskGauge rating={portfolio.riskRating} animate={true} />
              <div className="text-2xl font-bold mt-1" style={{ color: riskTone }}>{riskWord} risk</div>
              <div className="text-sm font-bold" style={{ color: C.text2 }}>{portfolio.riskRating} out of 5</div>
            </div>
          </section>

          <section className="glass rounded-2xl p-5 flex flex-col fade-up d4 md:col-span-2 xl:col-span-1" style={tile}>
            <SectionLabel className="mb-1">Past 12 months</SectionLabel>
            <p className="text-sm font-semibold mb-3" style={{ color: C.muted }}>
              <span style={{ color: C.text2 }}>{fmt(budget)}</span> would have become{' '}
              <span style={{ color: up ? C.teal : C.pink, fontWeight: 700 }}>{fmt(portfolio.projectedValue)}</span>
            </p>
            <div className="flex-1 flex items-center"><HistChart historical={portfolio.historical} compact /></div>
          </section>
        </div>

        {/* ── 3. The stocks, side by side ─────────────────────────────── */}
        <div className="mt-10 mb-4 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl" style={{ fontFamily: HEADING, fontWeight: 600, letterSpacing: '-0.025em', color: C.text }}>Your {portfolio.stocks.length} stocks</h2>
            <p className="text-base font-semibold" style={{ color: C.text2 }}>Each card shows how much of your {fmt(budget)} goes into that company. Tap one to learn more.</p>
          </div>
          <div className="flex items-center gap-3 text-xs font-bold" style={{ color: C.muted }}>
            {(['Conservative', 'Balanced', 'Aggressive'] as Risk[]).map(r => (
              <span key={r} className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: riskColor(r) }} />{r}</span>
            ))}
          </div>
        </div>
        <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
          {portfolio.stocks.map((s, i) => (
            <StockCard key={s.ticker} stock={s} budget={budget} index={i} shariah={opts.shariah} onOpen={el => openDetail(s.ticker, el)} />
          ))}
        </div>

        {/* ── 4. Plain-English read + advisor ─────────────────────────── */}
        <div className="grid gap-5 mt-10 lg:grid-cols-3">
          <section className="glass lg:col-span-2 rounded-2xl p-6 fade-up d6" style={{ border: `1px solid ${C.border}`, borderLeft: `4px solid ${C.violet}` }}>
            <div className="flex items-center justify-between mb-4 gap-2">
              <h3 className="text-lg font-semibold" style={{ color: C.text }}>In plain English</h3>
              {portfolio.explanationSource === 'llm' && <TagChip label="AI-written" color={C.violet} />}
            </div>
            {variant === 'no-explanation' || portfolio.explanation.length === 0 ? (
              <p className="text-base font-medium leading-relaxed" style={{ color: C.text2 }}>
                We couldn't generate a custom explanation for this combination. The standard read: a {risk.toLowerCase()} mix in {sector} across {portfolio.stocks.length} stocks,
                with the most money in {top.name} ({top.allocation}%). Over the past 12 months it would have returned about{' '}
                <b style={{ color: up ? C.teal : C.pink }}>{portfolio.weightedReturn.toFixed(1)}%</b>.
              </p>
            ) : (
              <ol className="space-y-4">
                {portfolio.explanation.map((b, i) => (
                  <li key={i} className="flex gap-3">
                    <span className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold" style={{ backgroundColor: [C.pink, C.cyan, C.teal][i % 3], color: C.canvas }}>{i + 1}</span>
                    <p className="text-base font-medium leading-relaxed" style={{ color: C.text2 }}>{b}</p>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <div className="flex flex-col gap-4">
            {onAskAdvisor && (
              <button onClick={onAskAdvisor} className="tint-hover glass w-full text-left rounded-2xl p-5 flex items-center gap-4"
                style={{ ['--fill' as string]: C.pink, border: `2px solid ${C.pink}55` }}>
                <span className="w-12 h-12 rounded-2xl flex items-center justify-center text-lg font-semibold flex-shrink-0" style={{ backgroundColor: C.pink, color: C.canvas }}>?</span>
                <span>
                  <span className="block text-base font-bold" style={{ color: C.text }}>Ask the advisor</span>
                  <span className="block text-sm font-semibold" style={{ color: C.text2 }}>Why these stocks? What's in the news?</span>
                </span>
              </button>
            )}
            <p className="text-sm font-medium leading-relaxed px-1" style={{ color: C.muted }}>
              <strong style={{ color: C.text2 }}>For educational purposes only.</strong> This tool does not execute trades, hold funds, or give licensed financial advice. Past returns don't guarantee future results.
            </p>
          </div>
        </div>

        {/* Demo-only state switcher, remove before release */}
        <div className="mt-10 pt-4 flex items-center gap-2 flex-wrap" style={{ borderTop: `1px solid ${C.border}` }}>
          <span className="text-[10px] uppercase tracking-widest font-bold" style={{ color: C.muted, opacity: 0.6 }}>View state:</span>
          {(['success', 'no-explanation', 'stale'] as DashVariant[]).map(v => (
            <button key={v} onClick={() => onVariant(v)} className="text-[10px] font-bold px-2 py-1 rounded transition-all"
              style={{ border: `1px solid ${variant === v ? C.violet : C.border}`, color: variant === v ? C.violet : C.muted, backgroundColor: variant === v ? `${C.violet}12` : 'transparent' }}>
              {v === 'success' ? 'Success' : v === 'no-explanation' ? 'No explanation' : 'Stale data'}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
