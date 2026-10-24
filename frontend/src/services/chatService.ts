// Advisor chat → POST /api/chat/message (Groq agent with tool calls)
import { api, USE_MOCK } from './api'
import { getUserId } from '../utils/userId'
import { SECTOR_TO_API } from './portfolioService'
import type { Portfolio } from '../types/portfolio'

export interface ChatReply { content: string; tools: string[]; status: string }

interface ChatContext { savedPortfolioId?: string | null; dashboard?: Portfolio | null }

export async function sendChat(sessionId: string, message: string, ctx: ChatContext): Promise<ChatReply> {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 600))
    return { status: 'mock', tools: [], content:
      'The advisor runs on the backend. Set **VITE_USE_MOCK=false** in `frontend/.env`, start the backend, and ask again.' }
  }
  const d = ctx.dashboard
  const res = await api<{ content: string; status: string; tools_used: { tool_name: string }[] }>('/api/chat/message', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      message,
      user_id: getUserId(),
      portfolio_id: ctx.savedPortfolioId ?? undefined,
      active_portfolio: !ctx.savedPortfolioId && d ? {
        portfolio_value: d.budget,
        risk_strategy: d.riskStrategy?.toLowerCase(),
        target_sector: d.sector ? SECTOR_TO_API[d.sector] : 'All',
        allocations: d.stocks.map(s => ({ ticker: s.ticker, weight_pct: s.allocation })),
      } : undefined,
    }),
  })
  return { content: res.content, status: res.status, tools: res.tools_used.map(t => t.tool_name) }
}
