import { useEffect, useRef } from 'react'
import { C } from '../../theme/tokens'

export default function ProSuccess({ onDone }: { onDone: () => void }) {
  const doneRef = useRef(onDone)
  doneRef.current = onDone
  useEffect(() => { const t = setTimeout(() => doneRef.current(), 3000); return () => clearTimeout(t) }, [])
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-5 text-center" style={{ backgroundColor: C.canvas }}>
      <div className="w-16 h-16 rounded-full flex items-center justify-center mb-6 scale-up d1"
        style={{ background: 'linear-gradient(135deg, #8B7FF0 0%, #4FD8E8 100%)' }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none"><path d="M5 12L10 17L19 8" stroke={C.canvas} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </div>
      <h2 className="text-3xl mb-2 fade-up d2" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>You're on Pro now</h2>
      <p className="text-sm mb-6 fade-up d3" style={{ color: C.muted, fontFamily: 'Inter', maxWidth: 280 }}>All four sectors are now unlocked in Insights. Taking you there now.</p>
      <div className="flex gap-1 fade-up d4">
        {[0, 1, 2].map(i => <div key={i} className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: C.cyan, animationDelay: `${i * 0.2}s` }} />)}
      </div>
    </div>
  )
}
