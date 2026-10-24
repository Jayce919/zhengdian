import { useState } from 'react'
import type { MindNode, MindTree } from '../types'
import Icon from '../components/Icon'
import { SUBJECT_NAMES, SUBJECT_ORDER, mindmaps, partById } from '../lib/content'

function Branch({ node, depth, nav }: { node: MindNode; depth: number; nav: (to: string) => void }) {
  const [open, setOpen] = useState(depth < 2)
  const kids = node.children ?? []
  const hasKids = kids.length > 0

  return (
    <li className={open ? '' : 'collapsed'}>
      <span
        className={`node ${hasKids ? 'toggle' : ''} ${node.pointId ? 'link' : ''} ${depth === 0 ? 'root' : ''}`}
        onClick={() => {
          if (node.pointId) nav(`theory/x/${node.pointId}`)
          else if (hasKids) setOpen(!open)
        }}
      >
        {hasKids ? <span className="caret">{open ? '▾' : '▸'}</span> : null}
        {node.label}
      </span>
      {hasKids ? (
        <ul>
          {kids.map((k, i) => (
            <Branch key={i} node={k} depth={depth + 1} nav={nav} />
          ))}
        </ul>
      ) : null}
    </li>
  )
}

export default function MindMap({ nav, seg }: { nav: (to: string) => void; seg: string[] }) {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>(() => {
    try {
      return JSON.parse(localStorage.getItem('zz-mind-collapsed') || '{}')
    } catch {
      return {}
    }
  })
  const toggleSubject = (id: string) =>
    setCollapsed((c) => {
      const next = { ...c, [id]: !c[id] }
      try {
        localStorage.setItem('zz-mind-collapsed', JSON.stringify(next))
      } catch {
        /* 忽略存储失败 */
      }
      return next
    })
  if (seg[0]) {
    const tree = mindmaps.find((m) => m.partId === seg[0])
    if (!tree) return <div className="empty">该专题还没有导图</div>
    return (
      <>
        <div className="card">
          <div className="muted small">{partById(tree.partId)?.no}</div>
          <h2>{tree.title}</h2>
          <div className="muted tiny">点带下划线的节点跳到对应考点，点其他节点展开/收起</div>
        </div>
        <div className="card mind">
          <ul>
            <Branch node={tree.root} depth={0} nav={nav} />
          </ul>
        </div>
      </>
    )
  }

  return (
    <>
      {SUBJECT_ORDER.map((id) => {
        const trees: MindTree[] = mindmaps.filter((m) => m.subject === id)
        if (!trees.length) return null
        const open = !collapsed[id]
        return (
          <div className="card" key={id}>
            <button
              className="subject-toggle"
              aria-expanded={open}
              onClick={() => toggleSubject(id)}
            >
              <span className="chev">
                <Icon name="chevron" size={18} />
              </span>
              <h2 style={{ margin: 0 }}>{SUBJECT_NAMES[id].name}</h2>
              <span className="tag">{trees.length} 个专题</span>
            </button>
            {open ? <div className="list grid-wide" style={{ marginTop: 10 }}>
              {trees.map((t) => (
                <button key={t.partId} className="item" onClick={() => nav(`mind/${t.partId}`)}>
                  <div style={{ flex: 1 }}>
                    <div className="title">{t.title}</div>
                    <div className="sub">{partById(t.partId)?.no}</div>
                  </div>
                  <span className="muted">›</span>
                </button>
              ))}
            </div> : null}
          </div>
        )
      })}
      {mindmaps.length === 0 ? <div className="empty">导图尚未生成</div> : null}
    </>
  )
}
