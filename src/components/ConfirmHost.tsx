import { useEffect, useReducer } from 'react'
import { getPendingConfirm, resolveConfirm, subscribeConfirm } from '../lib/confirm'

export default function ConfirmHost() {
  const [, force] = useReducer((x: number) => x + 1, 0)
  const pending = getPendingConfirm()

  useEffect(() => subscribeConfirm(() => force()), [])

  useEffect(() => {
    if (!pending) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') resolveConfirm(false)
      if (e.key === 'Enter') resolveConfirm(true)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [pending])

  if (!pending) return null

  return (
    <div className="dialog-backdrop" onClick={() => resolveConfirm(false)}>
      <div
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="dialog-title">{pending.title}</h2>
        {pending.message ? <p>{pending.message}</p> : null}
        <div className="dialog-actions">
          <button className="btn" onClick={() => resolveConfirm(false)}>
            {pending.cancelText ?? '取消'}
          </button>
          <button
            className={`btn ${pending.danger ? 'danger' : 'primary'}`}
            autoFocus
            onClick={() => resolveConfirm(true)}
          >
            {pending.okText ?? '确定'}
          </button>
        </div>
      </div>
    </div>
  )
}
