import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { C, DISPLAY } from '../theme/tokens'
import { fmt } from '../utils/format'
import { timeAgo } from '../utils/timeAgo'
import SectionLabel from '../components/ui/SectionLabel'
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

  if (error && !list) return <Shell><p className="text-sm" style={{ color: C.text2 }}>Couldn't load saved portfolios: {error}</p></Shell>
  if (!list) return <Shell><div className="h-32 rounded-2xl animate-pulse" style={{ backgroundColor: C.card }} /></Shell>

  if (list.length === 0) {
    return (
      <Shell>
        <div className="rounded-2xl p-6 text-center" style={{ backgroundColor: C.surface, border: `1px dashed ${C.border}` }}>
          <div className="text-lg mb-1" style={{ fontFamily: DISPLAY, color: C.text }}>Nothing saved yet</div>
          <p className="text-sm mb-4" style={{ color: C.muted }}>Build a portfolio, then tap <b style={{ color: C.cyan }}>Save &amp; track</b> to follow how it does at today's prices.</p>
          <button onClick={onBuild} className="pressable px-4 py-2 rounded-lg text-sm font-semibold" style={{ backgroundColor: C.cyan, color: C.canvas }}>Go to Portfolio</button>
        </div>
      </Shell>
    )
  }

  const current = list.find(p => p.id === selected)
  const s = perf?.summary

  return (
    <Shell>
      {/* Saved portfolio picker */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-5 -mx-1 px-1">
        {list.map(p => (
          <button key={p.id} onClick={() => setSelected(p.id)} className="pressable flex-shrink-0 text-left rounded-xl px-3 py-2"
            style={{ backgroundColor: p.id === selected ? `${C.cyan}14` : C.surface, border: `1px solid ${p.id === selected ? C.cyan : C.border}` }}>
            <div className="text-sm font-semibold whitespace-nowrap" style={{ color: C.text }}>{p.portfolio_name}</div>
            <div className="text-[11px]" style={{ color: C.muted }}>{fmt(Number(p.initial_investment))} · saved {timeAgo(p.created_at)}</div>
          </button>
        ))}
      </div>

      {current && (
        <div className="grid lg:grid-cols-12 gap-5">
          {/* Summary hero */}
          <section className="lg:col-span-7 fade-up">
            <SectionLabel className="mb-2">Value at today's prices</SectionLabel>
            <div className="leading-none mb-2" style={{ fontFamily: DISPLAY, color: C.text, fontSize: 'clamp(2.6rem, 6vw, 4.25rem)' }}>
              {s ? money(s.current_value) : '…'}
            </div>
            {s && (
              <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
                <span className="text-2xl font-semibold" style={{ color: tone(s.total_gain_loss_usd) }}>
                  {signed(s.total_gain_loss_usd).replace(/^([+-])/, '$1$')}
                </span>
                <span className="text-lg font-semibold" style={{ color: tone(s.total_gain_loss_pct) }}>{signed(s.total_gain_loss_pct, '%')}</span>
                <span className="text-sm" style={{ color: C.muted }}>since you saved it · invested {money(s.total_invested)}</span>
              </div>
            )}
            <div className="flex flex-wrap gap-2 mt-4">
              <TagChip label={sectorLabel(current.target_sector)} color={C.cyan} />
              <TagChip label={current.risk_strategy} color={C.violet} />
              {s && s.stale_prices > 0 && <TagChip label={`${s.stale_prices} price${s.stale_prices > 1 ? 's' : ''} not live`} color={C.pink} />}
            </div>
          </section>

          <section className="lg:col-span-5 rounded-2xl p-5 flex flex-col gap-3 fade-up d2" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
            <button onClick={() => onAskAdvisor(current.id)} className="pressable rounded-xl p-3 text-left" style={{ backgroundColor: `${C.pink}14`, border: `1px solid ${C.pink}40` }}>
              <div className="text-sm font-semibold" style={{ color: C.pink }}>Why is it up or down?</div>
              <div className="text-xs" style={{ color: C.muted }}>The advisor checks live prices and news for the biggest mover.</div>
            </button>
            <div className="flex gap-2">
              <button onClick={() => refresh(current.id)} disabled={loadingPerf} className="pressable flex-1 py-2 rounded-lg text-sm font-semibold disabled:opacity-60"
                style={{ backgroundColor: C.cyan, color: C.canvas }}>{loadingPerf ? 'Refreshing…' : 'Refresh prices'}</button>
              <button onClick={() => remove(current.id)} className="pressable px-3 py-2 rounded-lg text-sm" style={{ color: C.muted, border: `1px solid ${C.border}` }}>Remove</button>
            </div>
            <p className="text-[11px]" style={{ color: C.muted }}>
              {updatedAt ? `Updated ${timeAgo(new Date(updatedAt).toISOString())}. ` : ''}
              {USE_MOCK ? 'Mock mode: prices stay at their saved value.' : 'Prices come from the latest market close.'}
            </p>
          </section>

          {/* Holdings */}
          <section className="lg:col-span-12">
            <SectionLabel className="mb-3">Holdings</SectionLabel>
            {error && <p className="text-sm mb-2" style={{ color: C.pink }}>{error}</p>}
            <div className="grid sm:grid-cols-2 gap-3">
              {(perf?.holdings ?? []).map((h, i) => {
                const max = Math.max(...(perf?.holdings ?? []).map(x => x.current_value), 1)
                return (
                  <div key={h.ticker} className={`rounded-xl p-4 fade-up d${Math.min(i + 2, 8)}`} style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-baseline gap-2">
                          <span className="text-sm font-bold" style={{ color: C.text }}>{h.ticker}</span>
                          <span className="text-xs truncate" style={{ color: C.muted }}>{h.name}</span>
                        </div>
                        <div className="text-xs mt-1" style={{ color: C.muted }}>
                          {h.shares} sh · bought {money(h.buy_price)} · now {money(h.current_price)}{!h.price_is_live && ' (not live)'}
                        </div>
                      </div>
                      <span className="text-xs font-semibold px-2 py-1 rounded-full flex-shrink-0"
                        style={{ color: tone(h.gain_loss_pct), backgroundColor: `${tone(h.gain_loss_pct)}18` }}>
                        {signed(h.gain_loss_pct, '%')}
                      </span>
                    </div>
                    <div className="mt-3 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: C.border }}>
                      <div className="h-full rounded-full" style={{ width: `${(h.current_value / max) * 100}%`, backgroundColor: tone(h.gain_loss_usd) === C.muted ? C.cyan : tone(h.gain_loss_usd) }} />
                    </div>
                    <div className="flex justify-between text-xs mt-1.5" style={{ color: C.muted }}>
                      <span>{money(h.current_value)}</span>
                      <span style={{ color: tone(h.gain_loss_usd) }}>{signed(h.gain_loss_usd).replace(/^([+-])/, '$1$')}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        </div>
      )}
    </Shell>
  )
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="px-5 sm:px-8 py-6 max-w-5xl mx-auto">
      <h2 className="text-2xl mb-1" style={{ fontFamily: DISPLAY, color: C.text }}>Tracking</h2>
      <p className="text-sm mb-6" style={{ color: C.muted }}>Your saved practice portfolios, valued at today's prices.</p>
      {children}
    </div>
  )
}
