import type { ReactNode } from 'react'
import { C, DISPLAY } from '../../theme/tokens'

/** Same title treatment on every tab. */
export default function PageHeader({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 mb-8 fade-up">
      <div>
        <h1 className="leading-tight" style={{ fontFamily: DISPLAY, color: C.text, fontSize: 'clamp(2.2rem, 5vw, 3rem)' }}>{title}</h1>
        {subtitle && <p className="text-base sm:text-lg font-semibold mt-1 max-w-2xl" style={{ color: C.text2 }}>{subtitle}</p>}
      </div>
      {right}
    </div>
  )
}
