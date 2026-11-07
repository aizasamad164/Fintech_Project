import type { ReactNode } from 'react'
import { C, HEADING } from '../../theme/tokens'

/** Same title treatment on every tab except the dashboard. */
export default function PageHeader({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 mb-7 fade-up">
      <div>
        <h1 className="text-3xl font-semibold" style={{ fontFamily: HEADING, color: C.text, letterSpacing: '-0.02em' }}>{title}</h1>
        {subtitle && <p className="text-[0.95rem] font-medium mt-1.5 max-w-2xl" style={{ color: C.muted }}>{subtitle}</p>}
      </div>
      {right}
    </div>
  )
}
