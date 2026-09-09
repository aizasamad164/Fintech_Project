import { PieChart, Pie, Cell, Tooltip as RechartsTooltip } from 'recharts';

interface Props {
  allocations: { ticker: string; weight: number }[];
}

const COLORS = ['#4F46E5', '#22C55E', '#F59E0B', '#EF4444', '#06B6D4', '#8B5CF6'];

export default function PortfolioChart({ allocations }: Props) {
  const data = allocations.map((a) => ({ name: a.ticker, value: a.weight }));

  return (
    <PieChart width={320} height={320}>
      <Pie data={data} dataKey="value" nameKey="name" outerRadius={120} label>
        {data.map((_, index) => (
          <Cell key={index} fill={COLORS[index % COLORS.length]} />
        ))}
      </Pie>
      <RechartsTooltip />
    </PieChart>
  );
}
