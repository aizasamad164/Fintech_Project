import { useEffect, useState } from 'react'
import { getNews } from '../services/newsService'
import type { NewsItem } from '../types/portfolio'

export function useTickerNews(ticker: string, limit = 3) {
  const [items, setItems] = useState<NewsItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let cancelled = false
    setItems(null); setError(null)
    getNews(ticker, limit)
      .then(n => { if (!cancelled) setItems(n) })
      .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : 'Could not load news') })
    return () => { cancelled = true }
  }, [ticker, limit])
  return { items, error }
}
