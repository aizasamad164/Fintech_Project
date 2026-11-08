import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { authConfigured, supabase } from '../lib/supabaseClient'
import { setAccessToken } from '../services/api'
import { getDemoUserId, setSignedInUserId } from '../utils/userId'

export interface AppUser { id: string; email: string | null; demo: boolean }

interface AuthState {
  configured: boolean            // real accounts available
  loading: boolean               // still restoring a previous session
  user: AppUser | null
  recovering: boolean            // arrived from a "reset password" email link
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<{ needsConfirmation: boolean }>
  signInWithGoogle: () => Promise<void>
  sendPasswordReset: (email: string) => Promise<void>
  setNewPassword: (password: string) => Promise<void>
  continueAsDemo: () => void
  signOut: () => Promise<void>
}

const Ctx = createContext<AuthState | null>(null)

/** Turns Supabase's error messages into plain sentences. */
function friendly(message: string): string {
  const m = message.toLowerCase()
  if (m.includes('invalid login credentials')) return 'That email and password don\'t match an account.'
  if (m.includes('email not confirmed')) return 'Please confirm your email first. Check your inbox for the link.'
  if (m.includes('already registered') || m.includes('already been registered')) return 'An account with this email already exists. Sign in instead.'
  if (m.includes('password should be at least')) return 'Use a password of at least 8 characters.'
  if (m.includes('rate limit') || m.includes('too many')) return 'Too many attempts. Wait a minute and try again.'
  if (m.includes('failed to fetch') || m.includes('network')) return 'Can\'t reach the sign-in service. Check your internet connection.'
  return message
}

function fromSession(session: Session | null): AppUser | null {
  return session?.user ? { id: session.user.id, email: session.user.email ?? null, demo: false } : null
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null)
  const [loading, setLoading] = useState(authConfigured)
  const [recovering, setRecovering] = useState(false)

  const apply = useCallback((session: Session | null) => {
    setAccessToken(session?.access_token ?? null)
    setSignedInUserId(session?.user?.id ?? null)
    setUser(fromSession(session))
  }, [])

  useEffect(() => {
    if (!supabase) return
    supabase.auth.getSession().then(({ data }) => { apply(data.session); setLoading(false) })
    const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
      apply(session)                       // also fires on token refresh, keeping the API token fresh
      if (event === 'PASSWORD_RECOVERY') setRecovering(true)
    })
    return () => sub.subscription.unsubscribe()
  }, [apply])

  const value = useMemo<AuthState>(() => ({
    configured: authConfigured,
    loading,
    user,
    recovering,
    async signIn(email, password) {
      if (!supabase) throw new Error('Accounts are not set up on this computer.')
      const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password })
      if (error) throw new Error(friendly(error.message))
    },
    async signUp(email, password) {
      if (!supabase) throw new Error('Accounts are not set up on this computer.')
      const { data, error } = await supabase.auth.signUp({
        email: email.trim(), password, options: { emailRedirectTo: window.location.origin },
      })
      if (error) throw new Error(friendly(error.message))
      // With email confirmation on (Supabase's default), there is no session until the link is clicked.
      return { needsConfirmation: !data.session }
    },
    async signInWithGoogle() {
      if (!supabase) throw new Error('Accounts are not set up on this computer.')
      const { error } = await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: window.location.origin } })
      if (error) throw new Error(friendly(error.message))
    },
    async sendPasswordReset(email) {
      if (!supabase) throw new Error('Accounts are not set up on this computer.')
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), { redirectTo: window.location.origin })
      if (error) throw new Error(friendly(error.message))
    },
    async setNewPassword(password) {
      if (!supabase) throw new Error('Accounts are not set up on this computer.')
      const { error } = await supabase.auth.updateUser({ password })
      if (error) throw new Error(friendly(error.message))
      setRecovering(false)
    },
    continueAsDemo() {
      if (authConfigured) return          // never bypass real accounts
      setUser({ id: getDemoUserId(), email: null, demo: true })
    },
    async signOut() {
      if (supabase) await supabase.auth.signOut()
      apply(null)
    },
  }), [loading, user, recovering, apply])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
