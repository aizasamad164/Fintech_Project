import type { ReactNode } from 'react'
import { C } from '../../theme/tokens'

export default function OnboardShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: C.canvas }}>
      <div className="px-6 py-5 flex items-center gap-2" style={{ borderBottom: `1px solid ${C.border}` }}>
        <span className="text-base font-semibold" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>StockSense</span>
        <span className="text-xs" style={{ color: C.muted, fontFamily: 'Inter' }}>— educational only</span>
      </div>
      <div className="flex-1 flex items-start justify-center px-5 py-10 sm:py-16">
        <div className="w-full max-w-xl">{children}</div>
      </div>
    </div>
  )
}
