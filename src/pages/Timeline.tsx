import { useState } from 'react'
import type { TimelineEvent } from '../types'
import { timeline } from '../lib/content'

const KINDS = ['全部', '会议', '文件', '著作', '战争', '运动', '事件'] as const
type Kind = (typeof KINDS)[number]

export default function TimelinePage({ seg }: { seg: string[] }) {
  const initial = (KINDS.find((k) => k === seg[0]) ?? '全部') as Kind
  const [kind, setKind] = useState<Kind>(initial)
  const [open, setOpen] = useState<string | null>(null)

  const list: TimelineEvent[] = timeline
    .filter((e) => kind === '全部' || e.kind === kind)
    .sort((a, b) => a.year - b.year)

  // 按年代分组，让每个年代标签只在自己那一组内吸顶
  const groups: { decade: number; events: TimelineEvent[] }[] = []
  for (const e of list) {
    const d = Math.floor(e.year / 10) * 10
    const last = groups[groups.length - 1]
    if (last && last.decade === d) last.events.push(e)
    else groups.push({ decade: d, events: [e] })
  }

  return (
    <>
      <div className="card">
        <div className="muted small">史纲主线、重要会议与著作，按年份排序。点条目展开意义与出处。</div>
        <div className="toolbar" style={{ marginTop: 10 }}>
          {KINDS.map((k) => (
            <button key={k} className="chip" aria-pressed={kind === k} onClick={() => setKind(k)}>
              {k}
            </button>
          ))}
        </div>
      </div>

      {list.length === 0 ? (
        <div className="empty">暂无该类型的事件</div>
      ) : (
        <div className="card">
          <div className="timeline">
            {groups.map((g) => (
              <div className="decade-group" key={g.decade}>
                <div className="decade">{g.decade} 年代</div>
                {g.events.map((e) => (
                  <div
                    key={e.id}
                    className="tl-item"
                    onClick={() => setOpen(open === e.id ? null : e.id)}
                  >
                    <div>
                      <span className="yr">{e.year}</span>
                      <span style={{ fontWeight: 600 }}>{e.title}</span>
                      <span className="tag" style={{ marginLeft: 8 }}>
                        {e.kind}
                      </span>
                    </div>
                    <div className="muted tiny">
                      {e.date}
                      {e.place ? ` · ${e.place}` : ''}
                    </div>
                    {open === e.id ? (
                      <div className="tl-body">
                        <div className="small">{e.content}</div>
                        <div className="quote" style={{ marginTop: 8 }}>
                          {e.meaning}
                        </div>
                        <div className="refs">出处：{e.refs.join('；')}</div>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
