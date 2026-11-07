import type { ReactNode } from 'react'
import { C, HEADING } from '../../theme/tokens'
import LiveBackdrop from '../effects/LiveBackdrop'

// Same living background as the login screen, so the whole setup flow feels like one piece.
export default function OnboardShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-screen flex flex-col" style={{ backgroundColor: C.canvas }}>
      <LiveBackdrop />
      <div className="relative px-6 sm:px-10 py-5 flex items-center gap-3" style={{ zIndex: 1 }}>
        <span className="w-1.5 h-1.5 rounded-full breathe" style={{ backgroundColor: C.pink, boxShadow: `0 0 10px ${C.pink}` }} />
        <span className="text-base font-semibold" style={{ fontFamily: HEADING, color: C.text, letterSpacing: '-0.01em' }}>StockSense</span>
        <span className="text-[11px] font-semibold uppercase" style={{ color: C.muted, letterSpacing: '0.12em' }}>Educational</span>
      </div>
      <div className="relative flex-1 flex items-start justify-center px-5 pb-12 pt-4 sm:pt-8" style={{ zIndex: 1 }}>
        <div className="w-full max-w-3xl">{children}</div>
      </div>
    </div>
  )
}
