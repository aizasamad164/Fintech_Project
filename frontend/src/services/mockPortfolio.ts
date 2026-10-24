// Fake portfolio engine that mirrors what the backend will return.
// Lets the UI work before the FastAPI /recommend endpoint is wired up.
import { STOCKS } from '../data/stocks'
import type { Portfolio, PortfolioStock, Risk, Sector, StockDef } from '../types/portfolio'

const MONTHS = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']

export function generateMockPortfolio(budget: number, risk: Risk, sector: Sector): Portfolio {
  const all = STOCKS[sector]
  let sel: StockDef[], ws: number[]
  if (risk === 'Conservative') { sel = all.filter(s => s.riskClass !== 'Aggressive').slice(0, 4); ws = [38, 30, 20, 12] }
  else if (risk === 'Balanced') { sel = all.slice(0, 5); ws = [30, 25, 20, 15, 10] }
  else { sel = [...all.filter(s => s.riskClass === 'Aggressive'), ...all.filter(s => s.riskClass !== 'Aggressive')].slice(0, 4); ws = [40, 30, 20, 10] }

  const n = Math.min(sel.length, ws.length); sel = sel.slice(0, n); ws = ws.slice(0, n)
  const tot = ws.reduce((a, b) => a + b, 0)
  const norm = ws.map(w => Math.round(w * 100 / tot))
  norm[0] += 100 - norm.reduce((a, b) => a + b, 0)

  const stocks: PortfolioStock[] = sel.map((s, i) => {
    const dollars = Math.round(budget * norm[i] / 100)
    return { ...s, allocation: norm[i], dollars, shares: parseFloat((dollars / s.sharePrice).toFixed(3)) }
  })

  const weightedReturn = stocks.reduce((acc, s) => acc + s.allocation * s.yearReturn / 100, 0)
  const riskRating = risk === 'Conservative' ? 2 : risk === 'Balanced' ? 3 : 4

  const raw = MONTHS.map((month, i) => ({ month, value: stocks.reduce((acc, s) => acc + s.dollars * s.trend[i] / 100, 0) }))
  const scale = budget / raw[0].value
  const historical = raw.map(m => ({ ...m, value: Math.round(m.value * scale) }))

  const where = sector === 'Multi-Sector' ? 'multiple sectors' : sector
  const explanation = risk === 'Conservative'
    ? [`Your portfolio anchors to large, established companies — the kind that have held up through market cycles and tend to pay dividends. Slower growth, fewer surprises.`,
       `${stocks[0].name} holds the largest position at ${stocks[0].allocation}%, acting as ballast for the whole portfolio. If one holding dips, it won't pull everything down.`,
       `Based on the past 12 months, this kind of mix returned roughly ${weightedReturn.toFixed(1)}%. That's a steadier path, not the fastest one.`]
    : risk === 'Balanced'
    ? [`This portfolio blends steady earners with a handful of moderate-growth picks — seeking reasonable returns without concentrating in any single, volatile name.`,
       `${stocks.length} holdings across ${where} means a rough quarter for one company has a limited effect on the whole portfolio.`,
       `Over the past 12 months, this allocation would have returned around ${weightedReturn.toFixed(1)}%. Neither the safest nor the most aggressive — right in the middle of the risk spectrum.`]
    : [`This portfolio concentrates on the highest-growth names in ${where}. Larger potential upside — and larger month-to-month swings.`,
       `Expect more volatility than a conservative portfolio. Some months could be up 10%+; others could be down by a similar amount. That's expected with this profile.`,
       `Over the past 12 months, this approach returned ${weightedReturn.toFixed(1)}%. Past performance doesn't predict future results, especially with higher-volatility picks.`]

  return { stocks, weightedReturn, riskRating, explanation, historical, projectedValue: Math.round(budget * (1 + weightedReturn / 100)) }
}
