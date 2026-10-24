import { useRef, useState } from 'react'
import { actions, useProgress } from '../lib/store'
import { decodeProgress, encodeProgress, summarize } from '../lib/syncCode'
import { confirmDialog } from '../lib/confirm'

export default function Settings({ nav }: { nav: (to: string) => void }) {
  const p = useProgress()
  const [code, setCode] = useState('')
  const [inCode, setInCode] = useState('')
  const [json, setJson] = useState('')
  const [msg, setMsg] = useState('')
  const [summary, setSummary] = useState<ReturnType<typeof summarize>>(null)
  const codeRef = useRef<HTMLTextAreaElement>(null)

  async function makeCode() {
    setMsg('')
    try {
      const c = await encodeProgress(actions.exportJson())
      setCode(c)
      setSummary(summarize(actions.exportJson()))
      setMsg('已生成，复制后到另一台设备粘贴导入')
    } catch {
      setMsg('生成失败，请重试')
    }
  }

  async function copyCode() {
    if (!code) return
    try {
      await navigator.clipboard.writeText(code)
      setMsg('进度码已复制到剪贴板')
    } catch {
      codeRef.current?.select()
      setMsg('无法自动复制，已全选，请手动复制')
    }
  }

  async function importCode() {
    if (!inCode.trim()) return
    if (
      !(await confirmDialog({
        title: '导入进度码？',
        message: '导入会覆盖本机全部做题进度、错题本和模考记录。',
        okText: '覆盖导入',
        danger: true,
      }))
    )
      return
    try {
      const text = await decodeProgress(inCode)
      const s = summarize(text)
      if (!s) throw new Error('bad')
      actions.importJson(text)
      setMsg(`导入成功：${s.answered} 道做题记录、${s.mistakes} 道错题、${s.exams} 次模考`)
      setInCode('')
    } catch {
      setMsg('导入失败：进度码不完整或不是本应用的进度码')
    }
  }

  return (
    <>
      <div className="card">
        <h2>多端同步</h2>
        <div className="muted small">
          在一台设备上点「生成进度码」，把整段文字复制到另一台设备粘贴导入，做题记录、错题本、模考成绩、连续天数会完全一致。
        </div>
        <div className="toolbar">
          <button className="btn sm primary" onClick={makeCode}>
            生成进度码
          </button>
          <button className="btn sm" onClick={copyCode} disabled={!code}>
            复制
          </button>
        </div>
        <textarea
          ref={codeRef}
          className="io"
          style={{ minHeight: 96 }}
          value={code}
          readOnly
          placeholder="生成后进度码显示在这里"
          onFocus={(e) => e.currentTarget.select()}
        />
        {summary ? (
          <div className="muted small">
            包含 {summary.answered} 道做题记录 · {summary.mistakes} 道错题 · {summary.exams} 次模考 · 连续 {summary.days} 天
          </div>
        ) : null}
      </div>

      <div className="card">
        <h2>导入进度码</h2>
        <div className="muted small">把另一台设备生成的进度码粘贴到这里，导入后本机进度将被完全覆盖。</div>
        <textarea
          className="io"
          style={{ minHeight: 96 }}
          value={inCode}
          onChange={(e) => setInCode(e.target.value)}
          placeholder="粘贴进度码，形如 ZZ1:g:..."
        />
        <div className="toolbar">
          <button className="btn sm primary" onClick={importCode} disabled={!inCode.trim()}>
            导入并覆盖
          </button>
          <button
            className="btn sm"
            onClick={() => {
              setInCode('')
              setMsg('')
            }}
            disabled={!inCode}
          >
            清空输入
          </button>
        </div>
      </div>

      <div className="card">
        <h2>偏好</h2>
        <div className="row" style={{ marginTop: 8 }}>
          <span>深色模式</span>
          <span className="spacer" />
          <button
            className="chip"
            aria-pressed={p.settings.theme === 'dark'}
            onClick={() => actions.setSettings({ theme: p.settings.theme === 'dark' ? 'light' : 'dark' })}
          >
            {p.settings.theme === 'dark' ? '已开启' : '关闭'}
          </button>
        </div>
        <div className="row wrap" style={{ marginTop: 12 }}>
          <span>每日新题</span>
          <span className="spacer" />
          {[15, 30, 50, 80].map((n) => (
            <button
              key={n}
              className="chip"
              aria-pressed={p.settings.newPerDay === n}
              onClick={() => actions.setSettings({ newPerDay: n })}
            >
              {n}
            </button>
          ))}
        </div>
        <div className="row wrap" style={{ marginTop: 12 }}>
          <span>模考默认计时</span>
          <span className="spacer" />
          {[40, 50, 60, 0].map((n) => (
            <button
              key={n}
              className="chip"
              aria-pressed={p.settings.timerMinutes === n}
              onClick={() => actions.setSettings({ timerMinutes: n })}
            >
              {n === 0 ? '不限时' : `${n} 分`}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <h2>备份与重置</h2>
        <div className="muted small">进度保存在本机浏览器。进度码适合手机与平板之间同步；JSON 备份适合留档。</div>
        <div className="toolbar">
          <button
            className="btn sm"
            onClick={() => {
              setJson(actions.exportJson())
              setMsg('已生成 JSON 备份，可复制保存')
            }}
          >
            导出 JSON
          </button>
          <button
            className="btn sm"
            onClick={async () => {
              const ok = await confirmDialog({
                title: '导入 JSON？',
                message: '导入会覆盖当前全部进度、错题本和模考记录。',
                okText: '覆盖导入',
                danger: true,
              })
              if (!ok) return
              try {
                actions.importJson(json)
                setMsg('导入成功')
              } catch {
                setMsg('导入失败：文本格式不正确')
              }
            }}
            disabled={!json.trim()}
          >
            导入 JSON
          </button>
          <button
            className="btn sm"
            onClick={async () => {
              const ok = await confirmDialog({
                title: '清空全部进度？',
                message: '做题记录、错题本、模考成绩和连续天数都会删除，此操作不可撤销。',
                okText: '清空',
                danger: true,
              })
              if (!ok) return
              actions.reset()
              setMsg('已清空')
            }}
          >
            清空进度
          </button>
        </div>
        <textarea className="io" value={json} onChange={(e) => setJson(e.target.value)} placeholder="JSON 备份" />
        {msg ? <div className="muted small">{msg}</div> : null}
      </div>

      <div className="card">
        <h2>关于</h2>
        <div className="muted small" style={{ marginBottom: 8 }}>
          政点 —— 考研政治的选择题与背诵工具。
        </div>
        <div className="muted small">
          题库与知识点整理自肖秀荣《背诵手册》上下册、《精讲精练》与漫漫学《思维导图一本全》，表述以教材原文为准。
        </div>
        <div className="muted tiny" style={{ marginTop: 6 }}>
          时政整理截至 2026-10，考纲更新后需增量补充。
        </div>
        <div className="row" style={{ marginTop: 14 }}>
          <span className="muted small">作者</span>
          <a className="author-link" href="https://github.com/Jayce919" target="_blank" rel="noreferrer">
            Jayce919
          </a>
          <span className="spacer" />
          <span className="muted tiny">GitHub</span>
        </div>
        <button className="btn sm wide" style={{ marginTop: 12 }} onClick={() => nav('home')}>
          返回首页
        </button>
      </div>
    </>
  )
}
