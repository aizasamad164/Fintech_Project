import { C, HEADING, riskColor } from '../../theme/tokens'
import { fmt } from '../../utils/format'
import TrendSpark from '../charts/TrendSpark'
import type { PortfolioStock } from '../../types/portfolio'

interface Props {
  stock: PortfolioStock
  budget: number
  index: number
  onOpen: (el: HTMLElement) => void
}

const OUTLOOK: Record<string, { word: string; tone: string }> = {
  BUY: { word: 'Positive', tone: C.teal },
  HOLD: { word: 'Neutral', tone: C.cyan },
  SELL: { word: 'Negative', tone: C.pink },
}

/**
 * One stock, beginner-first: how much of YOUR money goes here, in % and in $,
 * how it did last year, and what kind of risk it is. Everything else lives
 * on the detail screen. Hover/focus fills the card with its strategy colour.
 */
export default function StockCard({ stock, budget, index, onOpen }: Props) {
  const color = riskColor(stock.riskClass)
  const up = stock.yearReturn >= 0
  const outlook = stock.mlSignal ? OUTLOOK[stock.mlSignal] : null
  return (
    <button type="button" onClick={e => onOpen(e.currentTarget)} aria-label={`${stock.ticker}: ${stock.allocation}% of your money. Open details`}
      className={`tint-fill glass group w-full text-left rounded-2xl p-5 flex flex-col fade-up d${Math.min(index + 2, 8)}`}
      style={{ ['--fill' as string]: color, border: `2px solid ${C.border}` }}>

      {/* Name */}
      <div className="flex items-center gap-3 mb-3">
        <div className="on-fill-bg w-11 h-11 rounded-xl flex-shrink-0 flex items-center justify-center text-sm font-bold"
          style={{ backgroundColor: `${color}22`, color, border: `1px solid ${color}55` }}>{stock.ticker.slice(0, 2)}</div>
        <div className="min-w-0">
          <div className="text-base font-semibold leading-tight" style={{ color: C.text }}>{stock.ticker}</div>
          <div className="text-sm font-semibold truncate" style={{ color: C.muted }}>{stock.name}</div>
        </div>
      </div>
      <span className="on-fill-bg self-start text-xs font-bold px-2.5 py-1 rounded-full mb-4"
        style={{ color, backgroundColor: `${color}1f`, border: `1px solid ${color}55` }}>{stock.riskClass} pick</span>

      {/* The money */}
      <div className="text-3xl leading-none" style={{ fontFamily: HEADING, fontWeight: 600, letterSpacing: '-0.025em', color: C.text }}>{stock.allocation}%</div>
      <div className="text-sm font-bold mt-1" style={{ color: C.text2 }}>of your money goes here</div>
      <div className="text-base font-bold mt-2" style={{ color }}>
        = {fmt(stock.dollars)} <span className="font-semibold" style={{ color: C.muted }}>of your {fmt(budget)}</span>
      </div>
      <div className="on-fill-track h-2 rounded-full mt-3 overflow-hidden" style={{ backgroundColor: C.border }}>
        <div className="on-fill-bar h-full rounded-full" style={{ width: `${Math.min(stock.allocation, 100)}%`, backgroundColor: color }} />
      </div>

      {/* History + outlook */}
      <div className="flex items-end justify-between gap-3 mt-4">
        <div>
          <div className="text-xs font-bold" style={{ color: C.muted }}>Past 12 months</div>
          <div className="text-base font-semibold" style={{ color: up ? C.teal : C.pink }}>{up ? '+' : ''}{stock.yearReturn.toFixed(1)}%</div>
        </div>
        <span className="spark"><TrendSpark trend={stock.trend} up={up} W={84} H={30} /></span>
      </div>
      {outlook && (
        <div className="text-sm font-bold mt-2" style={{ color: C.muted }}>
          Model outlook: <span style={{ color: outlook.tone }}>{outlook.word}</span>
        </div>
      )}

      {/* Clear call to action */}
      <div className="on-fill-bg mt-4 -mx-1 rounded-xl px-3 py-2.5 flex items-center justify-between text-sm font-bold"
        style={{ backgroundColor: `${color}1a`, color }}>
        <span>Tap for details</span>
        <svg width="18" height="18" viewBox="0 0 16 16" fill="none" aria-hidden className="transition-transform group-hover:translate-x-1">
          <path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
        </svg>
      </div>
    </button>
  )
}
