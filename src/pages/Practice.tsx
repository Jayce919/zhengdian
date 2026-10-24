import { useEffect, useMemo, useRef, useState } from 'react'
import type { Question, SubjectId } from '../types'
import { questions, SUBJECT_ORDER, SUBJECT_NAMES, subjects } from '../lib/content'
import { actions, useProgress } from '../lib/store'
import { isDue } from '../lib/srs'
import { grade, shuffle } from '../lib/scoring'
import { requestLeave, setNavGuard } from '../lib/navGuard'
import { confirmDialog } from '../lib/confirm'
import { Feedback, QuestionBody } from '../components/Question'

type Scope = 'due' | 'new' | 'mistakes' | 'all'
type Phase = 'setup' | 'run' | 'done'

type AnswerRecord = { picked: string[]; revealed: boolean }

const TYPES: { key: string; label: string }[] = [
  { key: 'single', label: '单选' },
  { key: 'multi', label: '多选' },
  { key: 'judge', label: '判断' },
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

  // 刷新或异常退出后，从浏览器会话里恢复上一次没做完的练习
  const boot = useMemo(() => {
    const s = loadSession()
    if (!s) return null
    const q = restoreQueue(s.ids)
    return q.length ? { s, queue: q } : null
  }, [])

  const [subject, setSubject] = useState<SubjectId | 'all'>(boot?.s.subject ?? 'all')
  const [types, setTypes] = useState<Set<string>>(() => new Set(boot?.s.types ?? ['single', 'multi']))
  const [scope, setScope] = useState<Scope>(boot?.s.scope ?? (autoMistakes ? 'mistakes' : 'due'))
  const [limit, setLimit] = useState(boot?.s.limit ?? 20)

  const [phase, setPhase] = useState<Phase>(boot ? 'run' : autoMistakes ? 'run' : 'setup')
  const [queue, setQueue] = useState<Question[]>(
    () =>
      boot?.queue ??
      (autoMistakes ? build(questions, p, 'all', new Set(['single', 'multi', 'judge']), 'mistakes', 20) : []),
  )
  const [idx, setIdx] = useState(boot ? Math.min(boot.s.idx, boot.queue.length - 1) : 0)
  const [picked, setPicked] = useState<string[]>(boot?.s.picked ?? [])
  const [revealed, setRevealed] = useState(boot?.s.revealed ?? false)
  // 回看上一题时要用到每题当时的选项与是否已揭晓
  const [records, setRecords] = useState<AnswerRecord[]>(() => {
    if (boot?.s.records?.length) return boot.s.records
    const arr: AnswerRecord[] = []
    if (boot?.s.revealed) arr[boot.s.idx] = { picked: boot.s.picked, revealed: true }
    return arr
  })
  const [tally, setTally] = useState(boot?.s.tally ?? { right: 0, total: 0 })

  // 作答进度实时存入会话，刷新、切后台被回收后还能接着做
  useEffect(() => {
    if (phase !== 'run' || queue.length === 0) return
    saveSession({
      ids: queue.map((q) => q.id),
      idx,
      picked,
      revealed,
      records,
      tally,
      subject,
      types: [...types],
      scope,
      limit,
    })
  }, [phase, queue, idx, picked, revealed, records, tally, subject, types, scope, limit])

  // 已确认离开时，跳转本身会触发一次 popstate，别再弹一次
  const leaving = useRef(false)

  // 离开前确认；确认离开才清掉会话，避免下次意外续上
  useEffect(() => {
    if (phase !== 'run') {
      setNavGuard(null)
      return
    }
    setNavGuard((_to, proceed) => {
      confirmDialog({
        title: '离开本次练习？',
        message: '这一组还没做完，离开会清空已作答的内容。',
        okText: '离开',
        cancelText: '继续做题',
        danger: true,
      }).then((ok) => {
        if (!ok) return
        leaving.current = true
        clearSession()
        proceed()
      })
    })
    return () => setNavGuard(null)
  }, [phase])

  // Android 16 预测性返回：练习中按返回先弹确认，而不是退出应用
  useEffect(() => {
    if (phase !== 'run') return
    history.pushState({ zz: 'practice-run' }, '')
    const onPop = () => {
      if (leaving.current) return
      history.pushState({ zz: 'practice-run' }, '')
      requestLeave('practice', () => setPhase('setup'))
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [phase])

  const pool = useMemo(
    () => build(questions, p, subject, types, scope, 9999),
    [p, subject, types, scope],
  )

  const q = queue[idx]

  function start() {
    clearSession()
    setQueue(build(questions, p, subject, types, scope, limit))
    setIdx(0)
    setTally({ right: 0, total: 0 })
    setPicked([])
    setRevealed(false)
    setRecords([])
    setPhase('run')
  }

  function submit() {
    if (!q || picked.length === 0) return
    const g = grade(q, picked)
    actions.answer(q.id, g.correct)
    setRevealed(true)
    setRecords((r) => {
      const next = [...r]
      next[idx] = { picked, revealed: true }
      return next
    })
    setTally((t) => ({ right: t.right + (g.correct ? 1 : 0), total: t.total + 1 }))
  }

  function goTo(n: number) {
    const i = Math.max(0, Math.min(queue.length - 1, n))
    if (i === idx) return
    const rec = records[i]
    setIdx(i)
    setPicked(rec?.picked ?? [])
    setRevealed(rec?.revealed ?? false)
  }

  function next() {
    if (idx + 1 >= queue.length) {
      clearSession()
      setPhase('done')
      return
    }
    goTo(idx + 1)
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

  const g = revealed ? grade(q, picked) : null

  return (
    <>
      <div className="progressbar">
        <span className="muted small">
          {idx + 1}/{queue.length}
        </span>
        <div className="meter">
          <i style={{ width: `${((idx + (revealed ? 1 : 0)) / queue.length) * 100}%` }} />
        </div>
        <button
          className="btn sm ghost"
          onClick={() => {
            clearSession()
            setPhase('done')
          }}
        >
          结束
        </button>
      </div>

      <div className={revealed ? 'split' : undefined}>
        <div className="card">
            <>
              <QuestionBody q={q} picked={picked} onPick={setPicked} revealed={revealed} index={idx} total={queue.length} />
              <div className="toolbar" style={{ marginTop: 16 }}>
                <button className="btn sm" onClick={() => goTo(idx - 1)} disabled={idx === 0}>
                  上一题
                </button>
                <button
                  className="btn sm ghost"
                  onClick={() => {
                    actions.answer(q.id, false)
                    setRevealed(true)
                    setTally((t) => ({ right: t.right, total: t.total + 1 }))
                    setRecords((r) => {
                      const next = [...r]
                      next[idx] = { picked: [], revealed: true }
                      return next
                    })
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
        </div>

        {revealed && g ? (
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
  types: Set<string>,
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

const SESSION_KEY = 'zz-practice-session'

interface PracticeSession {
  ids: string[]
  idx: number
  picked: string[]
  revealed: boolean
  records?: AnswerRecord[]
  tally: { right: number; total: number }
  subject: SubjectId | 'all'
  types: string[]
  scope: Scope
  limit: number
}

function saveSession(s: PracticeSession) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(s))
  } catch {
    /* 隐私模式或配额满时忽略 */
  }
}

function clearSession() {
  try {
    sessionStorage.removeItem(SESSION_KEY)
  } catch {
    /* 同上 */
  }
}

function loadSession(): PracticeSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    if (!raw) return null
    const s = JSON.parse(raw) as PracticeSession
    if (!Array.isArray(s.ids) || s.ids.length === 0) return null
    return s
  } catch {
    return null
  }
}

function restoreQueue(ids: string[]): Question[] {
  const byId = new Map(questions.map((q) => [q.id, q]))
  return ids.map((id) => byId.get(id)).filter((q): q is Question => Boolean(q))
}
