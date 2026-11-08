import { createClient, type SupabaseClient } from '@supabase/supabase-js'

// NFR-2.1: only the public anon key is used client-side, never the service role key.
const url = (import.meta.env.VITE_SUPABASE_URL as string | undefined)?.trim()
const anonKey = (import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined)?.trim()

/** True when real accounts are available (frontend/.env has the Supabase URL and anon key). */
export const authConfigured = Boolean(url && anonKey && !url.includes('your-project') && anonKey !== 'replace-me')

export const supabase: SupabaseClient | null = authConfigured
  ? createClient(url!, anonKey!, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } })
  : null
