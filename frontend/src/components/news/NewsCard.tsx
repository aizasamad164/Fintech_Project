import { C } from '../../theme/tokens'
import { timeAgo } from '../../utils/timeAgo'
import { useTickerNews } from '../../hooks/useTickerNews'

interface Props { ticker: string; limit?: number; compact?: boolean }

// Flat dark panel that sits under a holding (compact) or on the stock profile.
export default function NewsCard({ ticker, limit = 3, compact = false }: Props) {
  const { items, error } = useTickerNews(ticker, limit)
  return (
    <div className={compact ? 'rounded-lg px-3 py-2.5' : 'rounded-xl p-4'}
      style={{ backgroundColor: C.canvas, border: `1px solid ${C.border}` }}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-medium" style={{ color: C.muted }}>Recent news · {ticker}</span>
        <span className="w-1.5 h-1.5 rounded-full breathe" style={{ backgroundColor: C.pink }} aria-hidden />
      </div>

      {error && <p className="text-xs" style={{ color: C.muted }}>News is unavailable right now. Prices and allocation are unaffected.</p>}

      {!items && !error && (
        <div className="space-y-2" aria-label="Loading news">
          {Array.from({ length: limit }).map((_, i) => (
            <div key={i} className="h-3 rounded animate-pulse" style={{ backgroundColor: C.border, width: `${85 - i * 12}%` }} />
          ))}
        </div>
      )}

      {items && items.length === 0 && <p className="text-xs" style={{ color: C.muted }}>No headlines for {ticker} in the last few days.</p>}

      {items && items.length > 0 && (
        <ul className={compact ? 'space-y-1.5' : 'space-y-3'}>
          {items.map((n, i) => (
            <li key={n.id} className={i > 0 && !compact ? 'pt-3' : ''} style={i > 0 && !compact ? { borderTop: `1px solid ${C.border}` } : undefined}>
              <a href={n.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                className={`block leading-snug hover:underline ${compact ? 'text-xs' : 'text-sm'}`} style={{ color: C.text2 }}>
                {n.headline}
              </a>
              <div className="text-[11px] mt-0.5" style={{ color: C.muted }}>
                <span style={{ color: C.cyan }}>{n.source}</span> · {timeAgo(n.publishedAt)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
