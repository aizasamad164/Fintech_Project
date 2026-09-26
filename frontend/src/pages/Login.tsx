import { useState } from 'react'
import { C } from '../theme/tokens'

// TODO (backend): replace onLogin() with Supabase auth via src/lib/supabaseClient.ts
export default function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('')
  const [pw, setPw] = useState('')
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-5" style={{ backgroundColor: C.canvas }}>
      <div className="w-full max-w-sm">
        <div className="text-center mb-8 fade-up">
          <div className="text-3xl mb-1" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>StockSense</div>
          <div className="text-sm" style={{ color: C.muted, fontFamily: 'Inter' }}>Educational stock portfolio builder</div>
        </div>
        <button onClick={onLogin} className="w-full flex items-center justify-center gap-3 py-3 rounded-lg text-sm font-medium mb-5 transition-all hover:opacity-90 fade-up d1"
          style={{ border: `1px solid ${C.border}`, color: C.text2, fontFamily: 'Inter', backgroundColor: C.surface }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
          Continue with Google
        </button>
        <div className="flex items-center gap-3 mb-5 fade-up d2">
          <div className="flex-1 h-px" style={{ backgroundColor: C.border }} />
          <span className="text-xs" style={{ color: C.muted, fontFamily: 'Inter' }}>or sign in with email</span>
          <div className="flex-1 h-px" style={{ backgroundColor: C.border }} />
        </div>
        <div className="space-y-3 mb-4 fade-up d3">
          <input type="email" placeholder="Email address" value={email} onChange={e => setEmail(e.target.value)} className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-all"
            style={{ backgroundColor: C.surface, border: `1px solid ${email ? C.violet : C.border}`, color: C.text, fontFamily: 'Inter' }} />
          <input type="password" placeholder="Password" value={pw} onChange={e => setPw(e.target.value)} onKeyDown={e => e.key === 'Enter' && onLogin()} className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-all"
            style={{ backgroundColor: C.surface, border: `1px solid ${pw ? C.violet : C.border}`, color: C.text, fontFamily: 'Inter' }} />
        </div>
        <button onClick={onLogin} className="w-full py-3 rounded-lg text-sm font-semibold transition-all hover:opacity-90 active:scale-[0.98] fade-up d4"
          style={{ backgroundColor: C.cyan, color: C.canvas, fontFamily: 'Inter' }}>Sign in</button>
        <p className="text-xs text-center mt-4 fade-up d5" style={{ color: C.muted, fontFamily: 'Inter' }}>
          No account?{' '}<button className="underline" style={{ color: C.cyan }} onClick={onLogin}>Create one free</button>
        </p>
        <p className="text-xs text-center mt-8 fade-up d6" style={{ color: C.border, fontFamily: 'Inter' }}>For educational use only. No funds held, no trades executed.</p>
      </div>
    </div>
  )
}
