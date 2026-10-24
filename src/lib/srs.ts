import type { SrsCard } from '../types'

const DAY = 86400000

export const newCard = (): SrsCard => ({
  ef: 2.5,
  interval: 0,
  reps: 0,
  lapses: 0,
  due: Date.now(),
  last: 0,
})

/** SM-2，q 取 1/3/4/5（重来/困难/良好/简单） */
export function review(card: SrsCard, q: number, now = Date.now()): SrsCard {
  const c = { ...card, last: now }
  if (q < 3) {
    c.reps = 0
    c.interval = 1
    c.lapses += 1
  } else {
    if (c.reps === 0) c.interval = 1
    else if (c.reps === 1) c.interval = 6
    else c.interval = Math.round(c.interval * c.ef)
    c.reps += 1
  }
  c.ef = Math.max(1.3, c.ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
  c.due = now + c.interval * DAY
  return c
}

export const isDue = (card: SrsCard | undefined, now = Date.now()) => !card || card.due <= now
