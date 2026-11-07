import type { ReactNode } from 'react'
import { C } from '../../theme/tokens'

// Small heading used above dashboard sections.
export default function SectionLabel({ children, className = '', ruled = false }: { children: ReactNode; className?: string; ruled?: boolean }) {
  return (
    <div className={`text-xs font-bold uppercase ${className}`}
      style={{ color: C.muted, letterSpacing: '0.09em', borderBottom: ruled ? `1px solid ${C.border}` : undefined }}>
      {children}
    </div>
  )
}
