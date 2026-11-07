import { C } from '../../theme/tokens'
import { LESSONS } from '../../data/lessons'
import LessonThumb from '../../components/charts/LessonThumb'
import PageHeader from '../../components/ui/PageHeader'

const ACCENTS = [C.cyan, C.teal, C.violet, C.pink, '#B8F36B', '#7FB8FF']

export default function LearnTab({ onLesson }: { onLesson: (id: number) => void }) {
  return (
    <div className="px-4 sm:px-8 py-8 max-w-5xl mx-auto">
      <PageHeader title="Learn" subtitle="Short, plain-English lessons with annotated charts. No jargon, no assumed knowledge." />
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {LESSONS.map((lesson, i) => {
          const accent = ACCENTS[i % ACCENTS.length]
          return (
            <button key={lesson.id} onClick={() => onLesson(lesson.id)}
              className={`fill-hover glass text-left rounded-2xl p-5 flex flex-col fade-up d${Math.min(i + 1, 7)}`}
              style={{ ['--fill' as string]: accent, border: `2px solid ${C.border}` }}>
              <div className="on-fill-bg rounded-xl p-3 mb-4 self-start" style={{ backgroundColor: 'rgba(10,16,27,0.6)' }}><LessonThumb id={lesson.id} /></div>
              <div className="text-xs font-bold uppercase mb-1" style={{ color: accent, letterSpacing: '0.08em' }}>Lesson {lesson.id + 1}</div>
              <div className="text-lg font-bold mb-2 leading-snug" style={{ color: C.text }}>{lesson.title}</div>
              <div className="text-sm font-medium leading-relaxed flex-1" style={{ color: C.text2 }}>{lesson.subtitle}</div>
              <div className="text-sm font-bold mt-4" style={{ color: accent }}>Start lesson →</div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
