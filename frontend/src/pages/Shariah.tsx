import { useEffect, useMemo, useState } from 'react'
import { C, HEADING } from '../theme/tokens'
import PageHeader from '../components/ui/PageHeader'
import { getShariahInfo, type ShariahInfo, type ShariahStatus } from '../services/shariahService'
import { sectorLabel } from '../services/portfolioService'

const STATUS: Record<ShariahStatus, { label: string; color: string; meaning: string }> = {
  compliant: { label: 'Compliant', color: C.teal, meaning: 'Passes the screen. Can appear in Shariah portfolios.' },
  disputed: { label: 'Disputed', color: '#F0B43C', meaning: 'The screeners disagree. Left out to be safe.' },
  non_compliant: { label: 'Not compliant', color: C.pink, meaning: 'Fails the screen. Always left out.' },
}
const VERDICT: Record<string, string> = {
  halal: 'Pass', compliant: 'Pass', not_halal: 'Fail', non_compliant: 'Fail', questionable: 'Questionable',
}

interface Props { enabled: boolean; onToggle: (on: boolean) => void; onBuild: () => void }

/** What Shariah screening means here, which stocks pass, and a switch to apply it. */
export default function Shariah({ enabled, onToggle, onBuild }: Props) {
  const [info, setInfo] = useState<ShariahInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<ShariahStatus | 'all'>('all')
  useEffect(() => { getShariahInfo().then(setInfo).catch(e => setError(e.message)) }, [])

  const bySector = useMemo(() => {
    const rows = (info?.screened ?? []).filter(r => filter === 'all' || r.status === filter)
    const groups: Record<string, typeof rows> = {}
    rows.forEach(r => { (groups[r.sector] ??= []).push(r) })
    return Object.entries(groups)
  }, [info, filter])

  const counts = useMemo(() => {
    const c: Record<ShariahStatus, number> = { compliant: 0, disputed: 0, non_compliant: 0 }
    ;(info?.screened ?? []).forEach(r => { c[r.status] += 1 })
    return c
  }, [info])

  return (
    <div className="px-4 sm:px-8 py-8 max-w-6xl mx-auto">
      <PageHeader title="Shariah compliance" subtitle="Build portfolios only from stocks that pass Islamic finance screening, and see how each stock was judged." />

      {/* Switch + how it works */}
      <section className="glass rounded-2xl p-6 grid gap-6 lg:grid-cols-5 fade-up" style={{ border: `1px solid ${enabled ? C.teal : C.border}`, boxShadow: enabled ? `0 20px 50px -30px ${C.teal}` : 'none' }}>
        <div className="lg:col-span-3">
          <div className="text-[11px] font-semibold uppercase mb-2" style={{ color: C.muted, letterSpacing: '0.1em' }}>How the screen works</div>
          <p className="text-[0.95rem] font-medium leading-relaxed mb-3" style={{ color: C.text2 }}>
            Islamic finance rules out companies whose main business is prohibited (for example alcohol, gambling or interest-based lending),
            and companies that carry too much interest-bearing debt or earn too much from interest. Third-party screeners apply these
            AAOIFI-based rules to each company's latest financial statements.
          </p>
          {info?.rule && <p className="text-sm font-medium leading-relaxed" style={{ color: C.muted }}><b style={{ color: C.text2 }}>This app's rule:</b> {info.rule}</p>}
        </div>
        <div className="lg:col-span-2 flex flex-col justify-center gap-3">
          <button onClick={() => onToggle(!enabled)} role="switch" aria-checked={enabled}
            className="pressable flex items-center gap-4 text-left rounded-xl px-4 py-3.5"
            style={{ border: `1px solid ${enabled ? C.teal : C.border}`, backgroundColor: enabled ? `${C.teal}1c` : 'rgba(10,16,27,0.55)' }}>
            <span className="relative w-11 h-6 rounded-full flex-shrink-0 transition-colors" style={{ backgroundColor: enabled ? C.teal : C.border }} aria-hidden>
              <span className="absolute top-0.5 w-5 h-5 rounded-full transition-all" style={{ left: enabled ? 22 : 2, backgroundColor: C.text }} />
            </span>
            <span>
              <span className="block text-base font-semibold" style={{ color: C.text }}>{enabled ? 'Shariah screening is on' : 'Shariah screening is off'}</span>
              <span className="block text-xs font-medium" style={{ color: C.muted }}>Applies to the portfolios you build next</span>
            </span>
          </button>
          <button onClick={onBuild} className="cta px-6 py-3 rounded-xl text-[0.95rem] font-semibold"
            style={{ backgroundColor: C.teal, color: C.canvas, ['--glow' as string]: C.teal }}>
            {enabled ? 'View my Shariah portfolio' : 'Turn on and view portfolio'}
          </button>
        </div>
      </section>

      {error && <p className="mt-6 text-sm font-semibold" style={{ color: C.pink }} role="alert">Couldn't load screening data: {error}</p>}
      {info && !info.available && <p className="mt-6 text-sm font-semibold" style={{ color: C.pink }} role="alert">{info.message}</p>}

      {info?.available && (
        <>
          {/* Summary */}
          <div className="grid gap-4 sm:grid-cols-3 mt-6">
            {(Object.keys(STATUS) as ShariahStatus[]).map((s, i) => (
              <button key={s} onClick={() => setFilter(f => (f === s ? 'all' : s))} data-active={filter === s}
                className={`tint-fill glass text-left rounded-2xl p-5 fade-up d${i + 2}`}
                style={{ ['--fill' as string]: STATUS[s].color, border: `1px solid ${C.border}` }}>
                <div className="flex items-baseline justify-between">
                  <span className="text-sm font-semibold" style={{ color: STATUS[s].color }}>{STATUS[s].label}</span>
                  <span className="text-3xl" style={{ fontFamily: HEADING, fontWeight: 600, color: C.text }}>{counts[s]}</span>
                </div>
                <p className="text-xs font-medium mt-2" style={{ color: C.muted }}>{STATUS[s].meaning}</p>
              </button>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-4 text-xs font-semibold" style={{ color: C.muted }}>
            <span>Screened as of <b style={{ color: C.text2 }}>{info.as_of}</b></span>
            {info.sources?.map(s => <a key={s.name} href={s.url} target="_blank" rel="noreferrer" className="underline" style={{ color: C.cyan }}>{s.name} ({s.method})</a>)}
            {filter !== 'all' && <button onClick={() => setFilter('all')} className="underline" style={{ color: C.text2 }}>Show all</button>}
          </div>
          {info.warning && <p className="mt-3 text-sm font-semibold" style={{ color: '#F0B43C' }}>{info.warning}</p>}

          {/* Stocks by sector */}
          <div className="grid gap-5 mt-8 md:grid-cols-2">
            {bySector.map(([sector, rows]) => (
              <section key={sector} className="glass rounded-2xl p-5" style={{ border: `1px solid ${C.border}` }}>
                <h2 className="text-lg mb-3" style={{ fontFamily: HEADING, fontWeight: 600, color: C.text }}>{sectorLabel(sector)}</h2>
                <ul className="divide-y" style={{ borderColor: C.border }}>
                  {rows.map(r => (
                    <li key={r.ticker} className="py-2.5 flex items-center gap-3" style={{ borderColor: C.border }}>
                      <span className="w-14 text-sm font-semibold" style={{ color: C.text }}>{r.ticker}</span>
                      <span className="flex-1 text-xs font-medium" style={{ color: C.muted }}>
                        Musaffa: {r.musaffa ? VERDICT[r.musaffa] ?? r.musaffa : 'n/a'} · Zoya: {r.zoya ? VERDICT[r.zoya] ?? r.zoya : 'n/a'}
                      </span>
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded" title={r.note ?? undefined}
                        style={{ color: STATUS[r.status].color, border: `1px solid ${STATUS[r.status].color}66`, backgroundColor: `${STATUS[r.status].color}14` }}>
                        {STATUS[r.status].label}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>

          <p className="text-xs font-medium leading-relaxed mt-8 max-w-3xl" style={{ color: C.muted }}>
            <b style={{ color: C.text2 }}>Please note:</b> {info.disclaimer}
          </p>
        </>
      )}
    </div>
  )
}
