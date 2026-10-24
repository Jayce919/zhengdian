import { useEffect, useMemo, useRef, useState } from 'react'
import type { Question, SubjectId } from '../types'
import { questions, weights, SUBJECT_NAMES, SUBJECT_ORDER, subjects } from '../lib/content'
import { actions, useProgress } from '../lib/store'
import { grade, scoreOf, shuffle } from '../lib/scoring'
import { Feedback, QuestionBody } from '../components/Question'

type Stage = 'setup' | 'run' | 'result'

interface Paper {
  items: Question[]
  bySubject: Record<string, number>
}

function buildPaper(mode: 'template' | 'weighted' | 'zhenti'): Paper {
  if (mode === 'zhenti') {
    const byYear = new Map<number, Question[]>()
    for (const q of questions) {
      const y = (q as Question & { year?: number }).year
      if (!y) continue
      if (!byYear.has(y)) byYear.set(y, [])
      byYear.get(y)!.push(q)
    }
    const years = [...byYear.entries()].filter(([, qs]) => qs.length >= 25).map(([y]) => y).sort()
    if (years.length) {
      const year = years[Math.floor(Math.random() * years.length)]
      const items = [...byYear.get(year)!].sort((a, b) => a.id.localeCompare(b.id))
      const bySubject: Record<string, number> = {}
      for (const q of items) bySubject[q.subject] = (bySubject[q.subject] ?? 0) + 1
      return { items, bySubject }
    }
  }

  const singles = questions.filter((q) => q.type === 'single')
  const multis = questions.filter((q) => q.type === 'multi')
  const bySubject: Record<string, number> = {}

  const take = (pool: Question[], subject: SubjectId, n: number) => {
    const own = shuffle(pool.filter((q) => q.subject === subject)).slice(0, n)
    bySubject[subject] = (bySubject[subject] ?? 0) + own.length
    return own
  }

  let picked: Question[] = []
  if (mode === 'template') {
    for (const id of SUBJECT_ORDER) {
      const w = weights[id]
      if (!w) continue
      picked.push(...take(singles, id, w.single), ...take(multis, id, w.multi))
    }
  } else {
    const totalW = SUBJECT_ORDER.reduce((s, id) => s + (weights[id]?.score ?? 0), 0)
    for (const id of SUBJECT_ORDER) {
      const w = weights[id]
      if (!w) continue
      const share = w.score / totalW
      picked.push(...take(singles, id, Math.round(16 * share)), ...take(multis, id, Math.round(17 * share)))
    }
  }

  // 题库不足时按顺序补齐
  const have = new Set(picked.map((q) => q.id))
  const needS = 16 - picked.filter((q) => q.type === 'single').length
  const needM = 17 - picked.filter((q) => q.type === 'multi').length
  if (needS > 0) picked.push(...shuffle(singles.filter((q) => !have.has(q.id))).slice(0, needS))
  if (needM > 0) picked.push(...shuffle(multis.filter((q) => !have.has(q.id) && !picked.some((p) => p.id === q.id))).slice(0, needM))

  const singlesOut = shuffle(picked.filter((q) => q.type === 'single'))
  const multisOut = shuffle(picked.filter((q) => q.type === 'multi'))
  return { items: [...singlesOut, ...multisOut], bySubject }
}

