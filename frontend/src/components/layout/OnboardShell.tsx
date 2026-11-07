import type { ReactNode } from 'react'
import { C, DISPLAY } from '../../theme/tokens'
import LiveBackdrop from '../effects/LiveBackdrop'

// Same living background as the login screen, so the whole setup flow feels like one piece.
export default function OnboardShell({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return (
    <div className="relative min-h-screen flex flex-col" style={{ backgroundColor: C.canvas }}>
      <LiveBackdrop />
      <div className="relative px-6 py-5 flex items-center gap-3" style={{ zIndex: 1 }}>
        <span className="w-2 h-2 rounded-full breathe" style={{ backgroundColor: C.pink, boxShadow: `0 0 10px ${C.pink}` }} />
        <span className="text-xl" style={{ fontFamily: DISPLAY, color: C.text }}>StockSense</span>
        <span className="text-xs font-semibold" style={{ color: C.muted }}>Educational only</span>
      </div>
      <div className="relative flex-1 flex items-start justify-center px-5 pb-12 pt-4 sm:pt-10" style={{ zIndex: 1 }}>
        <div className={`w-full ${wide ? 'max-w-3xl' : 'max-w-2xl'}`}>{children}</div>
      </div>
    </div>
  )
}
