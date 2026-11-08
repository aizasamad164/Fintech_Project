// The id saved portfolios belong to.
// Signed in: the Supabase user id (set by AuthProvider).
// Demo mode (no Supabase configured): a random id kept in this browser.
const KEY = 'stocksense.userId'

function newId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

let signedInId: string | null = null
let demoId: string | null = null

export function setSignedInUserId(id: string | null) { signedInId = id }

export function getDemoUserId(): string {
  if (demoId) return demoId
  try {
    const existing = localStorage.getItem(KEY)
    demoId = existing ?? newId()
    if (!existing) localStorage.setItem(KEY, demoId)
  } catch {
    demoId = newId()
  }
  return demoId
}

export function getUserId(): string {
  return signedInId ?? getDemoUserId()
}
