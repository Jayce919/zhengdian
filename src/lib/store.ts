import { useSyncExternalStore } from 'react'
import type { Progress } from '../types'
import { newCard, review } from './srs'

const KEY = 'zz-progress-v1'

const todayKey = (d = new Date()) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

const defaults = (): Progress => ({
  version: 1,
  srs: {},
  flags: {},
  answers: {},
  streak: { last: '', days: 0 },
  exams: [],
  settings: { newPerDay: 30, theme: 'light', timerMinutes: 50, paperMode: 'template' },
})

function load(): Progress {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return defaults()
    const parsed = JSON.parse(raw) as Progress
    return { ...defaults(), ...parsed, settings: { ...defaults().settings, ...parsed.settings } }
  } catch {
    return defaults()
  }
}

let state: Progress = load()
const listeners = new Set<() => void>()

function commit(next: Progress) {
  state = next
  try {
    localStorage.setItem(KEY, JSON.stringify(state))
  } catch {
    /* 配额满时只保留内存态 */
  }
  listeners.forEach((l) => l())
}

const subscribe = (l: () => void) => {
  listeners.add(l)
  return () => listeners.delete(l)
}

export const useProgress = () => useSyncExternalStore(subscribe, () => state, () => state)

function touchStreak(p: Progress): Progress['streak'] {
  const t = todayKey()
  if (p.streak.last === t) return p.streak
  const yesterday = todayKey(new Date(Date.now() - 86400000))
  return { last: t, days: p.streak.last === yesterday ? p.streak.days + 1 : 1 }
}

export const actions = {
  answer(qid: string, correct: boolean) {
    const p = { ...state }
    const prev = p.srs[qid]
    p.srs = { ...p.srs, [qid]: review(prev ?? newCard(), correct ? 4 : 1) }
    p.answers = { ...p.answers, [qid]: { correct, at: Date.now() } }
    if (!correct) {
      const f = p.flags[qid] ?? {}
      p.flags = { ...p.flags, [qid]: { ...f, mistake: (f.mistake ?? 0) + 1 } }
    }
    p.streak = touchStreak(p)
    commit(p)
  },

  rateCard(qid: string, q: number) {
    const p = { ...state }
    p.srs = { ...p.srs, [qid]: review(p.srs[qid] ?? newCard(), q) }
    p.streak = touchStreak(p)
    commit(p)
  },

  toggleFlag(qid: string, key: 'fuzzy' | 'starred') {
    const f = state.flags[qid] ?? {}
    commit({ ...state, flags: { ...state.flags, [qid]: { ...f, [key]: !f[key] } } })
  },

  clearMistake(qid: string) {
    const f = state.flags[qid]
    if (!f) return
    commit({ ...state, flags: { ...state.flags, [qid]: { ...f, mistake: 0 } } })
  },

  recordExam(e: { score: number; single: number; multi: number; seconds: number; max?: number }) {
    commit({ ...state, exams: [...state.exams, { ...e, at: Date.now() }].slice(-100) })
  },

  setSettings(patch: Partial<Progress['settings']>) {
    commit({ ...state, settings: { ...state.settings, ...patch } })
  },

  exportJson() {
    return JSON.stringify(state, null, 2)
  },

  importJson(raw: string) {
    const parsed = JSON.parse(raw) as Progress
    commit({ ...defaults(), ...parsed })
  },

  reset() {
    commit(defaults())
  },
}

export { todayKey }
