export type Screen =
  | 'login' | 'budget' | 'risk' | 'sector' | 'processing'
  | 'nav' | 'paywall' | 'checkout' | 'pro-success'
export type Tab = 'portfolio' | 'insights' | 'learn' | 'account'
export type Risk = 'Conservative' | 'Balanced' | 'Aggressive'
export type Sector = 'Technology' | 'Healthcare' | 'Renewable Energy' | 'Pharmaceuticals' | 'Multi-Sector'
export type DashVariant = 'success' | 'no-explanation' | 'stale'

export interface StockDef {
  ticker: string
  name: string
  sector: string
  riskClass: Risk
  yearReturn: number
  trend: number[]
  peRatio: number
  volatility: 'Low' | 'Medium' | 'High'
  sharePrice: number
}

export interface PortfolioStock extends StockDef {
  allocation: number
  dollars: number
  shares: number
}

export interface Portfolio {
  stocks: PortfolioStock[]
  weightedReturn: number
  riskRating: number
  explanation: string[]
  historical: { month: string; value: number }[]
  projectedValue: number
}

export interface NewsItem {
  id: string
  ticker: string
  headline: string
  source: string
  url: string
  publishedAt: string // ISO timestamp
}
