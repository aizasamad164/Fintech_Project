// Single source of truth for colours used in inline styles and SVGs.
// Contrast was raised across the board: darker canvas, brighter text and
// secondary text, and visible borders, so everything reads clearly.
export const C = {
  canvas:  '#0A101B',
  surface: '#131D30',
  card:    '#1A2741',
  border:  '#2F3D5C',
  cyan:    '#4FD8E8',
  violet:  '#9A8FFF',
  pink:    '#F535AA', // highlight: aggressive risk, Pro, key actions
  muted:   '#AAB5CB',
  text:    '#F5F8FC',
  text2:   '#DCE3EE',
  teal:    '#3CEDB0', // conservative / gains
} as const

export const DISPLAY = "'DM Serif Display', Georgia, serif"

export const ORBIT_COLORS = [C.cyan, C.pink, C.violet, C.teal, '#FF8FD0', '#7FB8FF'] as const

/** Strategy colours: Conservative = green, Balanced = cyan, Aggressive = pink */
export const riskColor = (r: string) =>
  r.toLowerCase() === 'conservative' ? C.teal : r.toLowerCase() === 'balanced' ? C.cyan : C.pink
