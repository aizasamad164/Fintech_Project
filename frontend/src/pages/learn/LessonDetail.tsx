import { C } from '../../theme/tokens'
import { LESSONS, LESSON_CONTENT } from '../../data/lessons'
import LessonHeroGraph from '../../components/charts/LessonHeroGraph'
import SectionLabel from '../../components/ui/SectionLabel'
import { BackLink } from '../../components/ui/Buttons'

export default function LessonDetail({ id, onBack, onNext }: { id: number; onBack: () => void; onNext: () => void }) {
  const lesson = LESSONS[id]
  const content = LESSON_CONTENT[id]
  const nextLesson = LESSONS[(id + 1) % LESSONS.length]
  return (
    <div className="px-5 sm:px-8 py-6 max-w-2xl mx-auto">
      <BackLink label="Back to lessons" onClick={onBack} />
      <SectionLabel className="mb-2 fade-up">Learn how to —</SectionLabel>
      <h1 className="text-3xl mb-2 fade-up d1" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>{lesson.title}</h1>
      <p className="text-sm mb-8 fade-up d2" style={{ color: C.muted, fontFamily: 'Inter' }}>{lesson.subtitle}</p>
      <div className="mb-8 p-4 rounded-xl fade-up d3" style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}>
        <LessonHeroGraph id={id} />
      </div>
      <div className="space-y-5 mb-10">
        {content.paras.map((p, i) => (
          <p key={i} className={`text-sm leading-relaxed fade-up d${i + 4}`} style={{ color: i === 0 ? C.text2 : C.muted, fontFamily: 'Inter' }}>{p}</p>
        ))}
      </div>
      <div className="p-4 rounded-xl fade-up d7" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
        <div className="text-xs mb-1" style={{ color: C.muted, fontFamily: 'Inter' }}>Up next</div>
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-sm font-semibold" style={{ color: C.text, fontFamily: 'Inter' }}>Learn how to — {nextLesson.title.toLowerCase()}</div>
            <div className="text-xs mt-0.5" style={{ color: C.muted, fontFamily: 'Inter' }}>{nextLesson.subtitle}</div>
          </div>
          <button onClick={onNext} className="px-4 py-2 rounded-lg text-sm font-semibold flex-shrink-0 transition-all hover:opacity-90"
            style={{ backgroundColor: C.cyan, color: C.canvas, fontFamily: 'Inter' }}>Next lesson</button>
        </div>
      </div>
    </div>
  )
}
