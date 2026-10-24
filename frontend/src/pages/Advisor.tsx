import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { C, DISPLAY } from '../theme/tokens'
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
    <div className="px-5 sm:px-8 py-6 max-w-3xl mx-auto flex flex-col" style={{ minHeight: 'calc(100vh - 4rem)' }}>
      <div className="mb-4">
        <h2 className="text-2xl mb-1" style={{ fontFamily: DISPLAY, color: C.text }}>Advisor</h2>
        <p className="text-sm" style={{ color: C.muted }}>Ask anything about your portfolio, a stock, or an investing idea. Answers are educational, not advice.</p>
      </div>

      {/* What the advisor can see */}
      <div className="rounded-xl p-3 mb-4 flex flex-wrap items-center gap-2 text-xs" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
        <span style={{ color: C.muted }}>Talking about:</span>
        <select value={savedPortfolioId ?? ''} onChange={e => onSavedPortfolioChange(e.target.value || null)}
          className="rounded-lg px-2 py-1.5 outline-none text-xs" style={{ backgroundColor: C.canvas, color: C.text, border: `1px solid ${C.border}` }}
          aria-label="Portfolio the advisor should use">
          <option value="">{dashboard ? `Portfolio on screen (${dashboard.stocks.map(s => s.ticker).join(', ')})` : 'No portfolio'}</option>
          {saved.map(p => <option key={p.id} value={p.id}>Saved: {p.portfolio_name}</option>)}
        </select>
      </div>

      {/* Conversation */}
      <div className="flex-1 space-y-4 mb-4" aria-live="polite">
        {messages.length === 0 && (
          <div className="rounded-2xl p-5 fade-up" style={{ backgroundColor: C.card, borderLeft: `3px solid ${C.pink}` }}>
            <div className="text-sm font-semibold mb-2" style={{ color: C.text }}>Try asking</div>
            <div className="flex flex-wrap gap-2">
              {suggestions.map(s => (
                <button key={s} onClick={() => send(s)} className="pressable text-left text-xs px-3 py-2 rounded-full"
                  style={{ color: C.text2, border: `1px solid ${C.border}`, backgroundColor: C.surface }}>{s}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} fade-up`}>
            <div className="max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-relaxed"
              style={m.role === 'user'
                ? { backgroundColor: `${C.cyan}1f`, color: C.text, border: `1px solid ${C.cyan}40` }
                : { backgroundColor: C.surface, color: C.text2, border: `1px solid ${C.border}` }}>
              {m.role === 'assistant' && m.tools && m.tools.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {[...new Set(m.tools)].map(t => (
                    <span key={t} className="text-[10px] px-2 py-0.5 rounded-full" style={{ color: C.violet, backgroundColor: `${C.violet}18` }}>
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
          <div className="flex gap-1 px-2" aria-label="Advisor is thinking">
            {[0, 1, 2].map(i => <span key={i} className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: C.pink, animationDelay: `${i * 0.2}s` }} />)}
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Composer */}
      <form onSubmit={e => { e.preventDefault(); send(input) }}
        className="sticky bottom-20 lg:bottom-4 flex gap-2 rounded-2xl p-2"
        style={{ backgroundColor: C.surface, border: `1px solid ${C.border}`, boxShadow: '0 12px 30px -12px rgba(0,0,0,0.6)' }}>
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask the advisor…" aria-label="Message"
          maxLength={2000} className="flex-1 bg-transparent px-3 py-2 text-sm outline-none" style={{ color: C.text }} />
        <button type="submit" disabled={busy || !input.trim()} className="pressable px-4 py-2 rounded-xl text-sm font-semibold disabled:opacity-40"
          style={{ backgroundColor: C.pink, color: C.canvas }}>Send</button>
      </form>
    </div>
  )
}
