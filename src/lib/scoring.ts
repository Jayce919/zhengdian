import type { Question, SubjectId, Weights } from '../types'

export const LETTERS = ['A', 'B', 'C', 'D'] as const

export interface Grade {
  correct: boolean
  /** 多选漏选 */
  missing: string[]
  /** 多选错选 */
  extra: string[]
}

export function grade(q: Question, response: string | string[] | boolean): Grade {
  const picked = Array.isArray(response) ? response : response === true ? ['T'] : response === false ? ['F'] : [String(response)]

  if (q.type === 'multi') {
    const chosen = new Set(picked)
    const right = new Set(q.answer as string[])
    const missing = [...right].filter((x) => !chosen.has(x))
    const extra = [...chosen].filter((x) => !right.has(x))
    return { correct: missing.length === 0 && extra.length === 0, missing, extra }
  }
  if (q.type === 'judge') {
    return { correct: (picked[0] === 'T') === q.answer, missing: [], extra: [] }
  }
  return { correct: picked[0] === q.answer, missing: [], extra: [] }
}

/** 考试口径：单选 1 分，多选全对才 2 分 */
export function scoreOf(q: Question, g: Grade): number {
  if (q.type === 'single') return g.correct ? 1 : 0
  if (q.type === 'multi') return g.correct ? 2 : 0
  return 0
}

export function largestRemainder(total: number, weights: Record<string, number>): Record<string, number> {
  const keys = Object.keys(weights)
  const sum = keys.reduce((s, k) => s + weights[k], 0)
  const raw = keys.map((k) => ({ k, v: (weights[k] / sum) * total }))
  const base = raw.map((r) => ({ ...r, n: Math.floor(r.v) }))
  let left = total - base.reduce((s, r) => s + r.n, 0)
  const byFrac = [...base].sort((a, b) => b.v - b.n - (a.v - a.n))
  for (const r of byFrac) {
    if (left <= 0) break
    r.n += 1
    left -= 1
  }
  return Object.fromEntries(base.map((r) => [r.k, r.n]))
}

export interface PaperSlot {
  subject: SubjectId
  type: 'single' | 'multi'
  count: number
}

/** 严格模板卷：按真题题号结构（习思想与毛中特已按权重拆开） */
export function templateSlots(weights: Record<SubjectId, Weights>): PaperSlot[] {
  const slots: PaperSlot[] = []
  for (const [subject, w] of Object.entries(weights) as [SubjectId, Weights][]) {
    if (w.single) slots.push({ subject, type: 'single', count: w.single })
    if (w.multi) slots.push({ subject, type: 'multi', count: w.multi })
  }
  return slots
}

export function shuffle<T>(arr: T[], rnd: () => number = Math.random): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}
