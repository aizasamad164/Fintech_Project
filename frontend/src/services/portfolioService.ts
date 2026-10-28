// ─────────────────────────────────────────────────────────────────────────────
// THE ONE PLACE THE FRONTEND ASKS FOR A PORTFOLIO.
// VITE_USE_MOCK=true  → local mock data (no backend needed)
// VITE_USE_MOCK=false → POST /api/portfolio/rebalance on the FastAPI backend
// ─────────────────────────────────────────────────────────────────────────────
import { generateMockPortfolio } from './mockPortfolio'
import { api, USE_MOCK } from './api'
import { DEFAULT_OPTIONS, type Portfolio, type PortfolioOptions, type PortfolioStock, type Risk, type Sector } from '../types/portfolio'

// Frontend labels ↔ backend sector keys
export const SECTOR_TO_API: Record<Sector, string> = {
  Technology: 'Technology',
  Healthcare: 'Healthcare',
  Pharmaceuticals: 'Pharmaceuticals',
  'Renewable Energy': 'Renewable_Energy',
  'Multi-Sector': 'All',
}
export const sectorLabel = (apiSector: string): string =>
  apiSector === 'Renewable_Energy' ? 'Renewable Energy' : apiSector === 'All' ? 'Multi-Sector' : apiSector

interface ApiAllocation {
  ticker: string; name: string; sector: string; weight_pct: number
  actual_usd_allocated: number; shares: number; price: number
  year_return_pct: number; volatility: 'Low' | 'Medium' | 'High'
  risk_class: Risk; trend: number[]
  ml_signal: 'BUY' | 'HOLD' | 'SELL'; ml_confidence: number; predicted_5d_return: string
}
interface ApiRebalance {
  status: string
  as_of: string
  risk_strategy: string
  target_sector: string
  summary: { total_portfolio_value: number; weighted_1y_return_pct: number; projected_value: number; risk_rating: number }
  historical: { month: string; value: number }[]
  allocations: ApiAllocation[]
  explanation: string[]
  explanation_source: 'llm' | 'fallback' | 'none'
  notes?: string[]
  shariah?: { as_of: string | null; excluded_count: number; disclaimer: string | null }
}

// Recent results, so the request started during the loading animation is reused
// by the dashboard, and flipping back to an earlier Adjust choice is instant.
const CACHE_MS = 5 * 60_000
const cache = new Map<string, { at: number; promise: Promise<Portfolio> }>()

export function getPortfolio(budget: number, risk: Risk, sector: Sector, opts: PortfolioOptions = DEFAULT_OPTIONS): Promise<Portfolio> {
  const key = `${budget}|${risk}|${sector}|${opts.model}|${opts.shariah}`
  const hit = cache.get(key)
  if (hit && Date.now() - hit.at < CACHE_MS) return hit.promise
  const promise = loadPortfolio(budget, risk, sector, opts)
  cache.set(key, { at: Date.now(), promise })
  promise.catch(() => cache.delete(key)) // never cache failures
  return promise
}

/** Fire-and-forget: start building while the Processing screen animates. */
export function prefetchPortfolio(budget: number, risk: Risk, sector: Sector, opts: PortfolioOptions = DEFAULT_OPTIONS): void {
  getPortfolio(budget, risk, sector, opts).catch(() => { /* the dashboard shows the error */ })
}

async function loadPortfolio(budget: number, risk: Risk, sector: Sector, opts: PortfolioOptions): Promise<Portfolio> {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 150)) // imitate network delay
    return { ...generateMockPortfolio(budget, risk, sector), budget, riskStrategy: risk, sector, explanationSource: 'mock' }
  }
  return fetchFromBackend(budget, risk, sector, opts)
}

async function fetchFromBackend(budget: number, risk: Risk, sector: Sector, opts: PortfolioOptions): Promise<Portfolio> {
  const data = await api<ApiRebalance>('/api/portfolio/rebalance', {
    method: 'POST',
    body: JSON.stringify({
      portfolio_value: budget,
      target_sector: SECTOR_TO_API[sector],
      risk_strategy: risk.toLowerCase(),
      include_explanation: true,
      model_scope: opts.model,
      shariah_only: opts.shariah,
    }),
  })

  const stocks: PortfolioStock[] = data.allocations.map(a => ({
    ticker: a.ticker,
    name: a.name,
    sector: sectorLabel(a.sector),
    riskClass: a.risk_class,
    yearReturn: a.year_return_pct,
    trend: a.trend.length > 1 ? a.trend : [100, 100],
    peRatio: null,
    volatility: a.volatility,
    sharePrice: a.price,
    allocation: Math.round(a.weight_pct * 10) / 10,
    dollars: a.actual_usd_allocated,
    shares: a.shares,
    mlSignal: a.ml_signal,
    mlConfidence: a.ml_confidence,
    predicted5d: a.predicted_5d_return,
  }))

  return {
    stocks,
    weightedReturn: data.summary.weighted_1y_return_pct,
    riskRating: data.summary.risk_rating,
    explanation: data.explanation,
    historical: data.historical,
    projectedValue: data.summary.projected_value,
    budget,
    riskStrategy: risk,
    sector,
    asOf: data.as_of,
    explanationSource: data.explanation_source,
    options: opts,
    notes: data.notes ?? [],
    shariah: data.shariah
      ? { asOf: data.shariah.as_of, excludedCount: data.shariah.excluded_count, disclaimer: data.shariah.disclaimer }
      : undefined,
  }
}
