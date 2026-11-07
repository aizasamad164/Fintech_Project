// Cross-industry board. Mock → data/insights.ts, live → GET /api/insights
import { api, USE_MOCK } from './api'
import { INSIGHT_SECTORS, type InsightRow } from '../data/insights'
import { isProSector } from '../data/options'
import type { Risk, Sector } from '../types/portfolio'

interface ApiInsights { rows: { sector: Sector; bestRisk: Risk; bestReturn: number; trend: number[] }[] }

export async function getInsights(): Promise<InsightRow[]> {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 200))
    return INSIGHT_SECTORS.map(r => ({ ...r, locked: isProSector(r.sector) }))
  }
  const data = await api<ApiInsights>('/api/insights')
  return data.rows.map(r => ({ ...r, trend: r.trend.length > 1 ? r.trend : [100, 100], locked: isProSector(r.sector) }))
}
