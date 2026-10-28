export type Screen =
  | 'login' | 'budget' | 'risk' | 'sector' | 'processing'
  | 'nav' | 'paywall' | 'checkout' | 'pro-success'
export type Tab = 'portfolio' | 'insights' | 'tracking' | 'advisor' | 'learn' | 'account'
export type Risk = 'Conservative' | 'Balanced' | 'Aggressive'
export type Sector = 'Technology' | 'Healthcare' | 'Renewable Energy' | 'Pharmaceuticals' | 'Multi-Sector'
export type DashVariant = 'success' | 'no-explanation' | 'stale'

// Optional extras on top of budget / risk / sector. Defaults reproduce the original behaviour.
export type ModelScope = 'sector' | 'global'   // per-sector models | one cross-sector (global) model
export interface PortfolioOptions { model: ModelScope; shariah: boolean }
export const DEFAULT_OPTIONS: PortfolioOptions = { model: 'sector', shariah: false }

export interface StockDef {
  ticker: string
  name: string
  sector: string
  riskClass: Risk
  yearReturn: number
  trend: number[]
  peRatio: number | null
  volatility: 'Low' | 'Medium' | 'High'
  sharePrice: number
}

export interface PortfolioStock extends StockDef {
  allocation: number
  dollars: number
  shares: number
  // From the backend ML model (absent in mock mode)
  mlSignal?: 'BUY' | 'HOLD' | 'SELL'
  mlConfidence?: number
  predicted5d?: string
}

export interface Portfolio {
  stocks: PortfolioStock[]
  weightedReturn: number
  riskRating: number
  explanation: string[]
  historical: { month: string; value: number }[]
  projectedValue: number
  // Backend extras
  budget?: number
  riskStrategy?: Risk
  sector?: Sector
  asOf?: string
  explanationSource?: 'llm' | 'fallback' | 'none' | 'mock'
  options?: PortfolioOptions
  notes?: string[]
  shariah?: { asOf: string | null; excludedCount: number; disclaimer: string | null }
}

export interface NewsItem {
  id: string
  ticker: string
  headline: string
  source: string
  url: string
  publishedAt: string | null // ISO timestamp
}

// ── Saved portfolios / live tracking ─────────────────────────────────────────
export interface SavedPosition { ticker: string; sector: string; shares_held: number; buy_price: number; cost_basis?: number }
export interface SavedPortfolio {
  id: string
  portfolio_name: string
  target_sector: string
  risk_strategy: string
  initial_investment: number
  created_at: string
  positions: SavedPosition[]
}
export interface TrackedHolding {
  ticker: string; name: string; sector: string; shares: number
  buy_price: number; current_price: number; cost_basis: number; current_value: number
  gain_loss_usd: number; gain_loss_pct: number; price_is_live: boolean
}
export interface Performance {
  summary: {
    total_invested: number; current_value: number; total_gain_loss_usd: number
    total_gain_loss_pct: number; positions_count: number; stale_prices: number; biggest_mover?: string | null
  }
  holdings: TrackedHolding[]
}

// ── Advisor chat ─────────────────────────────────────────────────────────────
export interface ChatMessage { role: 'user' | 'assistant'; content: string; tools?: string[] }
