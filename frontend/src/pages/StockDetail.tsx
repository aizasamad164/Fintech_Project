import { C, DISPLAY, riskColor } from '../theme/tokens'
import { fmt } from '../utils/format'
import TagChip from '../components/ui/TagChip'
import SectionLabel from '../components/ui/SectionLabel'
import HistChart from '../components/charts/HistChart'
import NewsCard from '../components/news/NewsCard'
import { BackLink } from '../components/ui/Buttons'
import type { PortfolioStock, Risk } from '../types/portfolio'

const MONTHS = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']

const WHY: Record<Risk, string> = {
  Conservative: 'An established company with steadier price moves. It anchors the portfolio so one bad month elsewhere hurts less.',
  Balanced: 'A middle-ground pick: more growth potential than the steadiest names, without the biggest swings.',
  Aggressive: 'A higher-growth, higher-swing pick. It adds upside potential, and also most of the portfolio\'s month-to-month movement.',
}

export default function StockDetail({ stock, color, onBack }: { stock: PortfolioStock; color: string; onBack: () => void }) {
  const up = stock.yearReturn >= 0
  const historical = stock.trend.map((v, i) => ({ month: MONTHS[i], value: Math.round(stock.dollars * v / stock.trend[0]) }))
  const stats: [string, string, string?][] = [
    ['Weight', `${stock.allocation}%`],
    ['Invested', fmt(stock.dollars)],
    ['Shares', `${stock.shares}`],
    ['Share price', fmt(stock.sharePrice)],
    stock.mlSignal
      ? ['Model signal (5-day)', `${stock.mlSignal} · ${stock.predicted5d ?? ''}`, stock.mlSignal === 'BUY' ? C.teal : stock.mlSignal === 'SELL' ? C.pink : C.cyan]
      : ['P/E ratio', stock.peRatio != null ? `${stock.peRatio}` : '—'],
    ['Volatility', stock.volatility, stock.volatility === 'High' ? C.pink : stock.volatility === 'Medium' ? C.cyan : C.teal],
  ]
  return (
    <div className="px-5 sm:px-8 py-6 max-w-5xl mx-auto">
      <BackLink label="Back to portfolio" onClick={onBack} />

      <div className="grid lg:grid-cols-12 gap-6 lg:gap-8">
        <div className="lg:col-span-7">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center text-sm font-bold" style={{ backgroundColor: `${color}22`, color, boxShadow: `0 0 24px -6px ${color}` }}>{stock.ticker.slice(0, 2)}</div>
            <div>
              <div className="text-2xl font-bold leading-none" style={{ color: C.text }}>{stock.ticker}</div>
              <div className="text-sm mt-1" style={{ color: C.muted }}>{stock.name}</div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 mb-6">
            <TagChip label={stock.sector} color={C.muted} />
            <TagChip label={`Risk: ${stock.riskClass}`} color={riskColor(stock.riskClass)} />
          </div>
          <div className="flex items-baseline gap-3 mb-6">
            <span className="text-5xl" style={{ fontFamily: DISPLAY, color: C.text }}>{fmt(stock.sharePrice)}</span>
            <span className="text-lg font-semibold" style={{ color: up ? C.teal : C.pink }}>{up ? '+' : ''}{stock.yearReturn.toFixed(1)}% · 1 yr</span>
          </div>
          <div className="rounded-2xl p-4 mb-6" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
            <SectionLabel className="mb-3">Your {fmt(stock.dollars)} over 12 months (illustrative)</SectionLabel>
            <HistChart historical={historical} />
          </div>
          <div className="rounded-xl p-4" style={{ backgroundColor: C.surface, borderLeft: `3px solid ${color}` }}>
            <div className="text-sm font-semibold mb-1" style={{ color: C.text }}>Why it's in your portfolio</div>
            <p className="text-sm leading-relaxed" style={{ color: C.text2 }}>{WHY[stock.riskClass]}</p>
            {stock.mlSignal && (
              <p className="text-xs leading-relaxed mt-2" style={{ color: C.muted }}>
                The sector model rates it <span style={{ color: C.text2, fontWeight: 600 }}>{stock.mlSignal}</span> with{' '}
                {Math.round((stock.mlConfidence ?? 0.5) * 100)}% confidence, expecting about {stock.predicted5d} over the next 5 trading days.
                Short-term model estimates are often wrong; treat this as one input, not a forecast.
              </p>
            )}
          </div>
        </div>

        <div className="lg:col-span-5 space-y-6">
          <div className="grid grid-cols-2 gap-3">
            {stats.map(([k, v, c]) => (
              <div key={k} className="rounded-xl p-3.5" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
                <div className="text-[11px] mb-1" style={{ color: C.muted }}>{k}</div>
                <div className="text-lg font-semibold" style={{ color: c ?? C.text }}>{v}</div>
              </div>
            ))}
          </div>
          <NewsCard ticker={stock.ticker} limit={3} />
        </div>
      </div>
    </div>
  )
}
