import { C } from '../../theme/tokens'

export default function TagChip({ label, color = C.muted }: { label: string; color?: string }) {
  return (
    <span className="inline-flex items-center px-2.5 py-1 text-xs rounded-full font-medium"
      style={{ backgroundColor: `${color}18`, color, border: `1px solid ${color}30` }}>
      {label}
    </span>
  )
}
