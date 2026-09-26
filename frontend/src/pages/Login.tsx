import { useState } from 'react'
import { C, DISPLAY } from '../theme/tokens'
import ParticleField from '../components/effects/ParticleField'

// TODO (backend): replace onLogin() with Supabase auth via src/lib/supabaseClient.ts
export default function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('')
  const [pw, setPw] = useState('')
  const field = (filled: string) => ({
    backgroundColor: 'rgba(13,20,32,0.7)',
    border: `1px solid ${filled ? C.pink : C.border}`,
    boxShadow: filled ? `0 0 0 3px ${C.pink}1f` : 'none',
    color: C.text,
  })

  return (
    <div className="relative min-h-screen overflow-hidden flex items-center justify-center px-5" style={{ backgroundColor: C.canvas }}>
      {/* ── Living backdrop ─────────────────────────────────────────── */}
      <div className="absolute inset-0 grid-drift" aria-hidden />
      <ParticleField />
      {/* Glow pools */}
      <div className="absolute -top-40 -left-32 w-[520px] h-[520px] rounded-full breathe pointer-events-none" aria-hidden
        style={{ background: `radial-gradient(circle, ${C.violet}33 0%, transparent 65%)` }} />
      <div className="absolute -bottom-48 -right-24 w-[560px] h-[560px] rounded-full breathe pointer-events-none" aria-hidden
        style={{ background: `radial-gradient(circle, ${C.pink}2b 0%, transparent 65%)`, animationDelay: '2.5s' }} />
      {/* Orbiting rings behind the form */}
      <svg className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[760px] max-w-none pointer-events-none" viewBox="0 0 760 760" aria-hidden>
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" /></filter>
        </defs>
        <g className="orbit-slow" style={{ transformOrigin: '380px 380px' }}>
          <circle cx="380" cy="380" r="340" fill="none" stroke={C.cyan} strokeOpacity="0.14" strokeDasharray="2 10" />
          <circle cx="380" cy="40" r="4" fill={C.cyan} />
          <circle cx="380" cy="40" r="8" fill={C.cyan} filter="url(#glow)" opacity="0.7" />
        </g>
        <g className="orbit-mid" style={{ transformOrigin: '380px 380px' }}>
          <circle cx="380" cy="380" r="270" fill="none" stroke={C.violet} strokeOpacity="0.2" />
          <path d="M 380 110 A 270 270 0 0 1 614 245" fill="none" stroke={C.pink} strokeWidth="2" strokeLinecap="round" />
          <path d="M 380 110 A 270 270 0 0 1 614 245" fill="none" stroke={C.pink} strokeWidth="6" strokeLinecap="round" filter="url(#glow)" opacity="0.6" />
        </g>
        <g className="orbit-fast" style={{ transformOrigin: '380px 380px' }}>
          <circle cx="380" cy="380" r="205" fill="none" stroke={C.cyan} strokeOpacity="0.08" strokeDasharray="60 24" />
          <circle cx="585" cy="380" r="3" fill={C.violet} />
        </g>
      </svg>

      {/* ── Form panel ──────────────────────────────────────────────── */}
      <div className="relative w-full max-w-sm scale-up">
        <div className="rounded-2xl p-7 sm:p-8"
          style={{
            backgroundColor: 'rgba(19,29,46,0.62)',
            backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)',
            border: `1px solid ${C.border}`,
            boxShadow: `0 30px 80px -20px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.04), 0 0 0 1px ${C.cyan}0d`,
          }}>
          <div className="mb-7 fade-up">
            <div className="flex items-center gap-2 mb-3">
              <span className="w-2 h-2 rounded-full breathe" style={{ backgroundColor: C.pink, boxShadow: `0 0 10px ${C.pink}` }} />
              <span className="text-[11px] font-medium" style={{ color: C.muted }}>Market data online</span>
            </div>
            <div className="text-4xl leading-none mb-2" style={{ fontFamily: DISPLAY, color: C.text }}>StockSense</div>
            <div className="text-sm" style={{ color: C.muted }}>Build a practice portfolio and learn why each pick is there.</div>
          </div>

          <button onClick={onLogin} className="pressable w-full flex items-center justify-center gap-3 py-3 rounded-lg text-sm font-medium mb-5 fade-up d1"
            style={{ border: `1px solid ${C.border}`, color: C.text2, backgroundColor: 'rgba(13,20,32,0.6)' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
            Continue with Google
          </button>

          <div className="flex items-center gap-3 mb-5 fade-up d2">
            <div className="flex-1 h-px" style={{ backgroundColor: C.border }} />
            <span className="text-xs" style={{ color: C.muted }}>or sign in with email</span>
            <div className="flex-1 h-px" style={{ backgroundColor: C.border }} />
          </div>

          <div className="space-y-3 mb-4 fade-up d3">
            <input type="email" placeholder="Email address" aria-label="Email address" value={email} onChange={e => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-all" style={field(email)} />
            <input type="password" placeholder="Password" aria-label="Password" value={pw} onChange={e => setPw(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && onLogin()}
              className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-all" style={field(pw)} />
          </div>

          <button onClick={onLogin} className="pressable w-full py-3 rounded-lg text-sm font-semibold fade-up d4"
            style={{ backgroundColor: C.cyan, color: C.canvas, boxShadow: `0 8px 24px -8px ${C.cyan}80` }}>
            Sign in
          </button>
          <p className="text-xs text-center mt-4 fade-up d5" style={{ color: C.muted }}>
            No account?{' '}<button className="underline" style={{ color: C.pink }} onClick={onLogin}>Create one free</button>
          </p>
        </div>
        <p className="text-xs text-center mt-6 fade-up d6" style={{ color: C.muted, opacity: 0.7 }}>For educational use only. No funds held, no trades executed.</p>
      </div>
    </div>
  )
}
