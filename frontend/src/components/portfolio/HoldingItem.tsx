import { C, riskColor } from '../../theme/tokens'
import { fmt } from '../../utils/format'
import TagChip from '../ui/TagChip'
import TrendSpark from '../charts/TrendSpark'
import NewsCard from '../news/NewsCard'
import type { PortfolioStock } from '../../types/portfolio'

interface Props { stock: PortfolioStock; color: string; index: number; onOpen: (el: HTMLElement) => void }

export default function HoldingItem({ stock, color, index, onOpen }: Props) {
  const up = stock.yearReturn >= 0
  const volColor = stock.volatility === 'Low' ? C.teal : stock.volatility === 'Medium' ? C.cyan : C.pink
  return (
    <div className={`rounded-xl fade-up d${Math.min(index + 2, 8)}`} style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
      <button type="button" onClick={e => onOpen(e.currentTarget)} aria-label={`Open ${stock.ticker} details`}
        className="pressable w-full text-left p-4 rounded-xl group">
        <div className="flex items-start justify-between gap-4">
          <div className="flex gap-3 items-start flex-1 min-w-0">
            <div className="w-9 h-9 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-bold" style={{ backgroundColor: `${color}20`, color }}>{stock.ticker.slice(0, 2)}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 mb-0.5">
                <span className="text-sm font-bold" style={{ color: C.text }}>{stock.ticker}</span>
                <span className="text-xs truncate" style={{ color: C.muted }}>{stock.name}</span>
              </div>
              <div className="flex flex-wrap gap-2 mt-1">
                <TagChip label={stock.sector} color={C.muted} />
                <TagChip label={`Risk: ${stock.riskClass}`} color={riskColor(stock.riskClass)} />
                {stock.mlSignal && <TagChip label={`Model: ${stock.mlSignal}`} color={stock.mlSignal === 'BUY' ? C.teal : stock.mlSignal === 'SELL' ? C.pink : C.cyan} />}
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs" style={{ color: C.muted }}>
                <span><span style={{ color: C.text, fontWeight: 600 }}>{stock.allocation}%</span> weight</span>
                <span style={{ color: C.text, fontWeight: 600 }}>{fmt(stock.dollars)}</span>
                <span><span style={{ color: C.text, fontWeight: 600 }}>{stock.shares}</span> sh @ {fmt(stock.sharePrice)}</span>
                <span>Vol: <span style={{ color: volColor }}>{stock.volatility}</span></span>
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1 flex-shrink-0">
            <TrendSpark trend={stock.trend} up={up} />
            <span className="text-sm font-semibold" style={{ color: up ? C.teal : C.pink }}>{up ? '+' : ''}{stock.yearReturn.toFixed(1)}%</span>
            <span className="text-[10px] flex items-center gap-1 transition-colors group-hover:text-[#4FD8E8]" style={{ color: C.muted }}>
              Details
              <svg width="10" height="10" viewBox="0 0 16 16" fill="none"><path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
            </span>
          </div>
        </div>
      </button>
      <div className="px-4 pb-4 -mt-1">
        <NewsCard ticker={stock.ticker} limit={2} compact />
      </div>
    </div>
  )
}