export default function Exam({ nav }: { nav: (to: string) => void }) {
  const p = useProgress()
  const [stage, setStage] = useState<Stage>('setup')
  const [mode, setMode] = useState<'template' | 'weighted' | 'zhenti'>(p.settings.paperMode as 'template' | 'weighted')
  const [minutes, setMinutes] = useState(p.settings.timerMinutes)
  const [paper, setPaper] = useState<Paper>({ items: [], bySubject: {} })
  const [answers, setAnswers] = useState<Record<string, string[]>>({})
  const [idx, setIdx] = useState(0)
  const [left, setLeft] = useState(0)
  const startedAt = useRef(0)

  // Android 16 预测性返回：考试中按返回先回到设置，而不是退出应用
  useEffect(() => {
    if (stage !== 'run') return
    history.pushState({ zz: 'exam-run' }, '')
    const onPop = () => setStage('setup')
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [stage])

  const activeSubject = subjects.length > 0

  useEffect(() => {
    if (stage !== 'run') return
    const t = setInterval(() => setLeft((s) => Math.max(0, s - 1)), 1000)
    return () => clearInterval(t)
  }, [stage])

  useEffect(() => {
    if (stage === 'run' && left === 0 && minutes > 0) submit()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [left])

  const result = useMemo(() => {
    if (stage !== 'result') return null
    let score = 0
    let single = 0
    let multi = 0
    const rows = paper.items.map((q) => {
      const picked = answers[q.id] ?? []
      const g = grade(q, picked)
      const s = scoreOf(q, g)
      score += s
      if (q.type === 'single' && g.correct) single += 1
      if (q.type === 'multi' && g.correct) multi += 2
      return { q, picked, g }
    })
    return { score, single, multi, rows }
  }, [stage, paper, answers])

  function start() {
    const pp = buildPaper(mode)
    if (!pp.items.length) return
    actions.setSettings({ paperMode: mode, timerMinutes: minutes })
    setPaper(pp)
    setAnswers({})
    setIdx(0)
    setLeft(minutes * 60)
    startedAt.current = Date.now()
    setStage('run')
  }

  function submit() {
    if (!paper.items.length) return
    let score = 0
    let single = 0
    let multi = 0
    for (const q of paper.items) {
      const g = grade(q, answers[q.id] ?? [])
      score += scoreOf(q, g)
      if (q.type === 'single' && g.correct) single += 1
      if (q.type === 'multi' && g.correct) multi += 2
      actions.answer(q.id, g.correct)
    }
    const max = paper.items.filter((q) => q.type === 'single').length + paper.items.filter((q) => q.type === 'multi').length * 2
    actions.recordExam({
      score,
      single,
      multi,
      max,
      seconds: Math.round((Date.now() - startedAt.current) / 1000),
    })
    setStage('result')
  }

  if (stage === 'setup') {
    return (
      <div className="card">
        <h2>选择题整卷</h2>
        <div className="muted small">
          单选 16 题 × 1 分 + 多选 17 题 × 2 分 = 50 分。多选少选、错选均不得分。
        </div>

        <h3>组卷方式</h3>
        <div className="toolbar">
          <button className="chip" aria-pressed={mode === 'template'} onClick={() => setMode('template')}>
            严格模板卷
          </button>
          <button className="chip" aria-pressed={mode === 'weighted'} onClick={() => setMode('weighted')}>
            按权重随机卷
          </button>
          <button className="chip" aria-pressed={mode === 'zhenti'} onClick={() => setMode('zhenti')}>
            历年真题卷
          </button>
        </div>
        <div className="muted tiny" style={{ marginTop: 4 }}>
          {mode === 'template'
            ? '按真题题号结构：马原 4+5、毛中特 1+2、习思想 3+3、史纲 4+3、思修 2+2、时政 2+2'
            : mode === 'weighted'
              ? '按各学科选择题分值比例随机分配，每次略有不同'
              : '随机抽取一套历年真题的选择题部分（含原解析）'}
        </div>

        <h3>计时</h3>
        <div className="toolbar">
          {[0, 40, 50, 60].map((m) => (
            <button key={m} className="chip" aria-pressed={minutes === m} onClick={() => setMinutes(m)}>
              {m === 0 ? '不限时' : `${m} 分钟`}
            </button>
          ))}
        </div>

        {!activeSubject ? <div className="muted small" style={{ marginTop: 12 }}>题库为空，无法组卷。</div> : null}

        <button className="btn primary wide" style={{ marginTop: 16 }} onClick={start}>
          开始考试
        </button>
      </div>
    )
  }

  if (stage === 'result' && result) {
    const shown = result.rows.filter((r) => !r.g.correct)
    const singleTotal = paper.items.filter((q) => q.type === 'single').length
    const multiTotal = paper.items.filter((q) => q.type === 'multi').length
    const paperMax = singleTotal + multiTotal * 2
    return (
      <>
        <div className="card">
          <div className="score-hero">
            <div className="muted small">选择题得分</div>
            <div className="num">
              {result.score}
              <span className="den"> / {paperMax}</span>
            </div>
            <div className="row" style={{ justifyContent: 'center', marginTop: 10 }}>
              <span className="tag primary">
                单选 {result.single} / {singleTotal}
              </span>
              <span className="tag primary">
                多选 {result.multi} / {multiTotal * 2}
              </span>
            </div>
            {paperMax < 50 ? (
              <div className="muted tiny" style={{ marginTop: 6 }}>
                题库尚不足 38 题，本卷按现有题量计分
              </div>
            ) : null}
          </div>
          <div className="grid2" style={{ marginTop: 8 }}>
            {SUBJECT_ORDER.filter((id) => paper.bySubject[id]).map((id) => {
              const rows = result.rows.filter((r) => r.q.subject === id)
              const lost = rows.filter((r) => !r.g.correct)
              return (
                <div key={id} className="item" style={{ cursor: 'default', display: 'block' }}>
                  <div className="title">{SUBJECT_NAMES[id].short}</div>
                  <div className="sub">
                    {rows.length} 题 · 错 {lost.length} 题
                  </div>
                </div>
              )
            })}
          </div>
          <div className="toolbar" style={{ marginTop: 14 }}>
            <button className="btn" onClick={() => nav('theory')}>
              去理论查原文
            </button>
            <button className="btn primary" style={{ flex: 1 }} onClick={() => setStage('setup')}>
              再考一次
            </button>
          </div>
        </div>

        <div className="card">
          <h2>错题回顾（{shown.length}）</h2>
          {shown.length === 0 ? <div className="muted small">全对。</div> : null}
          {shown.map(({ q, picked, g }) => (
            <div key={q.id} style={{ marginTop: 18 }}>
              <QuestionBody q={q} picked={picked} revealed />
              <Feedback q={q} grade={g} picked={picked} />
            </div>
          ))}
        </div>
      </>
    )
  }

  const q = paper.items[idx]
  if (!q) return <div className="empty">没有可用的题目</div>
  const answered = Object.keys(answers).length
  const mm = Math.floor(left / 60)
  const ss = left % 60

  return (
    <>
      <div className="progressbar">
        <span className="muted small">
          {idx + 1}/{paper.items.length}
        </span>
        <div className="meter">
          <i style={{ width: `${(answered / paper.items.length) * 100}%` }} />
        </div>
        {minutes > 0 ? (
          <span className="tag" style={{ color: left < 300 ? 'var(--bad)' : undefined }}>
            {mm}:{String(ss).padStart(2, '0')}
          </span>
        ) : null}
      </div>

      <div className="split">
        <div className="card">
          <QuestionBody
            q={q}
            picked={answers[q.id] ?? []}
            onPick={(letters) => setAnswers((a) => ({ ...a, [q.id]: letters }))}
            index={idx}
            total={paper.items.length}
          />
          <div className="toolbar" style={{ marginTop: 16 }}>
            <button className="btn sm" onClick={() => setIdx(Math.max(0, idx - 1))} disabled={idx === 0}>
              上一题
            </button>
            <div className="spacer" />
            {idx + 1 < paper.items.length ? (
              <button className="btn primary" onClick={() => setIdx(idx + 1)}>
                下一题
              </button>
            ) : (
              <button className="btn primary" onClick={submit}>
                交卷
              </button>
            )}
          </div>
        </div>

        <div className="card sticky">
          <div className="row">
            <h2 style={{ margin: 0 }}>答题卡</h2>
            <span className="spacer" />
            <span className="muted tiny">已答 {answered}</span>
          </div>
          <div className="sheet" style={{ marginTop: 10 }}>
            {paper.items.map((item, i) => (
              <button
                key={item.id}
                data-state={(answers[item.id]?.length ?? 0) > 0 ? 'done' : undefined}
                onClick={() => setIdx(i)}
                aria-current={i === idx}
                style={i === idx ? { outline: '2px solid var(--red)' } : undefined}
              >
                {i + 1}
              </button>
            ))}
          </div>
          <button className="btn primary wide" style={{ marginTop: 12 }} onClick={submit}>
            交卷
          </button>
        </div>
      </div>
    </>
  )
}
