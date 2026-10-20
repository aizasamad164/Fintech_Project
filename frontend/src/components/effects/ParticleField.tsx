import { useEffect, useRef } from 'react'

// Slowly drifting dots that link up with faint lines when they pass close by.
// Canvas-based so it stays smooth; pauses for reduced-motion users.
export default function ParticleField({ density = 0.00009 }: { density?: number }) {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const COLORS = ['79,216,232', '139,127,240', '245,53,170']
    type P = { x: number; y: number; vx: number; vy: number; r: number; c: string }
    let pts: P[] = [], w = 0, h = 0, raf = 0

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      w = canvas.clientWidth; h = canvas.clientHeight
      canvas.width = w * dpr; canvas.height = h * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      const n = Math.max(24, Math.min(110, Math.floor(w * h * density)))
      pts = Array.from({ length: n }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
        r: Math.random() * 1.4 + 0.4,
        c: COLORS[Math.random() < 0.15 ? 2 : Math.random() < 0.5 ? 1 : 0],
      }))
    }

    const draw = () => {
      ctx.clearRect(0, 0, w, h)
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i]
        if (!reduced) {
          p.x += p.vx; p.y += p.vy
          if (p.x < 0) p.x = w; if (p.x > w) p.x = 0
          if (p.y < 0) p.y = h; if (p.y > h) p.y = 0
        }
        for (let j = i + 1; j < pts.length; j++) {
          const q = pts[j], dx = p.x - q.x, dy = p.y - q.y, d2 = dx * dx + dy * dy
          if (d2 < 110 * 110) {
            ctx.strokeStyle = `rgba(79,216,232,${0.12 * (1 - Math.sqrt(d2) / 110)})`
            ctx.lineWidth = 0.6
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke()
          }
        }
        ctx.fillStyle = `rgba(${p.c},0.8)`
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill()
      }
      if (!reduced) raf = requestAnimationFrame(draw)
    }

    resize(); draw()
    window.addEventListener('resize', resize)
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize) }
  }, [density])

  return <canvas ref={ref} className="absolute inset-0 w-full h-full" aria-hidden />
}
