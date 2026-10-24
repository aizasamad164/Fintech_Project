// ─────────────────────────────────────────────────────────────────────────────
// Headlines per ticker. Mock while VITE_USE_MOCK is on, otherwise
// GET /api/news/{ticker}?limit=3 (yfinance with Google News RSS fallback,
// cached 15 minutes on the backend).
// ─────────────────────────────────────────────────────────────────────────────
import { api, USE_MOCK } from './api'
import type { NewsItem } from '../types/portfolio'

export async function getNews(ticker: string, limit = 3): Promise<NewsItem[]> {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 250))
    return mockNews(ticker).slice(0, limit)
  }
  return api<NewsItem[]>(`/api/news/${encodeURIComponent(ticker)}?limit=${limit}`)
}

// PLACEHOLDER headlines — not real news. Sources are fictional on purpose so
// demo screenshots never attribute invented stories to real outlets.
const TEMPLATES = [
  { h: '{T} shares move as analysts revisit full-year outlook', s: 'Market Wire', ago: 2 },
  { h: 'What {T}\'s latest quarterly numbers mean for long-term holders', s: 'The Daily Ledger', ago: 9 },
  { h: 'Sector roundup: where {T} sits after this week\'s swings', s: 'Sector Brief', ago: 30 },
]

function mockNews(ticker: string): NewsItem[] {
  const now = Date.now()
  return TEMPLATES.map((t, i) => ({
    id: `${ticker}-${i}`,
    ticker,
    headline: t.h.replace('{T}', ticker),
    source: t.s,
    url: '#',
    publishedAt: new Date(now - t.ago * 3600_000).toISOString(),
  }))
}
