import type { ReactNode } from 'react'
import { C } from '../../theme/tokens'

export function CyanBtn({ children, onClick, disabled, full }: { children: ReactNode; onClick?: () => void; disabled?: boolean; full?: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className={`${full ? 'w-full' : ''} cta px-6 py-3 rounded-xl text-base font-bold disabled:opacity-40`}
      style={{ backgroundColor: disabled ? C.border : C.cyan, color: C.canvas }}>
      {children}
    </button>
  )
}

/** The main action on a screen: large, centred, glowing. */
export function BigCta({ children, onClick, disabled, color = C.cyan }: { children: ReactNode; onClick?: () => void; disabled?: boolean; color?: string }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className="cta w-full sm:w-auto sm:min-w-[340px] px-10 py-5 rounded-2xl text-lg font-bold disabled:opacity-40 disabled:cursor-not-allowed"
      style={{ backgroundColor: disabled ? C.border : color, color: C.canvas, ['--glow' as string]: color }}>
      {children}
    </button>
  )
}

export function GhostBtn({ children, onClick }: { children: ReactNode; onClick?: () => void }) {
  return (
    <button onClick={onClick} className="pressable px-6 py-4 rounded-2xl text-base font-bold"
      style={{ color: C.text2, border: `2px solid ${C.border}`, backgroundColor: 'rgba(19,29,48,0.6)' }}>
      {children}
    </button>
  )
}

export function BackLink({ label = 'Back', onClick }: { label?: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className="pressable flex items-center gap-2 text-sm font-bold mb-8 fade-in"
      style={{ color: C.text2 }}>
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
      {label}
    </button>
  )
}
