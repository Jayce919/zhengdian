import { questions, weights, SUBJECT_NAMES, SUBJECT_ORDER } from '../lib/content'
import { useProgress } from '../lib/store'

export default function Stats({ nav }: { nav: (to: string) => void }) {
  const p = useProgress()
  const answered = questions.filter((q) => p.answers[q.id])
  const right = answered.filter((q) => p.answers[q.id].correct)

  const accOf = (type: string) => {
    const pool = answered.filter((q) => q.type === type)
    const ok = pool.filter((q) => p.answers[q.id].correct)
    return pool.length ? Math.round((ok.length / pool.length) * 100) : null
  }

  const weak = Object.entries(p.flags)
    .filter(([, f]) => (f.mistake ?? 0) > 0)
    .sort((a, b) => (b[1].mistake ?? 0) - (a[1].mistake ?? 0))
    .slice(0, 12)

  const exams = [...p.exams].reverse().slice(0, 10)

  return (
    <>
      <div className="card">
        <h2>总览</h2>
        <div className="grid3">
          <div className="stat">
            <b>{answered.length}</b>
            <span>已做题</span>
          </div>
          <div className="stat">
            <b>{answered.length ? Math.round((right.length / answered.length) * 100) : 0}%</b>
            <span>总正确率</span>
          </div>
          <div className="stat">
            <b>{p.streak.days}</b>
            <span>连续天数</span>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>单选 / 多选</h2>
        <div className="row" style={{ gap: 18 }}>
          <div className="stat">
            <b>{accOf('single') ?? '—'}%</b>
            <span>单选</span>
          </div>
          <div className="stat">
            <b>{accOf('multi') ?? '—'}%</b>
            <span>多选</span>
          </div>
          <div className="stat">
            <b>{accOf('judge') ?? '—'}%</b>
            <span>判断</span>
          </div>
        </div>
        <div className="muted tiny" style={{ marginTop: 6 }}>
          多选最拉分：全对才得 2 分，漏选、错选都是 0 分。
        </div>
      </div>

      <div className="card">
        <h2>分学科</h2>
        <div className="stack">
          {SUBJECT_ORDER.map((id) => {
            const pool = answered.filter((q) => q.subject === id)
            if (!pool.length) return null
            const ok = pool.filter((q) => p.answers[q.id].correct).length
            const acc = Math.round((ok / pool.length) * 100)
            return (
              <div key={id}>
                <div className="subject-name">{SUBJECT_NAMES[id].name}</div>
                <div className="row tiny muted" style={{ marginTop: 3 }}>
                  <span>选择 {weights[id].score} 分</span>
                  <span>·</span>
                  <span>
                    {ok}/{pool.length}
                  </span>
                  <span className="spacer" />
                  <span>正确率 {acc}%</span>
                </div>
                <div className="meter" style={{ marginTop: 6 }}>
                  <i style={{ width: `${acc}%` }} />
                </div>
              </div>
            )
          })}
          {answered.length === 0 ? <div className="muted small">还没有做题记录</div> : null}
        </div>
      </div>

      <div className="card">
        <h2>模考记录</h2>
        {exams.length === 0 ? (
          <div className="muted small">还没有模考</div>
        ) : (
          <>
            <div className="row wrap" style={{ alignItems: 'flex-end', gap: 6, height: 90, marginBottom: 10 }}>
              {[...exams].reverse().map((e, i) => (
                <div key={i} style={{ flex: 1, textAlign: 'center' }}>
                  <div
                    style={{
                      height: `${Math.max(6, (e.score / (e.max ?? 50)) * 70)}px`,
                      background: 'var(--primary)',
                      borderRadius: 6,
                      opacity: 0.85,
                    }}
                    title={`${e.score}/50`}
                  />
                  <div className="muted tiny">{e.score}</div>
                </div>
              ))}
            </div>
            <div className="list">
              {exams.map((e, i) => (
                <div key={i} className="item" style={{ cursor: 'default' }}>
                  <div style={{ flex: 1 }}>
                    <div className="title">{e.score} / {e.max ?? 50} 分</div>
                    <div className="sub">
                      单选 {e.single}/16 · 多选 {e.multi}/34 · 用时 {Math.round(e.seconds / 60)} 分钟
                    </div>
                  </div>
                  <span className="muted tiny">
                    {new Date(e.at).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="card">
        <h2>易错考点</h2>
        {weak.length === 0 ? (
          <div className="muted small">还没有错题</div>
        ) : (
          <div className="list">
            {weak.map(([qid, f]) => {
              const q = questions.find((x) => x.id === qid)
              if (!q) return null
              return (
                <div key={qid} className="item" style={{ cursor: 'default' }}>
                  <div style={{ flex: 1 }}>
                    <div className="title">{q.stem.slice(0, 40)}</div>
                    <div className="sub">{SUBJECT_NAMES[q.subject].short} · 错 {f.mistake} 次</div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
        <button className="btn sm wide" style={{ marginTop: 12 }} onClick={() => nav('practice/mistakes')}>
          去刷错题
        </button>
      </div>
    </>
  )
}
