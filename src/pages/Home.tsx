import { questions, weights, SUBJECT_ORDER, SUBJECT_NAMES } from '../lib/content'
import { useProgress } from '../lib/store'
import { isDue } from '../lib/srs'

export default function Home({ nav }: { nav: (to: string) => void }) {
  const p = useProgress()
  const now = Date.now()

  const learned = questions.filter((q) => p.srs[q.id]).length
  const dueNow = questions.filter((q) => p.srs[q.id] && isDue(p.srs[q.id], now)).length
  const fresh = questions.length - learned
  const mistakes = Object.values(p.flags).filter((f) => (f.mistake ?? 0) > 0).length
  const lastExam = p.exams[p.exams.length - 1]

  const perSubject = SUBJECT_ORDER.map((id) => {
    const all = questions.filter((q) => q.subject === id)
    const done = all.filter((q) => p.srs[q.id]).length
    const right = all.filter((q) => p.answers[q.id]?.correct).length
    const answered = all.filter((q) => p.answers[q.id]).length
    return { id, total: all.length, done, right, answered }
  }).filter((s) => s.total > 0)

  return (
    <>
      <div className="card" style={{ padding: 18 }}>
        <div className="row">
          <div>
            <div className="muted small">今日待做</div>
            <div style={{ fontSize: 34, fontWeight: 750, color: 'var(--primary-ink)', lineHeight: 1.2 }}>
              {dueNow + fresh}
              <span className="small muted" style={{ fontWeight: 500 }}> 题</span>
            </div>
            <div className="muted tiny">到期复习 {dueNow} · 新题 {fresh}</div>
          </div>
          <div className="spacer" />
          <div className="stat">
            <b>{p.streak.days}</b>
            <span>连续天数</span>
          </div>
        </div>
        <button className="btn primary wide" style={{ marginTop: 14 }} onClick={() => nav('practice')}>
          开始刷题
        </button>
      </div>

      <div className="grid2">
        <button className="card item" onClick={() => nav('exam')} style={{ display: 'block' }}>
          <div className="title">模拟考试</div>
          <div className="sub">16 单选 + 17 多选</div>
        </button>
        <button className="card item" onClick={() => nav('practice/mistakes')} style={{ display: 'block' }}>
          <div className="title">错题本</div>
          <div className="sub">{mistakes} 道待巩固</div>
        </button>
        <button className="card item" onClick={() => nav('theory/keywords')} style={{ display: 'block' }}>
          <div className="title">提法速查</div>
          <div className="sub">根本 · 本质 · 前提</div>
        </button>
        <button className="card item" onClick={() => nav('timeline')} style={{ display: 'block' }}>
          <div className="title">时间轴</div>
          <div className="sub">史纲主线与重要会议</div>
        </button>
      </div>

      <div className="card">
        <h2>学科掌握度</h2>
        {perSubject.length === 0 ? (
          <div className="empty">题库尚未生成</div>
        ) : (
          <div className="stack">
            {perSubject.map((s) => {
              const pct = s.total ? Math.round((s.done / s.total) * 100) : 0
              const acc = s.answered ? Math.round((s.right / s.answered) * 100) : null
              return (
                <div key={s.id}>
                  <div className="subject-name">{SUBJECT_NAMES[s.id].name}</div>
                  <div className="row tiny muted" style={{ marginTop: 3 }}>
                    <span>选择 {weights[s.id].score} 分</span>
                    <span>·</span>
                    <span>
                      {s.done}/{s.total}
                    </span>
                    <span className="spacer" />
                    <span>{acc !== null ? `正确率 ${acc}%` : '未开始'}</span>
                  </div>
                  <div className="meter" style={{ marginTop: 6 }}>
                    <i style={{ width: `${pct}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <div className="card">
        <h2>最近模考</h2>
        {lastExam ? (
          <div className="row">
            <div className="stat">
              <b>{lastExam.score}</b>
              <span>总分 / {lastExam.max ?? 50}</span>
            </div>
            <div className="stat">
              <b>{lastExam.single}</b>
              <span>单选 / 16</span>
            </div>
            <div className="stat">
              <b>{lastExam.multi}</b>
              <span>多选 / 34</span>
            </div>
            <div className="spacer" />
            <button className="btn sm" onClick={() => nav('stats')}>
              全部记录
            </button>
          </div>
        ) : (
          <div className="muted small">还没有模考记录，先来一套试试。</div>
        )}
      </div>
    </>
  )
}
