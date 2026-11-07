import { C, DISPLAY } from '../theme/tokens'
import { fmt } from '../utils/format'
import TagChip from '../components/ui/TagChip'
import SectionLabel from '../components/ui/SectionLabel'
import HistChart from '../components/charts/HistChart'
import NewsCard from '../components/news/NewsCard'
import { BackLink } from '../components/ui/Buttons'
import type { PortfolioStock, Risk } from '../types/portfolio'

const FALLBACK_MONTHS = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']

const WHY: Record<Risk, string> = {
  Conservative: 'An established company whose price moves more steadily. It anchors the portfolio, so one bad month elsewhere hurts less.',
  Balanced: 'A middle-ground pick: more growth potential than the steadiest names, without the biggest swings.',
  Aggressive: "A higher-growth, higher-swing pick. It adds upside potential, and also most of the portfolio's month-to-month movement.",
}
const OUTLOOK: Record<string, string> = { BUY: 'Positive', HOLD: 'Neutral', SELL: 'Negative' }

interface Props { stock: PortfolioStock; color: string; budget: number; months?: string[]; onBack: () => void }

/** The screen a stock card "zooms" into. Themed in the stock's strategy colour. */
export default function StockDetail({ stock, color, budget, months, onBack }: Props) {
  const up = stock.yearReturn >= 0
  const labels = months && months.length >= stock.trend.length ? months.slice(-stock.trend.length) : FALLBACK_MONTHS.slice(-stock.trend.length)
  const historical = stock.trend.map((v, i) => ({ month: labels[i] ?? '', value: Math.round(stock.dollars * v / stock.trend[0]) }))
  const stats: [string, string, string?][] = [
    ['Your money in it', fmt(stock.dollars)],
    ['Share of your total', `${stock.allocation}%`],
    ['Shares you\'d own', `${stock.shares}`],
    ['Price per share', fmt(stock.sharePrice)],
    ['Price swings', stock.volatility, stock.volatility === 'High' ? C.pink : stock.volatility === 'Medium' ? C.cyan : C.teal],
    stock.mlSignal
      ? ['Model outlook (5 days)', OUTLOOK[stock.mlSignal] ?? stock.mlSignal, stock.mlSignal === 'BUY' ? C.teal : stock.mlSignal === 'SELL' ? C.pink : C.cyan]
      : ['P/E ratio', stock.peRatio != null ? `${stock.peRatio}` : '—'],
  ]
  return (
    <div className="px-4 sm:px-8 py-6 max-w-6xl mx-auto">
      <BackLink label="Back to portfolio" onClick={onBack} />

      {/* Hero, tinted in the strategy colour */}
      <section className="relative overflow-hidden rounded-3xl p-6 sm:p-8 mb-6"
        style={{ background: `linear-gradient(135deg, ${color}40 0%, ${color}14 45%, rgba(19,29,48,0.85) 100%)`,
          border: `2px solid ${color}88`, boxShadow: `0 30px 80px -30px ${color}` }}>
        <div className="flex flex-wrap items-center gap-4 mb-5">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-lg font-bold"
            style={{ backgroundColor: color, color: C.canvas, boxShadow: `0 0 30px -4px ${color}` }}>{stock.ticker.slice(0, 4)}</div>
          <div className="min-w-0">
            <div className="text-4xl font-bold leading-none" style={{ color: C.text }}>{stock.ticker}</div>
            <div className="text-lg font-semibold mt-1" style={{ color: C.text2 }}>{stock.name}</div>
          </div>
          <div className="flex flex-wrap gap-2 sm:ml-auto">
            <TagChip label={stock.sector} color={C.text2} />
            <TagChip label={`${stock.riskClass} pick`} color={color} />
          </div>
        </div>
        <div className="grid gap-6 sm:grid-cols-2">
          <div>
            <div className="text-sm font-bold uppercase" style={{ color: C.text2, letterSpacing: '0.08em' }}>Your share</div>
            <div className="text-5xl font-bold leading-tight" style={{ color: C.text }}>{stock.allocation}%</div>
            <div className="text-lg font-bold" style={{ color: C.text2 }}>= {fmt(stock.dollars)} of your {fmt(budget)}</div>
          </div>
          <div>
            <div className="text-sm font-bold uppercase" style={{ color: C.text2, letterSpacing: '0.08em' }}>Price today</div>
            <div className="text-5xl leading-tight" style={{ fontFamily: DISPLAY, color: C.text }}>{fmt(stock.sharePrice)}</div>
            <div className="text-lg font-bold" style={{ color: up ? C.teal : C.pink }}>{up ? '+' : ''}{stock.yearReturn.toFixed(1)}% over the past year</div>
          </div>
        </div>
      </section>

      <div className="grid lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 space-y-6">
          <div className="glass rounded-3xl p-5" style={{ border: `1px solid ${C.border}` }}>
            <SectionLabel className="mb-3">Your {fmt(stock.dollars)} over the past 12 months</SectionLabel>
            <HistChart historical={historical} />
          </div>
          <div className="glass rounded-3xl p-5" style={{ border: `1px solid ${C.border}`, borderLeft: `4px solid ${color}` }}>
            <div className="text-lg font-bold mb-2" style={{ color: C.text }}>Why it's in your portfolio</div>
            <p className="text-base font-medium leading-relaxed" style={{ color: C.text2 }}>{WHY[stock.riskClass]}</p>
            {stock.mlSignal && (
              <p className="text-sm font-medium leading-relaxed mt-3" style={{ color: C.muted }}>
                The sector model's short-term outlook is <b style={{ color: C.text2 }}>{(OUTLOOK[stock.mlSignal] ?? stock.mlSignal).toLowerCase()}</b> ({Math.round((stock.mlConfidence ?? 0.5) * 100)}% confidence,
                about {stock.predicted5d} over the next 5 trading days). Short-term estimates are often wrong, so treat this as one input, not a forecast.
              </p>
            )}
          </div>
        </div>

        <div className="lg:col-span-5 space-y-6">
          <div className="grid grid-cols-2 gap-3">
            {stats.map(([k, v, c]) => (
              <div key={k} className="tint-hover glass rounded-2xl p-4" style={{ ['--fill' as string]: color, border: `1px solid ${C.border}` }}>
                <div className="text-xs font-bold mb-1" style={{ color: C.muted }}>{k}</div>
                <div className="text-xl font-bold" style={{ color: c ?? C.text }}>{v}</div>
              </div>
            ))}
          </div>
          <NewsCard ticker={stock.ticker} limit={3} />
        </div>
      </div>
    </div>
  )
}
