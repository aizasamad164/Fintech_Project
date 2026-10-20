// ─────────────────────────────────────────────────────────────────────────────
// THE ONE PLACE THE FRONTEND ASKS FOR A PORTFOLIO.
// Right now it returns mock data. When the backend is ready, set
// VITE_USE_MOCK=false in frontend/.env and finish fetchFromBackend() below.
// No page or component needs to change when you switch.
// ─────────────────────────────────────────────────────────────────────────────
import { generateMockPortfolio } from './mockPortfolio'
import type { Portfolio, Risk, Sector } from '../types/portfolio'

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function getPortfolio(budget: number, risk: Risk, sector: Sector): Promise<Portfolio> {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 150)) // imitate network delay
    return generateMockPortfolio(budget, risk, sector)
  }
  return fetchFromBackend(budget, risk, sector)
}

async function fetchFromBackend(budget: number, risk: Risk, sector: Sector): Promise<Portfolio> {
  const res = await fetch(`${API_BASE}/api/v1/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ budget, risk_strategy: risk.toLowerCase(), sector }),
  })
  if (!res.ok) throw new Error(`Backend returned ${res.status}`)
  const data = await res.json()
  // TODO: map the backend response shape onto the Portfolio type once the
  // final schema in backend/app/schemas/portfolio.py is confirmed.
  return data as Portfolio
}
