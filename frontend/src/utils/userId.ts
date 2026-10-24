// Stable per-browser user id, used until real Supabase login is wired in.
// TODO (auth): replace with supabase.auth.getUser().id after sign-in.
const KEY = 'stocksense.userId'

function newId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

let memo: string | null = null

export function getUserId(): string {
  if (memo) return memo
  try {
    const existing = localStorage.getItem(KEY)
    memo = existing ?? newId()
    if (!existing) localStorage.setItem(KEY, memo)
  } catch {
    memo = newId()
  }
  return memo
}
