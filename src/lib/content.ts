import subjectsRaw from '../data/subjects.json'
import questionsRaw from '../data/questions.json'
import weightsRaw from '../data/weights.json'
import timelineRaw from '../data/timeline.json'
import mindmapsRaw from '../data/mindmaps.json'
import type { MindTree, Part, Point, Question, Subject, SubjectId, TimelineEvent, Weights } from '../types'

export const subjects = subjectsRaw as unknown as Subject[]
export const questions = questionsRaw as unknown as Question[]
export const weights = weightsRaw as Record<SubjectId, Weights>
export const timeline = timelineRaw as unknown as TimelineEvent[]
export const mindmaps = mindmapsRaw as unknown as MindTree[]

export const SUBJECT_ORDER: SubjectId[] = [
  'mayuan',
  'maozhongte',
  'xisixiang',
  'shigang',
  'sifa',
  'shizheng',
]

export const SUBJECT_NAMES: Record<SubjectId, { name: string; short: string }> = {
  mayuan: { name: '马克思主义基本原理', short: '马原' },
  maozhongte: { name: '毛泽东思想和中国特色社会主义理论体系概论', short: '毛中特' },
  xisixiang: { name: '习近平新时代中国特色社会主义思想概论', short: '习思想' },
  shigang: { name: '中国近现代史纲要', short: '史纲' },
  sifa: { name: '思想道德与法治', short: '思修法治' },
  shizheng: { name: '形势与政策及当代', short: '时政当代' },
}

const partMap = new Map<string, Part>()
const pointMap = new Map<string, Point>()
const pointPart = new Map<string, Part>()
for (const s of subjects) for (const p of s.parts) {
  partMap.set(p.id, p)
  for (const pt of p.points) {
    pointMap.set(pt.id, pt)
    pointPart.set(pt.id, p)
  }
}

export const partById = (id: string) => partMap.get(id)
export const pointById = (id: string) => pointMap.get(id)

export const pointsOf = (subject: SubjectId) =>
  subjects.filter((s) => s.id === subject).flatMap((s) => s.parts.flatMap((p) => p.points))

export const questionsOf = (subject: SubjectId) => questions.filter((q) => q.subject === subject)

export function counts() {
  const bySubject = {} as Record<SubjectId, number>
  for (const id of SUBJECT_ORDER) bySubject[id] = 0
  for (const q of questions) bySubject[q.subject] = (bySubject[q.subject] ?? 0) + 1
  return bySubject
}

export function searchPoints(kw: string, limit = 60) {
  const k = kw.trim()
  if (!k) return []
  const hits: { point: Point; part?: Part; score: number }[] = []
  for (const p of pointMap.values()) {
    const hay = `${p.title} ${p.core} ${p.quote} ${p.detail.join(' ')} ${p.keywords.join(' ')}`
    if (!hay.includes(k)) continue
    const score = (p.title.includes(k) ? 3 : 0) + (p.keywords.some((w) => w.includes(k)) ? 2 : 0) + 1
    hits.push({ point: p, part: pointPart.get(p.id), score })
  }
  return hits.sort((a, b) => b.score - a.score).slice(0, limit)
}

/** 提法速查：按“根本/本质/前提/决定/源泉/根源/第一/标志/里程碑”聚合 */
export const KEYWORD_GROUPS = ['根本', '本质', '前提', '决定', '源泉', '根源', '第一', '标志', '里程碑'] as const

export function pointsByKeyword(word: string) {
  return [...pointMap.values()].filter(
    (p) => p.keywords.includes(word) || p.core.includes(word) || p.quote.includes(word),
  )
}

export const todayStamp = '2026-10-22'
