import { C, riskColor } from '../../theme/tokens'
import { fmt } from '../../utils/format'
import TagChip from '../ui/TagChip'
import TrendSpark from '../charts/TrendSpark'
import type { PortfolioStock } from '../../types/portfolio'

export default function HoldingItem({ stock, color, index }: { stock: PortfolioStock; color: string; index: number }) {
  const up = stock.yearReturn >= 0
  const volColor = stock.volatility === 'Low' ? C.teal : stock.volatility === 'Medium' ? C.cyan : C.amber
  return (
    <div className={`py-4 fade-up d${Math.min(index + 2, 8)}`} style={{ borderBottom: `1px solid ${C.border}` }}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex gap-3 items-start flex-1 min-w-0">
          <div className="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-bold mt-0.5" style={{ backgroundColor: `${color}20`, color, fontFamily: 'Inter' }}>{stock.ticker.slice(0, 2)}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2 mb-0.5">
              <span className="text-sm font-bold" style={{ color: C.text, fontFamily: 'Inter' }}>{stock.ticker}</span>
              <span className="text-xs truncate" style={{ color: C.muted, fontFamily: 'Inter' }}>{stock.name}</span>
            </div>
            <div className="flex flex-wrap gap-2 mt-1">
              <TagChip label={stock.sector} color={C.muted} />
              <TagChip label={`Risk: ${stock.riskClass}`} color={riskColor(stock.riskClass)} />
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs" style={{ fontFamily: 'Inter', color: C.muted }}>
              <span><span style={{ color: C.text, fontWeight: 600 }}>{stock.allocation}%</span> weight</span>
              <span><span style={{ color: C.text, fontWeight: 600 }}>{fmt(stock.dollars)}</span></span>
              <span><span style={{ color: C.text, fontWeight: 600 }}>{stock.shares}</span> shares @ {fmt(stock.sharePrice)}</span>
              <span>P/E <span style={{ color: C.text }}>{stock.peRatio}</span></span>
              <span>Vol: <span style={{ color: volColor }}>{stock.volatility}</span></span>
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <TrendSpark trend={stock.trend} up={up} />
          <span className="text-sm font-semibold" style={{ color: up ? C.teal : C.amber, fontFamily: 'Inter' }}>{up ? '+' : ''}{stock.yearReturn.toFixed(1)}%</span>
          <span className="text-[10px]" style={{ color: C.border, fontFamily: 'Inter' }}>1-yr</span>
        </div>
      </div>
    </div>
  )
}
