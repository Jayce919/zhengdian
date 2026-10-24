import { useEffect, useMemo, useState } from 'react'
import type { QType, Question, SubjectId } from '../types'
import { questions, SUBJECT_ORDER, SUBJECT_NAMES, subjects } from '../lib/content'
import { actions, useProgress } from '../lib/store'
import { isDue } from '../lib/srs'
import { grade, shuffle } from '../lib/scoring'
import { Feedback, QuestionBody } from '../components/Question'

type Scope = 'due' | 'new' | 'mistakes' | 'all'
type Phase = 'setup' | 'run' | 'done'

const TYPES: { key: QType; label: string }[] = [
  { key: 'single', label: '单选' },
  { key: 'multi', label: '多选' },
  { key: 'judge', label: '判断' },
  { key: 'card', label: '背诵卡' },
]

const SCOPES: { key: Scope; label: string }[] = [
  { key: 'due', label: '今日复习' },
  { key: 'new', label: '未做' },
  { key: 'mistakes', label: '错题' },
  { key: 'all', label: '全部' },
]

export default function Practice({ initial }: { nav: (to: string) => void; initial: string[] }) {
  const p = useProgress()
  const autoMistakes = initial[0] === 'mistakes'

  const [subject, setSubject] = useState<SubjectId | 'all'>('all')
  const [types, setTypes] = useState<Set<QType>>(new Set(['single', 'multi']))
  const [scope, setScope] = useState<Scope>(autoMistakes ? 'mistakes' : 'due')
  const [limit, setLimit] = useState(20)

  const [phase, setPhase] = useState<Phase>(autoMistakes ? 'run' : 'setup')
  const [queue, setQueue] = useState<Question[]>(() => (autoMistakes ? build(questions, p, 'all', new Set(['single', 'multi', 'judge']), 'mistakes', 20) : []))
  const [idx, setIdx] = useState(0)
  const [picked, setPicked] = useState<string[]>([])
  const [revealed, setRevealed] = useState(false)
  const [cardOpen, setCardOpen] = useState(false)
  const [tally, setTally] = useState({ right: 0, total: 0 })

  // Android 16 预测性返回：练习中按返回先回到设置，而不是退出应用
  useEffect(() => {
    if (phase !== 'run') return
    history.pushState({ zz: 'practice-run' }, '')
    const onPop = () => setPhase('setup')
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [phase])

  const pool = useMemo(
    () => build(questions, p, subject, types, scope, 9999),
    [p, subject, types, scope],
  )

  const q = queue[idx]

  function start() {
    setQueue(build(questions, p, subject, types, scope, limit))
    setIdx(0)
    setTally({ right: 0, total: 0 })
    setPicked([])
    setRevealed(false)
    setCardOpen(false)
    setPhase('run')
  }

  function submit() {
    if (!q || picked.length === 0) return
    const g = grade(q, picked)
    actions.answer(q.id, g.correct)
    setRevealed(true)
    setTally((t) => ({ right: t.right + (g.correct ? 1 : 0), total: t.total + 1 }))
  }

  function rate(qv: number) {
    if (!q) return
    actions.rateCard(q.id, qv)
    setTally((t) => ({ right: t.right + (qv >= 3 ? 1 : 0), total: t.total + 1 }))
    next()
  }

  function next() {
    if (idx + 1 >= queue.length) {
      setPhase('done')
      return
    }
    setIdx(idx + 1)
    setPicked([])
    setRevealed(false)
    setCardOpen(false)
  }

  if (phase === 'setup') {
    return (
      <>
        <div className="card">
          <h2>选择范围</h2>
          <div className="toolbar">
            <button className="chip" aria-pressed={subject === 'all'} onClick={() => setSubject('all')}>
              全部
            </button>
            {SUBJECT_ORDER.filter((id) => subjects.some((s) => s.id === id) || questions.some((q) => q.subject === id)).map((id) => (
              <button key={id} className="chip" aria-pressed={subject === id} onClick={() => setSubject(id)}>
                {SUBJECT_NAMES[id].short}
              </button>
            ))}
          </div>

          <h3>题型</h3>
          <div className="toolbar">
            {TYPES.map((t) => (
              <button
                key={t.key}
                className="chip"
                aria-pressed={types.has(t.key)}
                onClick={() => {
                  const s = new Set(types)
                  s.has(t.key) ? s.delete(t.key) : s.add(t.key)
                  setTypes(s)
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          <h3>范围</h3>
          <div className="toolbar">
            {SCOPES.map((s) => (
              <button key={s.key} className="chip" aria-pressed={scope === s.key} onClick={() => setScope(s.key)}>
                {s.label}
              </button>
            ))}
          </div>

          <h3>数量</h3>
          <div className="toolbar">
            {[10, 20, 40, 80].map((n) => (
              <button key={n} className="chip" aria-pressed={limit === n} onClick={() => setLimit(n)}>
                {n} 题
              </button>
            ))}
          </div>

          <div className="muted small" style={{ marginTop: 14 }}>
            当前范围共 {pool.length} 题
            {pool.length === 0 ? '，换一个「范围」或题型试试' : ''}
          </div>
          <button className="btn primary wide" style={{ marginTop: 12 }} onClick={start} disabled={!pool.length || !types.size}>
            开始练习
          </button>
        </div>
      </>
    )
  }

  if (phase === 'done') {
    const acc = tally.total ? Math.round((tally.right / tally.total) * 100) : 0
    return (
      <div className="card">
        <div className="score-hero">
          <div className="muted small">正确率</div>
          <div className="num">{acc}%</div>
          <div className="muted small">
            {tally.right} / {tally.total}
          </div>
        </div>
        <button className="btn primary wide" onClick={() => setPhase('setup')}>
          再练一组
        </button>
      </div>
    )
  }

  if (!q) return <div className="empty">没有符合条件的题目</div>

  const isCard = q.type === 'card'
  const g = isCard || revealed ? grade(q, picked) : null

  return (
    <>
      <div className="progressbar">
        <span className="muted small">
          {idx + 1}/{queue.length}
        </span>
        <div className="meter">
          <i style={{ width: `${((idx + (revealed ? 1 : 0)) / queue.length) * 100}%` }} />
        </div>
        <button className="btn sm ghost" onClick={() => setPhase('done')}>
          结束
        </button>
      </div>

      <div className={revealed && !isCard ? 'split' : undefined}>
        <div className="card">
          {isCard ? (
            <>
              <div className="qhead">
                <span className="tag primary">{SUBJECT_NAMES[q.subject].short}</span>
                <span className="tag">背诵卡</span>
              </div>
              <div className="qstem card-front">{q.stem}</div>
              {cardOpen ? (
                <>
                  <div className="quote">{q.answer as string}</div>
                  <div className="muted small">{q.explain}</div>
                  <div className="refs">出处：{q.refs.join('；')}</div>
                  <div className="toolbar" style={{ marginTop: 14 }}>
                    <button className="btn" onClick={() => rate(1)}>
                      忘了
                    </button>
                    <button className="btn" onClick={() => rate(3)}>
                      模糊
                    </button>
                    <button className="btn primary" onClick={() => rate(5)}>
                      记得
                    </button>
                  </div>
                </>
              ) : (
                <button className="btn primary wide" style={{ marginTop: 16 }} onClick={() => setCardOpen(true)}>
                  显示答案
                </button>
              )}
            </>
          ) : (
            <>
              <QuestionBody q={q} picked={picked} onPick={setPicked} revealed={revealed} index={idx} total={queue.length} />
              <div className="toolbar" style={{ marginTop: 16 }}>
                <button
                  className="btn sm ghost"
                  onClick={() => {
                    actions.answer(q.id, false)
                    setRevealed(true)
                    setTally((t) => ({ right: t.right, total: t.total + 1 }))
                  }}
                  disabled={revealed}
                >
                  不会
                </button>
                <div className="spacer" />
                {revealed ? (
                  <button className="btn primary" onClick={next}>
                    {idx + 1 >= queue.length ? '完成' : '下一题'}
                  </button>
                ) : (
                  <button className="btn primary" onClick={submit} disabled={!picked.length}>
                    提交
                  </button>
                )}
              </div>
            </>
          )}
        </div>

        {revealed && !isCard && g ? (
          <div className="card sticky">
            <h2>解析</h2>
            <Feedback q={q} grade={g} picked={picked} />
          </div>
        ) : null}
      </div>
    </>
  )
}

function build(
  all: Question[],
  p: ReturnType<typeof useProgress>,
  subject: SubjectId | 'all',
  types: Set<QType>,
  scope: Scope,
  limit: number,
): Question[] {
  const now = Date.now()
  let pool = all.filter(
    (q) => (subject === 'all' || q.subject === subject) && types.has(q.type),
  )
  if (scope === 'mistakes') pool = pool.filter((q) => (p.flags[q.id]?.mistake ?? 0) > 0)
  if (scope === 'new') pool = pool.filter((q) => !p.srs[q.id])
  if (scope === 'due') pool = pool.filter((q) => isDue(p.srs[q.id], now))

  const weight = (q: Question) => {
    const f = p.flags[q.id]?.mistake ?? 0
    const s = p.srs[q.id]
    const overdue = s ? Math.min(3, (now - s.due) / 86400000) : 0
    return f * 3 + overdue
  }
  return shuffle(pool)
    .sort((a, b) => weight(b) - weight(a))
    .slice(0, limit)
}
