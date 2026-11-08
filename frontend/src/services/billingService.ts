// StockSense Pro billing → /api/billing/*
import { api, USE_MOCK } from './api'
import { getUserId } from '../utils/userId'

export interface BillingStatus {
  is_pro: boolean
  status: string
  current_period_end: string | null
  cancel_at_period_end: boolean
  simulated: boolean
}
export interface BillingConfig { configured: boolean; auth_mode: 'supabase' | 'demo'; price: { amount_cents: number; currency: string; interval: string } }

export const STRIPE_PUBLISHABLE_KEY = (import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY as string | undefined)?.trim() || ''

const FREE: BillingStatus = { is_pro: false, status: 'none', current_period_end: null, cancel_at_period_end: false, simulated: false }
let mockStatus: BillingStatus = { ...FREE }

// In demo mode the backend identifies the user by ?user_id=; when signed in it uses the token instead.
const q = () => `?user_id=${getUserId()}`

export async function getBillingConfig(): Promise<BillingConfig> {
  if (USE_MOCK) return { configured: false, auth_mode: 'demo', price: { amount_cents: 900, currency: 'usd', interval: 'month' } }
  return api<BillingConfig>('/api/billing/config')
}

export async function getBillingStatus(): Promise<BillingStatus> {
  if (USE_MOCK) return mockStatus
  return api<BillingStatus>(`/api/billing/status${q()}`)
}

export async function startSubscription(): Promise<{ subscription_id: string; client_secret: string }> {
  return api(`/api/billing/subscribe${q()}`, { method: 'POST' })
}

export async function confirmSubscription(subscriptionId: string): Promise<BillingStatus> {
  return api<BillingStatus>(`/api/billing/confirm${q()}`, { method: 'POST', body: JSON.stringify({ subscription_id: subscriptionId }) })
}

export async function cancelSubscription(): Promise<BillingStatus> {
  if (USE_MOCK) { mockStatus = { ...mockStatus, status: 'canceled', is_pro: false }; return mockStatus }
  return api<BillingStatus>(`/api/billing/cancel${q()}`, { method: 'POST' })
}

/** Only works when Stripe isn't configured (local demos). Clearly labelled in the UI. */
export async function simulateUpgrade(): Promise<BillingStatus> {
  if (USE_MOCK) { mockStatus = { ...FREE, is_pro: true, status: 'active', simulated: true }; return mockStatus }
  return api<BillingStatus>(`/api/billing/demo-upgrade${q()}`, { method: 'POST' })
}

/** After paying, Stripe may take a moment to mark the invoice paid; ask a few times. */
export async function waitForPro(subscriptionId: string, tries = 6): Promise<BillingStatus> {
  let last = await confirmSubscription(subscriptionId)
  for (let i = 1; i < tries && !last.is_pro; i++) {
    await new Promise(r => setTimeout(r, 1200))
    last = await confirmSubscription(subscriptionId)
  }
  return last
}

// Remember the subscription across a 3-D Secure redirect
const PENDING = 'stocksense.pendingSubscription'
export const pending = {
  set(id: string) { try { sessionStorage.setItem(PENDING, id) } catch { /* ignore */ } },
  take(): string | null {
    try { const v = sessionStorage.getItem(PENDING); sessionStorage.removeItem(PENDING); return v } catch { return null }
  },
}
