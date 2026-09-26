import { C, ORBIT_COLORS } from '../../theme/tokens'
import type { PortfolioStock } from '../../types/portfolio'

// Key for the orbit chart (dollar amounts live in the holdings list): swatch + ticker + percentage, one clean line each.
export default function AllocationLegend({ stocks }: { stocks: PortfolioStock[] }) {
  return (
    <ul className="space-y-2.5 w-full min-w-0 max-w-[260px]">
      {stocks.map((s, i) => (
        <li key={s.ticker} className="flex items-center gap-3 text-sm">
          <span className="w-3 h-3 rounded-sm flex-shrink-0" style={{ backgroundColor: ORBIT_COLORS[i % ORBIT_COLORS.length] }} aria-hidden />
          <span className="font-semibold flex-1" style={{ color: C.text }}>{s.ticker}</span>
          <span className="font-semibold" style={{ color: C.text2 }}>{s.allocation}%</span>
        </li>
      ))}
    </ul>
  )
}
