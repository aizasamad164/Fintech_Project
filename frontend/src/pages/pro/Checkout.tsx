import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, PaymentElement, useElements, useStripe } from '@stripe/react-stripe-js'
import { C, HEADING } from '../../theme/tokens'
import LiveBackdrop from '../../components/effects/LiveBackdrop'
import { BackLink } from '../../components/ui/Buttons'
import {
  STRIPE_PUBLISHABLE_KEY, getBillingConfig, pending, simulateUpgrade, startSubscription, waitForPro,
  type BillingConfig, type BillingStatus,
} from '../../services/billingService'

interface Props { onSuccess: (s: BillingStatus) => void; onBack: () => void }

// Load Stripe.js once (it comes from js.stripe.com, as Stripe requires)
const stripePromise = STRIPE_PUBLISHABLE_KEY ? loadStripe(STRIPE_PUBLISHABLE_KEY) : null

const appearance = {
  theme: 'night' as const,
  variables: {
    colorPrimary: C.cyan, colorBackground: '#0F1828', colorText: C.text, colorTextSecondary: C.muted,
    colorDanger: C.pink, borderRadius: '10px', fontFamily: 'Space Grotesk, system-ui, sans-serif', fontSizeBase: '15px',
  },
  rules: { '.Input': { border: `1px solid ${C.border}` }, '.Label': { fontWeight: '600' } },
}

function Summary({ cfg }: { cfg: BillingConfig | null }) {
  const amount = cfg ? (cfg.price.amount_cents / 100).toFixed(2) : '9.00'
  return (
    <div className="p-4 rounded-xl mb-6" style={{ backgroundColor: 'rgba(10,16,27,0.6)', border: `1px solid ${C.border}` }}>
      <div className="flex items-center justify-between">
        <div>
          <div className="text-base font-semibold" style={{ color: C.text }}>StockSense Pro</div>
          <div className="text-sm font-medium mt-0.5" style={{ color: C.muted }}>Monthly · cancel anytime</div>
        </div>
        <div className="text-xl" style={{ fontFamily: HEADING, fontWeight: 600, color: C.text }}>${amount}</div>
      </div>
    </div>
  )
}

/** The card form itself. Card details go from this form straight to Stripe. */
function PayForm({ subscriptionId, onSuccess }: { subscriptionId: string; onSuccess: (s: BillingStatus) => void }) {
  const stripe = useStripe()
  const elements = useElements()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const pay = async (e: FormEvent) => {
    e.preventDefault()
    if (!stripe || !elements) return
    setBusy(true); setError(null)
    pending.set(subscriptionId)   // in case the bank sends the user to a 3-D Secure page and back
    const { error: payError } = await stripe.confirmPayment({
      elements, redirect: 'if_required', confirmParams: { return_url: window.location.origin },
    })
    if (payError) { setError(payError.message ?? 'The payment did not go through.'); setBusy(false); return }
    try {
      const status = await waitForPro(subscriptionId)
      pending.take()
      if (status.is_pro) onSuccess(status)
      else setError('Payment received, but Pro is not active yet. Refresh in a minute.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not confirm the subscription.')
    } finally { setBusy(false) }
  }

  return (
    <form onSubmit={pay} className="space-y-5">
      <PaymentElement options={{ layout: 'tabs' }} />
      {error && <p className="text-sm font-semibold" style={{ color: C.pink }} role="alert">{error}</p>}
      <button type="submit" disabled={!stripe || busy} className="cta w-full py-3.5 rounded-xl text-[0.95rem] font-semibold disabled:opacity-60"
        style={{ backgroundColor: C.cyan, color: C.canvas }}>
        {busy ? 'Processing…' : 'Pay $9.00 and upgrade'}
      </button>
    </form>
  )
}

export default function Checkout({ onSuccess, onBack }: Props) {
  const [cfg, setCfg] = useState<BillingConfig | null>(null)
  const [sub, setSub] = useState<{ subscription_id: string; client_secret: string } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const live = Boolean(cfg?.configured && stripePromise)
  useEffect(() => { getBillingConfig().then(setCfg).catch(e => setError(e.message)) }, [])
  useEffect(() => {
    if (!live || sub) return
    startSubscription().then(setSub).catch(e => setError(e.message))
  }, [live, sub])

  const options = useMemo(() => (sub ? { clientSecret: sub.client_secret, appearance } : undefined), [sub])

  const simulate = async () => {
    setBusy(true); setError(null)
    try { onSuccess(await simulateUpgrade()) } catch (e) { setError(e instanceof Error ? e.message : 'Could not upgrade.') } finally { setBusy(false) }
  }

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center px-5 py-12" style={{ backgroundColor: C.canvas }}>
      <LiveBackdrop />
      <div className="relative w-full max-w-md glass rounded-2xl p-7" style={{ zIndex: 1, border: `1px solid ${C.border}` }}>
        <BackLink onClick={onBack} />
        <h1 className="text-2xl mb-5" style={{ fontFamily: HEADING, fontWeight: 600, letterSpacing: '-0.02em', color: C.text }}>Upgrade to Pro</h1>
        <Summary cfg={cfg} />

        {!cfg && !error && <div className="h-40 rounded-xl animate-pulse" style={{ backgroundColor: C.card }} aria-label="Loading" />}

        {cfg && live && !sub && !error && <div className="h-56 rounded-xl animate-pulse" style={{ backgroundColor: C.card }} aria-label="Preparing secure card form" />}
        {cfg && live && sub && options && (
          <Elements stripe={stripePromise} options={options}>
            <PayForm subscriptionId={sub.subscription_id} onSuccess={onSuccess} />
          </Elements>
        )}

        {cfg && !live && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl text-sm font-medium leading-relaxed" style={{ backgroundColor: '#F0B43C14', border: '1px solid #F0B43C55', color: C.text2 }}>
              Payments aren't set up on this computer.{' '}
              {!cfg.configured ? <>Add <code style={{ color: C.cyan }}>STRIPE_SECRET_KEY</code> to <code>backend/.env</code></> : null}
              {!cfg.configured && !STRIPE_PUBLISHABLE_KEY ? ' and ' : null}
              {!STRIPE_PUBLISHABLE_KEY ? <><code style={{ color: C.cyan }}>VITE_STRIPE_PUBLISHABLE_KEY</code> to <code>frontend/.env</code></> : null}
              {' '}to take test card payments.
            </div>
            {!cfg.configured && (
              <button onClick={simulate} disabled={busy} className="pressable w-full py-3 rounded-xl text-sm font-semibold disabled:opacity-60"
                style={{ border: `1px solid ${C.border}`, color: C.text2, backgroundColor: 'rgba(10,16,27,0.6)' }}>
                {busy ? 'Upgrading…' : 'Simulate the upgrade (demo, no payment)'}
              </button>
            )}
          </div>
        )}

        {error && <p className="text-sm font-semibold mt-4" style={{ color: C.pink }} role="alert">{error}</p>}

        <div className="flex items-center justify-center gap-2 mt-6">
          <svg width="12" height="12" viewBox="0 0 12 14" fill="none" aria-hidden><rect x="2" y="5" width="8" height="8" rx="1.5" stroke={C.muted} strokeWidth="1.2" /><path d="M4 5V4a2 2 0 014 0v1" stroke={C.muted} strokeWidth="1.2" /></svg>
          <span className="text-xs font-medium" style={{ color: C.muted }}>
            {live ? 'Secured by Stripe. Test mode: use card 4242 4242 4242 4242, any future date, any CVC.' : 'No card details are collected in demo mode.'}
          </span>
        </div>
      </div>
    </div>
  )
}
