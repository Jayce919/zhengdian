export type SubjectId = 'mayuan' | 'maozhongte' | 'xisixiang' | 'shigang' | 'sifa' | 'shizheng'

export type QType = 'single' | 'multi' | 'judge'

export interface Confusion {
  a: string
  b: string
  diff: string
}

export interface Point {
  id: string
  title: string
  /** 教材原句，原样摘录，不在整理时改写 */
  quote: string
  core: string
  detail: string[]
  keywords: string[]
  confusions: Confusion[]
  refs: string[]
}

export interface Part {
  id: string
  no: string
  title: string
  summary?: string
  points: Point[]
}

export interface Subject {
  id: SubjectId
  name: string
  short: string
  examShare: number
  parts: Part[]
}

export type Trap = '偷换概念' | '扩大缩小' | '张冠李戴' | '绝对化' | '因果倒置' | '无关正确项'

export interface Question {
  id: string
  type: QType
  subject: SubjectId
  partId: string
  stem: string
  options?: string[]
  /** single/judge 为字符串或布尔；multi 为字母数组 */
  answer: string | string[] | boolean
  explain: string
  distractors?: Record<string, { why: string; trap: Trap }>
  refs: string[]
  difficulty?: number
  /** 题目来源：zhenti / textbook / confusion / card 等 */
  source?: string
  /** 背诵判断对应的考点 */
  pointId?: string
}

export interface Weights {
  /** 单选题量 */
  single: number
  /** 多选题量 */
  multi: number
  /** 选择题分值 */
  score: number
  examShare: number
}

export interface TimelineEvent {
  id: string
  year: number
  date: string
  title: string
  kind: '会议' | '文件' | '著作' | '战争' | '运动' | '事件'
  subject: SubjectId
  place?: string
  people?: string[]
  content: string
  meaning: string
  refs: string[]
}

export interface MindNode {
  label: string
  pointId?: string
  children?: MindNode[]
}

export interface MindTree {
  subject: SubjectId
  partId: string
  title: string
  root: MindNode
}

export interface SrsCard {
  ef: number
  interval: number
  reps: number
  lapses: number
  due: number
  last: number
}

export interface Answered {
  correct: boolean
  at: number
}

export interface Progress {
  version: 1
  srs: Record<string, SrsCard>
  flags: Record<string, { mistake?: number; fuzzy?: boolean; starred?: boolean }>
  answers: Record<string, Answered>
  streak: { last: string; days: number }
  exams: { at: number; score: number; single: number; multi: number; seconds: number; max?: number }[]
  settings: {
    newPerDay: number
    theme: 'light' | 'dark'
    timerMinutes: number
    paperMode: 'template' | 'weighted' | 'zhenti'
  }
}
