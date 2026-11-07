import { C } from '../../theme/tokens'
import ParticleField from './ParticleField'

/**
 * The animated "instrument panel" background shared by every screen:
 * drifting grid, particle network, glow pools and slow orbit rings.
 * Fixed behind the content, ignores clicks.
 *   intensity="full"   login / onboarding / loading
 *   intensity="subtle" inside the app, so it never fights with data
 */
export default function LiveBackdrop({ intensity = 'full' }: { intensity?: 'full' | 'subtle' }) {
  const subtle = intensity === 'subtle'
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden" aria-hidden style={{ zIndex: 0, opacity: subtle ? 0.55 : 1 }}>
      <div className="absolute inset-0 grid-drift" />
      <ParticleField density={subtle ? 0.00005 : 0.00009} />
      <div className="absolute -top-40 -left-32 w-[560px] h-[560px] rounded-full breathe"
        style={{ background: `radial-gradient(circle, ${C.violet}33 0%, transparent 65%)` }} />
      <div className="absolute -bottom-48 -right-24 w-[600px] h-[600px] rounded-full breathe"
        style={{ background: `radial-gradient(circle, ${C.pink}2b 0%, transparent 65%)`, animationDelay: '2.5s' }} />
      <svg className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] max-w-none" viewBox="0 0 760 760">
        <defs>
          <filter id="bd-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" /></filter>
        </defs>
        <g className="orbit-slow" style={{ transformOrigin: '380px 380px' }}>
          <circle cx="380" cy="380" r="340" fill="none" stroke={C.cyan} strokeOpacity="0.14" strokeDasharray="2 10" />
          <circle cx="380" cy="40" r="4" fill={C.cyan} />
          <circle cx="380" cy="40" r="8" fill={C.cyan} filter="url(#bd-glow)" opacity="0.7" />
        </g>
        <g className="orbit-mid" style={{ transformOrigin: '380px 380px' }}>
          <circle cx="380" cy="380" r="270" fill="none" stroke={C.violet} strokeOpacity="0.2" />
          <path d="M 380 110 A 270 270 0 0 1 614 245" fill="none" stroke={C.pink} strokeWidth="2" strokeLinecap="round" />
          <path d="M 380 110 A 270 270 0 0 1 614 245" fill="none" stroke={C.pink} strokeWidth="6" strokeLinecap="round" filter="url(#bd-glow)" opacity="0.6" />
        </g>
        <g className="orbit-fast" style={{ transformOrigin: '380px 380px' }}>
          <circle cx="380" cy="380" r="205" fill="none" stroke={C.cyan} strokeOpacity="0.08" strokeDasharray="60 24" />
          <circle cx="585" cy="380" r="3" fill={C.violet} />
        </g>
      </svg>
    </div>
  )
}
