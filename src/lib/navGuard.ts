/**
 * 页面内导航拦截：练习、考试进行中离开前先确认，避免误触底部导航丢掉整场作答。
 *
 * 页面自己用 setNavGuard 注册一个「能否离开」的判断，卸载时清掉；
 * App 的跳转入口统一走 canLeave()，返回 false 就不跳。
 */

type Guard = (to: string) => boolean

let guard: Guard | null = null

export function setNavGuard(fn: Guard | null) {
  guard = fn
}

/** true 表示可以离开当前页面 */
export function canLeave(to: string): boolean {
  if (!guard) return true
  return guard(to)
}
