// Shared backend helper. Every service goes through here.
export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
export const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    })
  } catch {
    throw new Error(`Can't reach the backend at ${API_BASE}. Is it running?`)
  }
  if (!res.ok) {
    let detail = `${res.status}`
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body)
    } catch { /* not JSON */ }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}
