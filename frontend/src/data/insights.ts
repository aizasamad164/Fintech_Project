// MOCK DATA — later replaced by a backend "cross-industry insights" endpoint.
import type { Risk, Sector } from '../types/portfolio'

export interface InsightRow { sector: Sector; bestRisk: Risk; bestReturn: number; trend: number[]; locked: boolean }

const ROWS: InsightRow[] = [
  { sector: 'Technology', bestRisk: 'Aggressive', bestReturn: 52.4, trend: [100,108,118,112,128,140,132,148,162,155,168,172], locked: false },
  { sector: 'Healthcare', bestRisk: 'Aggressive', bestReturn: 18.6, trend: [100,102,105,103,107,111,108,112,116,114,118,118], locked: false },
  { sector: 'Pharmaceuticals', bestRisk: 'Balanced', bestReturn: 16.9, trend: [100,103,106,104,109,113,110,115,118,116,120,119], locked: true },
  { sector: 'Renewable Energy', bestRisk: 'Balanced', bestReturn: 12.4, trend: [100,103,107,104,109,114,110,116,120,117,122,121], locked: true },
  { sector: 'Multi-Sector', bestRisk: 'Balanced', bestReturn: 24.8, trend: [100,104,108,106,112,118,114,120,126,122,128,127], locked: true },
]

// Always ranked highest → lowest yield
export const INSIGHT_SECTORS = [...ROWS].sort((a, b) => b.bestReturn - a.bestReturn)
