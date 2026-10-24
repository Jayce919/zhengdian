/**
 * 应用内确认框。Android WebView 不一定显示 window.confirm，原生弹窗被静默取消，
 * 调用方只会看到「点了没反应」，所以统一换成应用内渲染的对话框。
 *
 * 用法：const ok = await confirmDialog({ title: '…', message: '…', okText: '离开' })
 * 渲染入口是 components/ConfirmHost.tsx，挂在 App 根节点。
 */

export type ConfirmOptions = {
  title: string
  message?: string
  okText?: string
  cancelText?: string
  danger?: boolean
}

type Pending = ConfirmOptions & { resolve: (ok: boolean) => void }

let pending: Pending | null = null
const listeners = new Set<() => void>()

function emit() {
  listeners.forEach((fn) => fn())
}

export function subscribeConfirm(fn: () => void) {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}

export function getPendingConfirm() {
  return pending
}

export function resolveConfirm(ok: boolean) {
  const cur = pending
  if (!cur) return
  pending = null
  emit()
  cur.resolve(ok)
}

export function confirmDialog(opts: ConfirmOptions): Promise<boolean> {
  // 已有弹窗未处理时按取消结算，避免新的请求被旧弹窗挡住
  if (pending) {
    const old = pending
    pending = null
    old.resolve(false)
  }
  return new Promise((resolve) => {
    pending = { ...opts, resolve }
    emit()
  })
}
