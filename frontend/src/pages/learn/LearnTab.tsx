import { C } from '../../theme/tokens'
import { LESSONS } from '../../data/lessons'
import LessonThumb from '../../components/charts/LessonThumb'

export default function LearnTab({ onLesson }: { onLesson: (id: number) => void }) {
  return (
    <div className="px-5 sm:px-8 py-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl mb-1 fade-up" style={{ fontFamily: "'DM Serif Display'", color: C.text }}>Learn how to —</h2>
        <p className="text-sm fade-up d1" style={{ color: C.muted }}>Short, plain-English explainers with annotated charts. No jargon, no assumed knowledge.</p>
      </div>
      <div className="grid sm:grid-cols-2 gap-3">
        {LESSONS.map((lesson, i) => (
          <button key={lesson.id} onClick={() => onLesson(lesson.id)}
            className={`text-left p-4 rounded-xl transition-all hover:border-cyan-500 group fade-up d${Math.min(i + 1, 7)}`}
            style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}>
            <div className="flex gap-3 items-start">
              <div className="mt-1 p-2 rounded-lg flex-shrink-0" style={{ backgroundColor: C.surface }}><LessonThumb id={lesson.id} /></div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold mb-1" style={{ color: C.muted }}>Lesson {lesson.id + 1}</div>
                <div className="text-sm font-semibold mb-1 leading-snug" style={{ color: C.text }}>Learn how to — {lesson.title.toLowerCase()}</div>
                <div className="text-xs leading-relaxed" style={{ color: C.muted }}>{lesson.subtitle}</div>
              </div>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style={{ color: C.muted, flexShrink: 0, marginTop: 4 }}><path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
