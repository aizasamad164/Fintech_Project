import { C } from '../../theme/tokens'

export default function TagChip({ label, color = C.muted }: { label: string; color?: string }) {
  return (
    <span className="on-fill-bg inline-flex items-center px-2.5 py-1 text-xs rounded-full font-bold"
      style={{ backgroundColor: `${color}22`, color, border: `1px solid ${color}55` }}>
      {label}
    </span>
  )
}
