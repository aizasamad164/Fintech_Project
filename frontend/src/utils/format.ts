export function fmt(n: number, compact = false) {
  if (compact && n >= 1000) return '$' + (n / 1000).toFixed(n < 10000 ? 1 : 0) + 'k'
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}
