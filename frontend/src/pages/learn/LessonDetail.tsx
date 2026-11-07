import { C, HEADING } from '../../theme/tokens'
import { LESSONS, LESSON_CONTENT } from '../../data/lessons'
import LessonHeroGraph from '../../components/charts/LessonHeroGraph'
import { BackLink } from '../../components/ui/Buttons'

const ACCENTS = [C.cyan, C.teal, C.violet, C.pink, '#B8F36B', '#7FB8FF']

export default function LessonDetail({ id, onBack, onNext }: { id: number; onBack: () => void; onNext: () => void }) {
  const lesson = LESSONS[id]
  const content = LESSON_CONTENT[id]
  const nextLesson = LESSONS[(id + 1) % LESSONS.length]
  const accent = ACCENTS[id % ACCENTS.length]
  return (
    <div className="px-4 sm:px-8 py-8 max-w-3xl mx-auto">
      <BackLink label="Back to lessons" onClick={onBack} />
      <div className="text-sm font-bold uppercase mb-2 fade-up" style={{ color: accent, letterSpacing: '0.09em' }}>Lesson {id + 1}</div>
      <h1 className="leading-tight mb-3 fade-up d1" style={{ fontFamily: HEADING, fontWeight: 600, letterSpacing: '-0.025em', color: C.text, fontSize: 'clamp(1.75rem, 3.2vw, 2.25rem)' }}>{lesson.title}</h1>
      <p className="text-lg font-semibold mb-8 fade-up d2" style={{ color: C.text2 }}>{lesson.subtitle}</p>
      <div className="glass mb-8 p-5 rounded-2xl fade-up d3" style={{ border: `2px solid ${accent}55`, boxShadow: `0 24px 60px -30px ${accent}` }}>
        <LessonHeroGraph id={id} />
      </div>
      <div className="space-y-6 mb-10">
        {content.paras.map((p, i) => (
          <p key={i} className={`text-lg leading-relaxed fade-up d${i + 4}`} style={{ color: i === 0 ? C.text : C.text2, fontWeight: i === 0 ? 600 : 500 }}>{p}</p>
        ))}
      </div>
      <button onClick={onNext} className={`tint-fill glass w-full text-left rounded-2xl p-5 flex items-center justify-between gap-4 fade-up d7`}
        style={{ ['--fill' as string]: ACCENTS[(id + 1) % ACCENTS.length], border: `2px solid ${C.border}` }}>
        <div>
          <div className="text-sm font-bold mb-1" style={{ color: C.muted }}>Up next</div>
          <div className="text-base font-semibold" style={{ color: C.text }}>{nextLesson.title}</div>
          <div className="text-sm font-semibold mt-0.5" style={{ color: C.text2 }}>{nextLesson.subtitle}</div>
        </div>
        <span className="text-base font-bold flex-shrink-0" style={{ color: C.text }}>Next →</span>
      </button>
    </div>
  )
}
