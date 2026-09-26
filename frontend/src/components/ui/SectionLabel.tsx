import type { ReactNode } from 'react'
import { C } from '../../theme/tokens'

// Small uppercase heading used above dashboard sections.
export default function SectionLabel({ children, className = '', ruled = false }: { children: ReactNode; className?: string; ruled?: boolean }) {
  return (
    <div className={`text-xs font-semibold uppercase tracking-widest ${className}`}
      style={{ color: C.muted, fontFamily: 'Inter', letterSpacing: '0.08em', borderBottom: ruled ? `1px solid ${C.border}` : undefined }}>
      {children}
    </div>
  )
}
