import { useEffect, useState } from 'react'
import { getPortfolio } from '../services/portfolioService'
import { DEFAULT_OPTIONS, type Portfolio, type PortfolioOptions, type Risk, type Sector } from '../types/portfolio'

export function useGeneratedPortfolio(budget: number, risk: Risk, sector: Sector, opts: PortfolioOptions = DEFAULT_OPTIONS) {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getPortfolio(budget, risk, sector, opts)
      .then(p => { if (!cancelled) setPortfolio(p) })
      .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : 'Could not load portfolio') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [budget, risk, sector, opts.model, opts.shariah])

  return { portfolio, loading, error }
}
