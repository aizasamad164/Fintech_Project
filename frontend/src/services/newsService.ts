// ─────────────────────────────────────────────────────────────────────────────
// Headlines per ticker. Mock while VITE_USE_MOCK is on.
// Backend plan: GET /api/v1/news/{ticker}?limit=3 → Finnhub company-news,
// cached in Supabase for ~1 hour. Swap happens here only.
// ─────────────────────────────────────────────────────────────────────────────
import type { NewsItem } from '../types/portfolio'

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function getNews(ticker: string, limit = 3): Promise<NewsItem[]> {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 250))
    return mockNews(ticker).slice(0, limit)
  }
  const res = await fetch(`${API_BASE}/api/v1/news/${encodeURIComponent(ticker)}?limit=${limit}`)
  if (!res.ok) throw new Error(`News request failed (${res.status})`)
  return (await res.json()) as NewsItem[]
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
