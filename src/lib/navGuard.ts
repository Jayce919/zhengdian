/**
 * 页面内导航拦截：练习、考试进行中离开前先确认，避免误触底部导航丢掉整场作答。
 *
 * 页面自己用 setNavGuard 注册一个「能否离开」的判断，卸载时清掉；
 * App 的跳转入口统一走 requestLeave()，由拦截器决定什么时候真正跳。
 * 拦截器可以是异步的（弹应用内确认框），确认后自己调用 proceed。
 */

type Proceed = () => void
type Guard = (to: string, proceed: Proceed) => void

let guard: Guard | null = null

export function setNavGuard(fn: Guard | null) {
  guard = fn
}

/** 请求离开当前页面：没有拦截器就直接走 */
export function requestLeave(to: string, proceed: Proceed) {
  if (!guard) {
    proceed()
    return
  }
  guard(to, proceed)
}
