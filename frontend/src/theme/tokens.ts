// Single source of truth for colours used in inline styles and SVGs.
export const C = {
  canvas:  '#0D1420',
  surface: '#131D2E',
  card:    '#1A2640',
  border:  '#26314A',
  cyan:    '#4FD8E8',
  violet:  '#8B7FF0',
  amber:   '#F0A830',
  muted:   '#8793AC',
  text:    '#E8EDF5',
  text2:   '#C4CEDC',
  teal:    '#3CEDB0',
} as const

export const ORBIT_COLORS = [C.cyan, C.violet, C.teal, C.amber, '#CF7AE8'] as const

export const riskColor = (r: string) =>
  r === 'Conservative' ? C.teal : r === 'Balanced' ? C.cyan : C.amber
