import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { C, DISPLAY } from '../theme/tokens'
import { fmt } from '../utils/format'
import { timeAgo } from '../utils/timeAgo'
import PageHeader from '../components/ui/PageHeader'
import TagChip from '../components/ui/TagChip'
import { deletePortfolio, getPerformance, listPortfolios } from '../services/trackingService'
import { sectorLabel } from '../services/portfolioService'
import { USE_MOCK } from '../services/api'
import type { Performance, SavedPortfolio } from '../types/portfolio'

const money = (n: number) => n.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 })
const signed = (n: number, suffix = '') => `${n >= 0 ? '+' : ''}${n.toFixed(2)}${suffix}`
const tone = (n: number) => (n > 0 ? C.teal : n < 0 ? C.pink : C.muted)

interface Props { onAskAdvisor: (portfolioId: string) => void; onBuild: () => void }

export default function Tracking({ onAskAdvisor, onBuild }: Props) {
  const [list, setList] = useState<SavedPortfolio[] | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [perf, setPerf] = useState<Performance | null>(null)
  const [loadingPerf, setLoadingPerf] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [updatedAt, setUpdatedAt] = useState<number | null>(null)

  useEffect(() => {
    listPortfolios()
      .then(items => { setList(items); if (items[0]) setSelected(items[0].id) })
      .catch(e => setError(e.message))
  }, [])

  const refresh = useCallback(async (id: string) => {
    setLoadingPerf(true); setError(null)
    try { setPerf(await getPerformance(id)); setUpdatedAt(Date.now()) }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not load performance') }
    finally { setLoadingPerf(false) }
  }, [])

  useEffect(() => { if (selected) refresh(selected) }, [selected, refresh])

  const remove = async (id: string) => {
    if (!window.confirm('Remove this saved portfolio? This cannot be undone.')) return
    await deletePortfolio(id)
    const rest = (list ?? []).filter(p => p.id !== id)
    setList(rest); setPerf(null); setSelected(rest[0]?.id ?? null)
  }

  if (error && !list) return <Shell><p className="text-base font-semibold" style={{ color: C.text2 }} role="alert">Couldn't load saved portfolios: {error}</p></Shell>
  if (!list) return <Shell><div className="h-32 rounded-2xl animate-pulse" style={{ backgroundColor: C.card }} /></Shell>

  if (list.length === 0) {
    return (
      <Shell>
        <div className="glass rounded-3xl p-10 text-center" style={{ border: `2px dashed ${C.border}` }}>
          <div className="text-3xl mb-2" style={{ fontFamily: DISPLAY, color: C.text }}>Nothing saved yet</div>
          <p className="text-lg font-semibold mb-6" style={{ color: C.text2 }}>Build a portfolio, then tap <b style={{ color: C.cyan }}>Save &amp; track</b> to follow how it does at today's prices.</p>
          <button onClick={onBuild} className="cta px-8 py-4 rounded-2xl text-base font-bold" style={{ backgroundColor: C.cyan, color: C.canvas }}>Go to Portfolio →</button>
        </div>
      </Shell>
    )
  }

  const current = list.find(p => p.id === selected)
  const s = perf?.summary

  const accent = (n: number) => (n > 0 ? C.teal : n < 0 ? C.pink : C.cyan)
  const gl = s ? accent(s.total_gain_loss_usd) : C.cyan

  return (
    <Shell>
      {/* Saved portfolio picker */}
      <div className="flex gap-3 overflow-x-auto pb-3 mb-6 -mx-1 px-1">
        {list.map(p => {
          const on = p.id === selected
          return (
            <button key={p.id} onClick={() => setSelected(p.id)} className="pressable glass flex-shrink-0 text-left rounded-2xl px-4 py-3"
              style={{ backgroundColor: on ? C.cyan : undefined, border: `2px solid ${on ? C.cyan : C.border}` }}>
              <div className="text-base font-bold whitespace-nowrap" style={{ color: on ? C.canvas : C.text }}>{p.portfolio_name}</div>
              <div className="text-sm font-semibold" style={{ color: on ? C.canvas : C.muted }}>{fmt(Number(p.initial_investment))} · saved {timeAgo(p.created_at)}</div>
            </button>
          )
        })}
      </div>

      {current && (
        <>
          {/* Hero: value now + actions */}
          <section className="glass relative overflow-hidden rounded-3xl p-6 sm:p-8 flex flex-col lg:flex-row gap-6 lg:items-center fade-up"
            style={{ border: `1px solid ${C.border}`, boxShadow: `0 30px 80px -40px ${gl}` }}>
            <div className="absolute -top-24 -right-16 w-80 h-80 rounded-full pointer-events-none" aria-hidden
              style={{ background: `radial-gradient(circle, ${gl}2e 0%, transparent 70%)` }} />
            <div className="relative flex-1 min-w-0">
              <div className="flex flex-wrap gap-2 mb-5">
                <TagChip label={sectorLabel(current.target_sector)} color={C.cyan} />
                <TagChip label={current.risk_strategy} color={C.violet} />
                {s && s.stale_prices > 0 && <TagChip label={`${s.stale_prices} price${s.stale_prices > 1 ? 's' : ''} not live`} color={C.pink} />}
              </div>
              <div className="text-sm font-bold uppercase mb-2" style={{ color: C.muted, letterSpacing: '0.09em' }}>Worth at today's prices</div>
              <div className="leading-none mb-3" style={{ fontFamily: DISPLAY, color: C.text, fontSize: 'clamp(3rem, 7vw, 5rem)' }}>
                {s ? money(s.current_value) : '…'}
              </div>
              {s && (
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                  <span className="text-2xl font-bold px-3 py-1 rounded-xl" style={{ color: C.canvas, backgroundColor: gl }}>
                    {signed(s.total_gain_loss_usd).replace(/^([+-])/, '$1$')} ({signed(s.total_gain_loss_pct, '%')})
                  </span>
                  <span className="text-base font-semibold" style={{ color: C.text2 }}>since you saved it · you put in {money(s.total_invested)}</span>
                </div>
              )}
            </div>
            <div className="relative flex flex-col sm:flex-row lg:flex-col gap-3 w-full lg:w-72 flex-shrink-0">
              <button onClick={() => onAskAdvisor(current.id)} className="cta px-6 py-4 rounded-2xl text-base font-bold"
                style={{ backgroundColor: C.pink, color: C.canvas, ['--glow' as string]: C.pink }}>Why is it up or down?</button>
              <button onClick={() => refresh(current.id)} disabled={loadingPerf} className="cta px-6 py-4 rounded-2xl text-base font-bold disabled:opacity-60"
                style={{ backgroundColor: C.cyan, color: C.canvas }}>{loadingPerf ? 'Refreshing…' : 'Refresh prices'}</button>
              <button onClick={() => remove(current.id)} className="pressable px-6 py-3 rounded-2xl text-sm font-bold"
                style={{ color: C.text2, border: `2px solid ${C.border}` }}>Remove portfolio</button>
            </div>
          </section>
          <p className="text-sm font-semibold mt-3 px-1" style={{ color: C.muted }}>
            {updatedAt ? `Updated ${timeAgo(new Date(updatedAt).toISOString())}. ` : ''}
            {USE_MOCK ? 'Mock mode: prices stay at their saved value.' : 'Prices come from the latest market close.'}
          </p>

          {/* Holdings, side by side */}
          <h2 className="text-3xl mt-10 mb-4" style={{ fontFamily: DISPLAY, color: C.text }}>How each stock is doing</h2>
          {error && <p className="text-base font-bold mb-3" style={{ color: C.pink }} role="alert">{error}</p>}
          <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
            {(perf?.holdings ?? []).map((h, i) => {
              const c = accent(h.gain_loss_usd)
              const total = Math.max(s?.current_value ?? 0, 1)
              return (
                <div key={h.ticker} className={`fill-hover glass rounded-2xl p-5 fade-up d${Math.min(i + 2, 8)}`}
                  style={{ ['--fill' as string]: c, border: `2px solid ${C.border}` }}>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div className="min-w-0">
                      <div className="text-lg font-bold" style={{ color: C.text }}>{h.ticker}</div>
                      <div className="text-sm font-semibold truncate" style={{ color: C.muted }}>{h.name}</div>
                    </div>
                    <span className="on-fill-bg text-sm font-bold px-2.5 py-1 rounded-full flex-shrink-0" style={{ color: c, backgroundColor: `${c}22` }}>
                      {signed(h.gain_loss_pct, '%')}
                    </span>
                  </div>
                  <div className="text-3xl font-bold" style={{ color: C.text }}>{money(h.current_value)}</div>
                  <div className="text-base font-bold mt-1" style={{ color: c }}>{signed(h.gain_loss_usd).replace(/^([+-])/, '$1$')} since saved</div>
                  <div className="on-fill-track mt-3 h-2 rounded-full overflow-hidden" style={{ backgroundColor: C.border }}>
                    <div className="on-fill-bar h-full rounded-full" style={{ width: `${(h.current_value / total) * 100}%`, backgroundColor: c }} />
                  </div>
                  <div className="text-sm font-semibold mt-3" style={{ color: C.text2 }}>
                    {h.shares} shares · bought at {money(h.buy_price)} · now {money(h.current_price)}{!h.price_is_live && ' (not live)'}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </Shell>
  )
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="px-4 sm:px-8 py-8 max-w-7xl mx-auto">
      <PageHeader title="Tracking" subtitle="Your saved practice portfolios, valued at today's prices." />
      {children}
    </div>
  )
}
