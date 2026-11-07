import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { C } from '../theme/tokens'
import PageHeader from '../components/ui/PageHeader'
import { sendChat } from '../services/chatService'
import { listPortfolios } from '../services/trackingService'
import type { ChatMessage, Portfolio, SavedPortfolio } from '../types/portfolio'

const TOOL_LABELS: Record<string, string> = {
  optimize_portfolio: 'Built a portfolio',
  get_portfolio_performance: 'Checked live P&L',
  get_ml_prediction: 'Asked the ML model',
  get_market_news: 'Read the news',
  get_stock_price: 'Checked a price',
}

// Minimal, safe markdown: paragraphs, "- " bullets, **bold**. No raw HTML is rendered.
function renderInline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={i} style={{ color: C.text, fontWeight: 600 }}>{part.slice(2, -2)}</strong>
      : <Fragment key={i}>{part}</Fragment>)
}
function Markdown({ text }: { text: string }) {
  const blocks = text.replace(/\r/g, '').split(/\n{2,}/)
  return (
    <div className="space-y-2.5">
      {blocks.map((b, i) => {
        const lines = b.split('\n').filter(Boolean)
        if (b.trim() === '---') return <hr key={i} style={{ borderColor: C.border }} />
        if (lines.every(l => /^\s*([-*•]|\d+\.)\s+/.test(l))) {
          return (
            <ul key={i} className="space-y-1 pl-4 list-disc">
              {lines.map((l, j) => <li key={j}>{renderInline(l.replace(/^\s*([-*•]|\d+\.)\s+/, ''))}</li>)}
            </ul>
          )
        }
        const heading = /^#{1,4}\s+/.test(b)
        return heading
          ? <div key={i} className="font-semibold" style={{ color: C.text }}>{renderInline(b.replace(/^#{1,4}\s+/, ''))}</div>
          : <p key={i}>{lines.map((l, j) => <Fragment key={j}>{j > 0 && <br />}{renderInline(l)}</Fragment>)}</p>
      })}
    </div>
  )
}

interface Props {
  dashboard: Portfolio | null
  savedPortfolioId: string | null
  onSavedPortfolioChange: (id: string | null) => void
}

export default function Advisor({ dashboard, savedPortfolioId, onSavedPortfolioChange }: Props) {
  const sessionId = useMemo(() => `web-${crypto.randomUUID()}`, [])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState<SavedPortfolio[]>([])
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => { listPortfolios().then(setSaved).catch(() => setSaved([])) }, [])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, busy])

  const context = saved.find(p => p.id === savedPortfolioId)
  const suggestions = context
    ? ['How is my saved portfolio doing?', 'Which holding moved the most, and why?', 'Is this portfolio well diversified?']
    : dashboard
    ? [`Why did you pick ${dashboard.stocks[0]?.ticker ?? 'these stocks'}?`, `What's the latest news on ${dashboard.stocks[0]?.ticker ?? 'my top holding'}?`, 'What does volatility mean?']
    : ['Build me a $5,000 balanced tech portfolio', 'What does the model think of NVDA?', 'What is diversification?']

  const send = async (text: string) => {
    const msg = text.trim()
    if (!msg || busy) return
    setInput('')
    setMessages(m => [...m, { role: 'user', content: msg }])
    setBusy(true)
    try {
      const reply = await sendChat(sessionId, msg, { savedPortfolioId, dashboard })
      setMessages(m => [...m, { role: 'assistant', content: reply.content, tools: reply.tools }])
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', content: `Couldn't reach the advisor: ${e instanceof Error ? e.message : 'unknown error'}` }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="px-4 sm:px-8 py-8 max-w-4xl mx-auto flex flex-col" style={{ minHeight: 'calc(100vh - 9rem)' }}>
      <PageHeader title="Advisor" subtitle="Ask anything about your portfolio, a stock, or an investing idea. Answers are educational, not advice." />

      {/* What the advisor can see */}
      <div className="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-3" style={{ border: `1px solid ${C.border}` }}>
        <span className="text-base font-bold" style={{ color: C.text2 }}>Talking about:</span>
        <select value={savedPortfolioId ?? ''} onChange={e => onSavedPortfolioChange(e.target.value || null)}
          className="flex-1 min-w-[220px] rounded-xl px-3 py-2.5 outline-none text-base font-semibold"
          style={{ backgroundColor: C.canvas, color: C.text, border: `2px solid ${C.border}` }}
          aria-label="Portfolio the advisor should use">
          <option value="">{dashboard ? `Portfolio on screen (${dashboard.stocks.map(s => s.ticker).join(', ')})` : 'No portfolio'}</option>
          {saved.map(p => <option key={p.id} value={p.id}>Saved: {p.portfolio_name}</option>)}
        </select>
      </div>

      {/* Conversation */}
      <div className="flex-1 space-y-4 mb-6" aria-live="polite">
        {messages.length === 0 && (
          <div className="glass rounded-3xl p-6 fade-up" style={{ border: `1px solid ${C.border}`, borderLeft: `4px solid ${C.pink}` }}>
            <div className="text-lg font-bold mb-3" style={{ color: C.text }}>Try asking</div>
            <div className="grid gap-3 sm:grid-cols-3">
              {suggestions.map((s, i) => (
                <button key={s} onClick={() => send(s)} className="fill-hover glass text-left text-base font-bold px-4 py-4 rounded-2xl"
                  style={{ ['--fill' as string]: [C.pink, C.cyan, C.teal][i % 3], color: C.text, border: `2px solid ${C.border}` }}>{s}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} fade-up`}>
            <div className={`max-w-[88%] rounded-3xl px-5 py-4 text-base font-medium leading-relaxed ${m.role === 'assistant' ? 'glass' : ''}`}
              style={m.role === 'user'
                ? { backgroundColor: C.cyan, color: C.canvas, fontWeight: 700 }
                : { color: C.text2, border: `1px solid ${C.border}` }}>
              {m.role === 'assistant' && m.tools && m.tools.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {[...new Set(m.tools)].map(t => (
                    <span key={t} className="text-xs font-bold px-2.5 py-1 rounded-full" style={{ color: C.violet, backgroundColor: `${C.violet}22`, border: `1px solid ${C.violet}55` }}>
                      {TOOL_LABELS[t] ?? t}
                    </span>
                  ))}
                </div>
              )}
              {m.role === 'assistant' ? <Markdown text={m.content} /> : m.content}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex items-center gap-2 px-2" aria-label="Advisor is thinking">
            {[0, 1, 2].map(i => <span key={i} className="w-2.5 h-2.5 rounded-full animate-pulse" style={{ backgroundColor: C.pink, animationDelay: `${i * 0.2}s` }} />)}
            <span className="text-sm font-bold ml-1" style={{ color: C.muted }}>Thinking…</span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Composer */}
      <form onSubmit={e => { e.preventDefault(); send(input) }}
        className="glass sticky bottom-4 flex gap-2 rounded-3xl p-2"
        style={{ border: `2px solid ${C.border}`, boxShadow: '0 16px 40px -14px rgba(0,0,0,0.7)' }}>
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask the advisor…" aria-label="Message"
          maxLength={2000} className="flex-1 bg-transparent px-4 py-3 text-base font-semibold outline-none" style={{ color: C.text }} />
        <button type="submit" disabled={busy || !input.trim()} className="cta px-6 py-3 rounded-2xl text-base font-bold disabled:opacity-40"
          style={{ backgroundColor: C.pink, color: C.canvas, ['--glow' as string]: C.pink }}>Send</button>
      </form>
    </div>
  )
}
