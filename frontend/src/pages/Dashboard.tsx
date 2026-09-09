import { useState } from 'react';
import RiskToggle from '../components/RiskToggle';
import SectorFilter from '../components/SectorFilter';
import PortfolioChart from '../components/PortfolioChart';
import AllocationTable from '../components/AllocationTable';
import { usePortfolio } from '../hooks/usePortfolio';

const SECTORS = ['technology', 'healthcare', 'renewable energy', 'combined'];

export default function Dashboard() {
  const [budget, setBudget] = useState(1000);
  const [risk, setRisk] = useState<'conservative' | 'balanced' | 'aggressive'>('balanced');
  const [sectors, setSectors] = useState<string[]>(['combined']);
  const { data, loading, error, generate } = usePortfolio();

  function handleGenerate() {
    generate({ budget, risk_strategy: risk, sectors });
  }

  return (
    <div className="p-6 max-w-4xl mx-auto flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Build Your Portfolio</h1>

      <div>
        <label className="block mb-1 font-medium">Budget ($)</label>
        <input
          type="number"
          value={budget}
          onChange={(e) => setBudget(Number(e.target.value))}
          className="border rounded px-3 py-2 w-40"
        />
      </div>

      <RiskToggle value={risk} onChange={setRisk} />
      <SectorFilter sectors={SECTORS} selected={sectors} onChange={setSectors} />

      <button
        onClick={handleGenerate}
        disabled={loading}
        className="bg-indigo-600 text-white rounded px-4 py-2 w-fit"
      >
        {loading ? 'Generating…' : 'Generate Portfolio'}
      </button>

      {error && <p className="text-red-600">{error}</p>}

      {data && (
        <div className="flex flex-col md:flex-row gap-6 items-start">
          <PortfolioChart allocations={data.allocations} />
          <AllocationTable allocations={data.allocations} />
        </div>
      )}
    </div>
  );
}
