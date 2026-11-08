// Shariah screening data → GET /api/portfolio/shariah/universe
import { api, USE_MOCK } from './api'

export type ShariahStatus = 'compliant' | 'disputed' | 'non_compliant'
export interface ScreenedStock { ticker: string; sector: string; status: ShariahStatus; musaffa: string | null; zoya: string | null; note?: string | null }
export interface ShariahInfo {
  available: boolean
  message?: string
  as_of?: string
  rule?: string
  sources?: { name: string; method: string; url: string }[]
  disclaimer?: string
  compliant_count?: number
  age_days?: number
  warning?: string
  screened?: ScreenedStock[]
}

const MOCK: ShariahInfo = {
  available: true,
  as_of: '2026-10-28',
  rule: 'A stock counts as Shariah-compliant here only if Musaffa passes it AND Zoya does not contradict it.',
  sources: [{ name: 'Musaffa', method: 'AAOIFI-based screening', url: 'https://musaffa.com' }, { name: 'Zoya', method: 'AAOIFI standard', url: 'https://zoya.finance' }],
  disclaimer: 'Screened with third-party tools, not a fatwa. Statuses change when companies report new financial statements.',
  compliant_count: 3,
  screened: [
    { ticker: 'AAPL', sector: 'Technology', status: 'compliant', musaffa: 'halal', zoya: null },
    { ticker: 'NVDA', sector: 'Technology', status: 'compliant', musaffa: 'halal', zoya: null },
    { ticker: 'MSFT', sector: 'Technology', status: 'disputed', musaffa: 'not_halal', zoya: 'questionable', note: 'Musaffa fails it; Zoya marks it questionable.' },
    { ticker: 'ENPH', sector: 'Renewable_Energy', status: 'compliant', musaffa: 'halal', zoya: 'compliant' },
    { ticker: 'NEE', sector: 'Renewable_Energy', status: 'non_compliant', musaffa: 'not_halal', zoya: 'non_compliant' },
  ],
}

export async function getShariahInfo(): Promise<ShariahInfo> {
  if (USE_MOCK) { await new Promise(r => setTimeout(r, 150)); return MOCK }
  return api<ShariahInfo>('/api/portfolio/shariah/universe')
}
