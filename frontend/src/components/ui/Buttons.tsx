import type { ReactNode } from 'react'
import { C } from '../../theme/tokens'

export function CyanBtn({ children, onClick, disabled, full }: { children: ReactNode; onClick?: () => void; disabled?: boolean; full?: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className={`${full ? 'w-full' : ''} cta px-6 py-3 rounded-xl text-sm font-semibold disabled:opacity-40`}
      style={{ backgroundColor: disabled ? C.border : C.cyan, color: C.canvas }}>
      {children}
    </button>
  )
}

/** The main action on a screen: clearly visible, centred, restrained. */
export function BigCta({ children, onClick, disabled, color = C.cyan }: { children: ReactNode; onClick?: () => void; disabled?: boolean; color?: string }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className="cta w-full sm:w-auto sm:min-w-[280px] px-8 py-3.5 rounded-xl text-[0.95rem] font-semibold tracking-wide disabled:opacity-40 disabled:cursor-not-allowed"
      style={{ backgroundColor: disabled ? C.border : color, color: disabled ? C.muted : C.canvas, ['--glow' as string]: color }}>
      {children}
    </button>
  )
}

export function GhostBtn({ children, onClick }: { children: ReactNode; onClick?: () => void }) {
  return (
    <button onClick={onClick} className="pressable px-6 py-3.5 rounded-xl text-[0.95rem] font-semibold"
      style={{ color: C.text2, border: `1px solid ${C.border}`, backgroundColor: 'rgba(19,29,48,0.6)' }}>
      {children}
    </button>
  )
}

export function BackLink({ label = 'Back', onClick }: { label?: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className="pressable flex items-center gap-2 text-sm font-semibold mb-7 fade-in"
      style={{ color: C.text2 }}>
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
      {label}
    </button>
  )
}
