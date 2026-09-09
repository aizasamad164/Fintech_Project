interface AllocationItem {
  ticker: string;
  weight: number;
  amount: number;
  shares: number;
}

interface Props {
  allocations: AllocationItem[];
}

// FR-6.1: ticker, percentage, dollar value, share counts.
// FR-6.3: converts to swipeable/stacked cards at <=768px via Tailwind's `md:` breakpoint.
export default function AllocationTable({ allocations }: Props) {
  return (
    <>
      {/* Desktop table */}
      <table className="hidden md:table w-full text-left">
        <thead>
          <tr>
            <th>Ticker</th>
            <th>%</th>
            <th>Amount</th>
            <th>Shares</th>
          </tr>
        </thead>
        <tbody>
          {allocations.map((a) => (
            <tr key={a.ticker}>
              <td>{a.ticker}</td>
              <td>{(a.weight * 100).toFixed(1)}%</td>
              <td>${a.amount.toFixed(2)}</td>
              <td>{a.shares}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Mobile cards */}
      <div className="md:hidden flex flex-col gap-3">
        {allocations.map((a) => (
          <div key={a.ticker} className="border rounded-lg p-4 shadow-sm">
            <div className="font-semibold">{a.ticker}</div>
            <div>{(a.weight * 100).toFixed(1)}% &middot; ${a.amount.toFixed(2)}</div>
            <div>{a.shares} shares</div>
          </div>
        ))}
      </div>
    </>
  );
}
