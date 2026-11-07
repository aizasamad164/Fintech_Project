import { C, ORBIT_COLORS } from '../../theme/tokens'
import { fmt } from '../../utils/format'
import type { PortfolioStock } from '../../types/portfolio'

// Key for the orbit chart: colour, ticker, share of the user's money and the dollar amount.
export default function AllocationLegend({ stocks }: { stocks: PortfolioStock[] }) {
  return (
    <ul className="space-y-2 w-full min-w-0">
      {stocks.map((s, i) => (
        <li key={s.ticker} className="flex items-center gap-3 text-sm">
          <span className="w-3.5 h-3.5 rounded flex-shrink-0" style={{ backgroundColor: ORBIT_COLORS[i % ORBIT_COLORS.length] }} aria-hidden />
          <span className="font-bold w-14" style={{ color: C.text }}>{s.ticker}</span>
          <span className="flex-1 font-semibold text-right" style={{ color: C.muted }}>{fmt(s.dollars)}</span>
          <span className="font-bold w-14 text-right" style={{ color: C.text }}>{s.allocation}%</span>
        </li>
      ))}
    </ul>
  )
}
