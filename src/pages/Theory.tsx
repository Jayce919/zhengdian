import { useState } from 'react'
import {
  KEYWORD_GROUPS,
  SUBJECT_NAMES,
  SUBJECT_ORDER,
  partById,
  pointById,
  pointsByKeyword,
  searchPoints,
  subjects,
  questionsOf,
  todayStamp,
} from '../lib/content'

export default function Theory({ seg, nav }: { nav: (to: string) => void; seg: string[] }) {
  const [kw, setKw] = useState('')

  if (seg[0] === 'x' && seg[1]) {
    const pt = pointById(seg[1])
    if (!pt) return <div className="empty">未找到该考点</div>
    const part = [...subjects.flatMap((s) => s.parts)].find((p) => p.points.some((x) => x.id === pt.id))
    return (
      <div className="card point">
        <div className="row small">
          <span className="tag primary">{part?.no}</span>
          <span className="muted">{part?.title}</span>
        </div>
        <h2 style={{ marginTop: 8 }}>{pt.title}</h2>

        <div className="quote">{pt.quote}</div>

        <h3>要点</h3>
        <div>{pt.core}</div>
        {pt.detail.length ? (
          <ul className="bullets">
            {pt.detail.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        ) : null}

        {pt.confusions.length ? (
          <>
            <h3>易混对比</h3>
            <table className="cmp">
              <thead>
                <tr>
                  <th style={{ width: '28%' }}>概念</th>
                  <th style={{ width: '28%' }}>易混</th>
                  <th>区别</th>
                </tr>
              </thead>
              <tbody>
                {pt.confusions.map((c, i) => (
                  <tr key={i}>
                    <td>{c.a}</td>
                    <td>{c.b}</td>
                    <td>{c.diff}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : null}

        <div className="refs">出处：{pt.refs.join('；')}</div>
        <div className="toolbar" style={{ marginTop: 14 }}>
          <button className="btn sm" onClick={() => nav('theory')}>
            返回
          </button>
          <div className="spacer" />
          <button className="btn sm primary" onClick={() => nav('practice')}>
            去刷相关题
          </button>
        </div>
      </div>
    )
  }

  if (seg[0] === 'p' && seg[1]) {
    const part = partById(seg[1])
    if (!part) return <div className="empty">未找到该专题</div>
    return (
      <>
        <div className="card">
          <div className="muted small">{part.no}</div>
          <h2>{part.title}</h2>
          {part.summary ? <div className="muted small">{part.summary}</div> : null}
        </div>
        <div className="list grid-wide">
          {part.points.map((pt) => (
            <button key={pt.id} className="item" onClick={() => nav(`theory/x/${pt.id}`)}>
              <div style={{ flex: 1 }}>
                <div className="title">{pt.title}</div>
                <div className="sub">{pt.core.slice(0, 46)}…</div>
              </div>
              <span className="muted">›</span>
            </button>
          ))}
        </div>
      </>
    )
  }

  if (seg[0] === 's' && seg[1]) {
    const s = subjects.find((x) => x.id === seg[1])
    if (!s) return <div className="empty">该学科内容尚未整理</div>
    return (
      <>
        <div className="card">
          <h2>{s.name}</h2>
          <div className="muted small">大纲占比 {s.examShare}%</div>
        </div>
        <div className="list grid-wide">
          {s.parts.map((p) => (
            <button key={p.id} className="item" onClick={() => nav(`theory/p/${p.id}`)}>
              <div style={{ flex: 1 }}>
                <div className="title">
                  {p.no} {p.title}
                </div>
                <div className="sub">{p.points.length} 个考点</div>
              </div>
              <span className="muted">›</span>
            </button>
          ))}
        </div>
      </>
    )
  }

  if (seg[0] === 'keywords') {
    return (
      <>
        <div className="card">
          <h2>提法速查</h2>
          <div className="muted small">
            政治最爱考的固定搭配：同一词在不同原理中的对应表述。点开逐条对照原文。
          </div>
          <div className="toolbar" style={{ marginTop: 10 }}>
            {KEYWORD_GROUPS.map((k) => (
              <span key={k} className="chip">
                {k} · {pointsByKeyword(k).length}
              </span>
            ))}
          </div>
        </div>
        {KEYWORD_GROUPS.map((k) => {
          const pts = pointsByKeyword(k)
          if (!pts.length) return null
          return (
            <div className="card" key={k}>
              <h2>“{k}”的提法</h2>
              <div className="list">
                {pts.map((p) => (
                  <button key={p.id} className="item" onClick={() => nav(`theory/x/${p.id}`)}>
                    <div style={{ flex: 1 }}>
                      <div className="title">{p.title}</div>
                      <div className="sub">{p.core.slice(0, 52)}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )
        })}
        <div className="muted tiny center" style={{ marginTop: 12 }}>
          整理截至 {todayStamp}
        </div>
      </>
    )
  }

  const results = searchPoints(kw)

  return (
    <>
      <div className="card">
        <input
          value={kw}
          onChange={(e) => setKw(e.target.value)}
          placeholder="搜索考点、关键词，如“剩余价值”“根本动力”"
          style={{
            width: '100%',
            border: '1px solid var(--line)',
            background: 'var(--surface)',
            color: 'var(--ink)',
            borderRadius: 12,
            padding: '11px 14px',
            fontSize: 15,
          }}
        />
        <div className="toolbar" style={{ marginTop: 10 }}>
          <button className="chip" onClick={() => nav('theory/keywords')}>
            提法速查
          </button>
        </div>
      </div>

      {kw.trim() ? (
        <div className="list grid-wide">
          {results.length === 0 ? <div className="empty">没有匹配的考点</div> : null}
          {results.map(({ point, part }) => (
            <button key={point.id} className="item" onClick={() => nav(`theory/x/${point.id}`)}>
              <div style={{ flex: 1 }}>
                <div className="title">{point.title}</div>
                <div className="sub">
                  {part?.no} {part?.title}
                </div>
              </div>
              <span className="muted">›</span>
            </button>
          ))}
        </div>
      ) : (
        <div className="list grid-wide">
          {SUBJECT_ORDER.map((id) => {
            const s = subjects.find((x) => x.id === id)
            const n = s?.parts.reduce((a, p) => a + p.points.length, 0) ?? 0
            const qn = questionsOf(id).length
            return (
              <button
                key={id}
                className="item"
                onClick={() => nav(`theory/s/${id}`)}
                disabled={!s}
                style={{ opacity: s ? 1 : 0.5 }}
              >
                <div style={{ flex: 1 }}>
                  <div className="title">{SUBJECT_NAMES[id].name}</div>
                  <div className="sub">
                    {n > 0 ? `${s!.parts.length} 个专题 · ${n} 个考点` : qn > 0 ? `独立题库 ${qn} 题，去刷题板块练习` : '待整理'}
                  </div>
                </div>
                <span className="muted">{s ? '›' : '—'}</span>
              </button>
            )
          })}
        </div>
      )}
    </>
  )
}
