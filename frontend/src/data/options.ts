import { C } from '../theme/tokens'
import type { Risk, Sector } from '../types/portfolio'

export const RISK_OPTS: { v: Risk; desc: string; range: string; color: string }[] = [
  { v: 'Conservative', desc: 'Favor large, established companies with consistent earnings. Prioritize stability over maximum growth.', range: '5–15% est. return', color: C.teal },
  { v: 'Balanced', desc: 'Mix steady earners with moderate-growth picks. Diversify so no single company carries the whole portfolio.', range: '10–25% est. return', color: C.cyan },
  { v: 'Aggressive', desc: 'Concentrate in high-growth companies. Bigger potential upside and larger swings in both directions.', range: '15–50%+ est. return', color: C.pink },
]

export const SECTOR_OPTS: { v: Sector; desc: string; eg: string; color: string }[] = [
  { v: 'Technology', desc: 'Software, semiconductors, cloud platforms, and internet infrastructure.', eg: 'MSFT · AAPL · NVDA · AMD', color: C.cyan },
  { v: 'Healthcare', desc: 'Medical devices, pharmaceuticals, health insurance, and diagnostics.', eg: 'JNJ · UNH · ISRG · ABT', color: C.teal },
  { v: 'Renewable Energy', desc: 'Solar, wind, clean power utilities, and sustainable energy systems.', eg: 'NEE · FSLR · BEP · ENPH', color: '#B8F36B' },
  { v: 'Pharmaceuticals', desc: 'Drug makers and biotech: prescription medicines, vaccines, and treatment pipelines.', eg: 'LLY · AZN · AMGN · VRTX', color: C.violet },
  { v: 'Multi-Sector', desc: 'Spread across all sectors above for broader diversification.', eg: 'MSFT · JNJ · LLY · NEE', color: C.pink },
]

export const RISKS: Risk[] = ['Conservative', 'Balanced', 'Aggressive']
export const SECTORS: Sector[] = ['Technology', 'Healthcare', 'Pharmaceuticals', 'Renewable Energy', 'Multi-Sector']

/** Sectors that need StockSense Pro. One list, used by onboarding, Adjust and Insights. */
export const PRO_SECTORS: Sector[] = ['Healthcare', 'Multi-Sector']
export const isProSector = (s: Sector) => PRO_SECTORS.includes(s)
