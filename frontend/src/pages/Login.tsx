import { useState, type FormEvent } from 'react'
import { C, HEADING } from '../theme/tokens'
import LiveBackdrop from '../components/effects/LiveBackdrop'
import { useAuth } from '../auth/AuthProvider'

type Mode = 'signin' | 'signup' | 'reset'
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
)

/** Sign in, create an account, reset a password, or set a new one after a reset email. */
export default function Login() {
  const auth = useAuth()
  const [mode, setMode] = useState<Mode>('signin')
  const [email, setEmail] = useState('')
  const [pw, setPw] = useState('')
  const [pw2, setPw2] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const field = (filled: boolean, bad = false) => ({
    backgroundColor: 'rgba(10,16,27,0.7)',
    border: `1px solid ${bad ? C.pink : filled ? C.cyan : C.border}`,
    color: C.text,
  })

  const switchMode = (m: Mode) => { setMode(m); setError(null); setNotice(null); setPw(''); setPw2('') }

  const run = async (fn: () => Promise<void>) => {
    setBusy(true); setError(null); setNotice(null)
    try { await fn() } catch (e) { setError(e instanceof Error ? e.message : 'Something went wrong.') } finally { setBusy(false) }
  }

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (auth.recovering) {
      if (pw.length < 8) return setError('Use a password of at least 8 characters.')
      if (pw !== pw2) return setError('The two passwords don\'t match.')
      return run(async () => { await auth.setNewPassword(pw); setNotice('Password updated. You\'re signed in.') })
    }
    if (!EMAIL_RE.test(email.trim())) return setError('Enter a valid email address.')
    if (mode === 'reset') {
      return run(async () => { await auth.sendPasswordReset(email); setNotice('If that email has an account, a reset link is on its way.') })
    }
    if (pw.length < 8) return setError('Passwords are at least 8 characters.')
    if (mode === 'signup') {
      if (pw !== pw2) return setError('The two passwords don\'t match.')
      return run(async () => {
        const { needsConfirmation } = await auth.signUp(email, pw)
        if (needsConfirmation) { setNotice(`Almost done: we sent a confirmation link to ${email.trim()}. Open it, then sign in.`); setMode('signin'); setPw(''); setPw2('') }
      })
    }
    return run(() => auth.signIn(email, pw))
  }

  const title = auth.recovering ? 'Choose a new password' : mode === 'signup' ? 'Create your account' : mode === 'reset' ? 'Reset your password' : 'Welcome back'
  const cta = auth.recovering ? 'Save new password' : mode === 'signup' ? 'Create account' : mode === 'reset' ? 'Send reset link' : 'Sign in'

  return (
    <div className="relative min-h-screen overflow-hidden flex items-center justify-center px-5 py-10" style={{ backgroundColor: C.canvas }}>
      <LiveBackdrop />

      <div className="relative w-full max-w-sm scale-up" style={{ zIndex: 1 }}>
        <div className="glass rounded-2xl p-7 sm:p-8"
          style={{ border: `1px solid ${C.border}`, boxShadow: `0 30px 80px -20px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.04)` }}>
          <div className="mb-6">
            <div className="text-2xl mb-1" style={{ fontFamily: HEADING, fontWeight: 600, letterSpacing: '-0.025em', color: C.text }}>StockSense</div>
            <div className="text-base font-semibold" style={{ color: C.text2 }}>{title}</div>
          </div>

          {!auth.configured ? (
            /* Teammate running without Supabase keys */
            <div className="space-y-4">
              <p className="text-sm font-medium leading-relaxed" style={{ color: C.text2 }}>
                Accounts aren't set up on this computer yet. Add <code style={{ color: C.cyan }}>VITE_SUPABASE_URL</code> and{' '}
                <code style={{ color: C.cyan }}>VITE_SUPABASE_ANON_KEY</code> to <code>frontend/.env</code> to turn on sign-up and login.
              </p>
              <button onClick={auth.continueAsDemo} className="cta w-full py-3 rounded-xl text-sm font-semibold" style={{ backgroundColor: C.cyan, color: C.canvas }}>
                Continue in demo mode
              </button>
              <p className="text-xs font-medium" style={{ color: C.muted }}>Demo mode keeps your saved portfolios in this browser only.</p>
            </div>
          ) : (
            <>
              {!auth.recovering && mode !== 'reset' && (
                <>
                  <button type="button" onClick={() => run(auth.signInWithGoogle)} disabled={busy}
                    className="pressable w-full flex items-center justify-center gap-3 py-3 rounded-xl text-sm font-semibold mb-5 disabled:opacity-60"
                    style={{ border: `1px solid ${C.border}`, color: C.text, backgroundColor: 'rgba(10,16,27,0.6)' }}>
                    <GoogleIcon /> Continue with Google
                  </button>
                  <div className="flex items-center gap-3 mb-5">
                    <div className="flex-1 h-px" style={{ backgroundColor: C.border }} />
                    <span className="text-xs font-semibold" style={{ color: C.muted }}>or with email</span>
                    <div className="flex-1 h-px" style={{ backgroundColor: C.border }} />
                  </div>
                </>
              )}

              <form onSubmit={submit} noValidate className="space-y-3">
                {!auth.recovering && (
                  <input type="email" autoComplete="email" placeholder="Email address" aria-label="Email address" value={email}
                    onChange={e => setEmail(e.target.value)} className="w-full px-4 py-3 rounded-xl text-sm font-medium outline-none transition-all" style={field(!!email)} />
                )}
                {mode !== 'reset' || auth.recovering ? (
                  <input type="password" autoComplete={mode === 'signin' && !auth.recovering ? 'current-password' : 'new-password'}
                    placeholder={auth.recovering ? 'New password' : 'Password'} aria-label="Password" value={pw}
                    onChange={e => setPw(e.target.value)} className="w-full px-4 py-3 rounded-xl text-sm font-medium outline-none transition-all" style={field(!!pw)} />
                ) : null}
                {(mode === 'signup' || auth.recovering) && (
                  <input type="password" autoComplete="new-password" placeholder="Confirm password" aria-label="Confirm password" value={pw2}
                    onChange={e => setPw2(e.target.value)} className="w-full px-4 py-3 rounded-xl text-sm font-medium outline-none transition-all"
                    style={field(!!pw2, !!pw2 && pw2 !== pw)} />
                )}
                {mode === 'signup' && <p className="text-xs font-medium" style={{ color: C.muted }}>At least 8 characters.</p>}

                {error && <p className="text-sm font-semibold" style={{ color: C.pink }} role="alert">{error}</p>}
                {notice && <p className="text-sm font-semibold" style={{ color: C.teal }} role="status">{notice}</p>}

                <button type="submit" disabled={busy} className="cta w-full py-3 rounded-xl text-sm font-semibold disabled:opacity-60"
                  style={{ backgroundColor: C.cyan, color: C.canvas }}>
                  {busy ? 'Please wait…' : cta}
                </button>
              </form>

              {!auth.recovering && (
                <div className="flex items-center justify-between mt-4 text-xs font-semibold">
                  {mode === 'signin'
                    ? <button onClick={() => switchMode('reset')} style={{ color: C.muted }} className="hover:underline">Forgot password?</button>
                    : <button onClick={() => switchMode('signin')} style={{ color: C.muted }} className="hover:underline">Back to sign in</button>}
                  {mode !== 'signup'
                    ? <button onClick={() => switchMode('signup')} style={{ color: C.pink }} className="hover:underline">Create an account</button>
                    : <span style={{ color: C.muted }}>Have an account? <button onClick={() => switchMode('signin')} style={{ color: C.pink }} className="hover:underline">Sign in</button></span>}
                </div>
              )}
            </>
          )}
        </div>
        <p className="text-xs text-center mt-6 font-medium" style={{ color: C.muted, opacity: 0.8 }}>For educational use only. No funds held, no trades executed.</p>
      </div>
    </div>
  )
}
