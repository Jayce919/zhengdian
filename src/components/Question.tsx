import type { Question } from '../types'
import type { Grade } from '../lib/scoring'
import { LETTERS, scoreOf } from '../lib/scoring'
import { SUBJECT_NAMES } from '../lib/content'

export const judgeOptions = ['T. 正确', 'F. 错误']

export function optionText(o: string) {
  return o.replace(/^[A-Za-z][.、．]\s*/, '')
}

export function correctLetters(q: Question): string[] {
  if (q.type === 'multi') return q.answer as string[]
  if (q.type === 'judge') return [(q.answer as boolean) ? 'T' : 'F']
  return [q.answer as string]
}

interface BodyProps {
  q: Question
  picked: string[]
  onPick?: (letters: string[]) => void
  revealed?: boolean
  index?: number
  total?: number
}

export function QuestionBody({ q, picked, onPick, revealed, index, total }: BodyProps) {
  const opts = q.type === 'judge' ? judgeOptions : (q.options ?? [])
  const right = correctLetters(q)

  const stateOf = (letter: string) => {
    if (!revealed) return undefined
    if (right.includes(letter)) return 'right'
    if (picked.includes(letter)) return 'wrong'
    return undefined
  }

  const toggle = (letter: string) => {
    if (!onPick || revealed) return
    if (q.type === 'multi') {
      onPick(picked.includes(letter) ? picked.filter((x) => x !== letter) : [...picked, letter])
    } else {
      onPick([letter])
    }
  }

  return (
    <>
      <div className="qhead">
        <span className="tag primary">{SUBJECT_NAMES[q.subject].short}</span>
        <span className="tag">{q.type === 'single' ? '单选' : q.type === 'multi' ? '多选' : '判断'}</span>
        {total ? (
          <span className="spacer" />
        ) : null}
        {total ? (
          <span className="muted tiny">
            {index! + 1} / {total}
          </span>
        ) : null}
      </div>

      <div className="qstem">{q.stem}</div>
      {q.type === 'multi' ? <div className="muted tiny" style={{ marginTop: 6 }}>多选：少选、错选均不得分</div> : null}

      <div className="options">
        {opts.map((o, i) => {
          const letter = q.type === 'judge' ? (i === 0 ? 'T' : 'F') : LETTERS[i]
          const st = stateOf(letter)
          return (
            <button
              key={letter}
              className="option"
              data-picked={picked.includes(letter)}
              data-state={st}
              onClick={() => toggle(letter)}
              disabled={revealed}
              aria-pressed={picked.includes(letter)}
            >
              <span className="k">{letter === 'T' ? '✓' : letter === 'F' ? '✕' : letter}</span>
              <span>{optionText(o)}</span>
            </button>
          )
        })}
      </div>
    </>
  )
}

export function Feedback({ q, grade, picked }: { q: Question; grade: Grade; picked: string[] }) {
  const right = correctLetters(q)
  const gain = scoreOf(q, grade)
  return (
    <div className="explain">
      <div className={`verdict ${grade.correct ? 'ok' : 'bad'}`}>
        {grade.correct ? '✓ 答对' : '✕ 答错'}
        {q.type === 'multi' ? <span className="tag">{grade.correct ? '得 2 分' : '得 0 分'}</span> : null}
        {q.type === 'single' ? <span className="tag">{gain ? '得 1 分' : '得 0 分'}</span> : null}
      </div>

      {q.type === 'multi' && !grade.correct ? (
        <div className="why">
          {grade.missing.length ? (
            <div>
              <span className="tag warn">漏选</span> {grade.missing.join('、')}
            </div>
          ) : null}
          {grade.extra.length ? (
            <div>
              <span className="tag bad">错选</span> {grade.extra.join('、')}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="why">
        <span className="muted">正确答案：</span>
        <b>{right.join('')}</b>
        {picked.length ? <span className="muted">（你选 {picked.join('') || '无'}）</span> : null}
      </div>

      <div className="why">{q.explain}</div>

      {q.distractors ? (
        <div className="why">
          {Object.entries(q.distractors).map(([letter, d]) =>
            picked.includes(letter) || !grade.correct ? (
              <div key={letter} style={{ marginTop: 6 }}>
                <span className="who">{letter}</span>{' '}
                <span className="tag">{d.trap}</span> {d.why}
              </div>
            ) : null,
          )}
        </div>
      ) : null}

      {q.refs?.length ? <div className="refs">出处：{q.refs.join('；')}</div> : null}
    </div>
  )
}
