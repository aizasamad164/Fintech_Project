import { useEffect, useRef } from 'react'
import { C } from '../../theme/tokens'
import LiveBackdrop from '../../components/effects/LiveBackdrop'

export default function ProSuccess({ onDone }: { onDone: () => void }) {
  const doneRef = useRef(onDone)
  doneRef.current = onDone
  useEffect(() => { const t = setTimeout(() => doneRef.current(), 3000); return () => clearTimeout(t) }, [])
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center px-5 text-center" style={{ backgroundColor: C.canvas }}>
      <LiveBackdrop />
      <div className="relative flex flex-col items-center" style={{ zIndex: 1 }}>
      <div className="w-20 h-20 rounded-full flex items-center justify-center mb-6 scale-up d1"
        style={{ background: 'linear-gradient(135deg, #F535AA 0%, #8B7FF0 50%, #4FD8E8 100%)' }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none"><path d="M5 12L10 17L19 8" stroke={C.canvas} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </div>
      <h2 className="text-4xl mb-3 fade-up d2" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>You're on Pro now</h2>
      <p className="text-lg font-semibold mb-6 fade-up d3" style={{ color: C.text2, maxWidth: 340 }}>Every sector is now unlocked. Taking you back now.</p>
      <div className="flex gap-1 fade-up d4">
        {[0, 1, 2].map(i => <div key={i} className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: C.cyan, animationDelay: `${i * 0.2}s` }} />)}
      </div>
      </div>
    </div>
  )
}
