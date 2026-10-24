// Saved portfolios + live P&L.
// Live → /api/portfolio/save | list | {id}/performance | DELETE {id}
// Mock → browser localStorage with prices frozen at save time (0% change)
import { api, USE_MOCK } from './api'
import { getUserId } from '../utils/userId'
import { SECTOR_TO_API } from './portfolioService'
import type { Performance, Portfolio, SavedPortfolio } from '../types/portfolio'

const MOCK_KEY = 'stocksense.mockSaved'

function mockLoad(): SavedPortfolio[] {
  try { return JSON.parse(localStorage.getItem(MOCK_KEY) ?? '[]') } catch { return [] }
}
function mockStore(list: SavedPortfolio[]) {
  try { localStorage.setItem(MOCK_KEY, JSON.stringify(list)) } catch { /* private mode */ }
}

export async function savePortfolio(p: Portfolio, name: string): Promise<SavedPortfolio> {
  const body = {
    user_id: getUserId(),
    portfolio_name: name,
    target_sector: p.sector ? SECTOR_TO_API[p.sector] : 'All',
    risk_strategy: (p.riskStrategy ?? 'Balanced').toLowerCase(),
    initial_investment: p.budget ?? p.stocks.reduce((a, s) => a + s.dollars, 0),
    positions: p.stocks.map(s => ({
      ticker: s.ticker, sector: s.sector, shares_held: s.shares, buy_price: s.sharePrice,
      cost_basis: Math.round(s.shares * s.sharePrice * 100) / 100,
    })),
  }
  if (USE_MOCK) {
    const saved: SavedPortfolio = { ...body, id: crypto.randomUUID(), created_at: new Date().toISOString() }
    mockStore([saved, ...mockLoad()])
    return saved
  }
  const res = await api<{ portfolio: SavedPortfolio }>('/api/portfolio/save', { method: 'POST', body: JSON.stringify(body) })
  return res.portfolio
}

export async function listPortfolios(): Promise<SavedPortfolio[]> {
  if (USE_MOCK) return mockLoad()
  const res = await api<{ portfolios: SavedPortfolio[] }>(`/api/portfolio/list?user_id=${getUserId()}`)
  return res.portfolios
}

export async function getPerformance(id: string): Promise<Performance> {
  if (USE_MOCK) {
    const p = mockLoad().find(x => x.id === id)
    const holdings = (p?.positions ?? []).map(pos => {
      const cost = pos.cost_basis ?? pos.shares_held * pos.buy_price
      return { ticker: pos.ticker, name: pos.ticker, sector: pos.sector, shares: pos.shares_held,
        buy_price: pos.buy_price, current_price: pos.buy_price, cost_basis: cost, current_value: cost,
        gain_loss_usd: 0, gain_loss_pct: 0, price_is_live: false }
    })
    const invested = holdings.reduce((a, h) => a + h.cost_basis, 0)
    return { summary: { total_invested: invested, current_value: invested, total_gain_loss_usd: 0,
      total_gain_loss_pct: 0, positions_count: holdings.length, stale_prices: holdings.length }, holdings }
  }
  return api<Performance>(`/api/portfolio/${id}/performance?user_id=${getUserId()}`)
}

export async function deletePortfolio(id: string): Promise<void> {
  if (USE_MOCK) { mockStore(mockLoad().filter(p => p.id !== id)); return }
  await api(`/api/portfolio/${id}?user_id=${getUserId()}`, { method: 'DELETE' })
}
