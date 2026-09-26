import type { ReactNode } from 'react'
import { C } from '../../theme/tokens'

export function CyanBtn({ children, onClick, disabled, full }: { children: ReactNode; onClick?: () => void; disabled?: boolean; full?: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className={`${full ? 'w-full' : ''} px-6 py-3 rounded-lg text-sm font-semibold transition-all active:scale-[0.98] disabled:opacity-40`}
      style={{ backgroundColor: disabled ? C.border : C.cyan, color: C.canvas, fontFamily: 'Inter' }}>
      {children}
    </button>
  )
}

export function GhostBtn({ children, onClick }: { children: ReactNode; onClick?: () => void }) {
  return (
    <button onClick={onClick} className="px-5 py-3 rounded-lg text-sm font-medium transition-all hover:opacity-80"
      style={{ color: C.muted, border: `1px solid ${C.border}`, fontFamily: 'Inter' }}>
      {children}
    </button>
  )
}

export function BackLink({ label = 'Back', onClick }: { label?: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className="flex items-center gap-2 text-sm mb-8 transition-all hover:opacity-70 fade-in"
      style={{ color: C.muted, fontFamily: 'Inter' }}>
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
      {label}
    </button>
  )
}
