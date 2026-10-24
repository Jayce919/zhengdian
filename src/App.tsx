import { useCallback, useEffect, useRef } from 'react'
import { useRoute, segments } from './lib/router'
import { requestLeave } from './lib/navGuard'
import { useProgress } from './lib/store'
import Home from './pages/Home'
import Practice from './pages/Practice'
import Exam from './pages/Exam'
import Theory from './pages/Theory'
import MindMap from './pages/MindMap'
import TimelinePage from './pages/Timeline'
import Stats from './pages/Stats'
import Settings from './pages/Settings'
import Icon from './components/Icon'
import ConfirmHost from './components/ConfirmHost'

const NAV = [
  { key: 'home', label: '首页', ico: 'home' },
  { key: 'practice', label: '刷题', ico: 'practice' },
  { key: 'theory', label: '理论', ico: 'theory' },
  { key: 'mind', label: '导图', ico: 'mind' },
  { key: 'timeline', label: '时间轴', ico: 'timeline' },
] as const

const TITLES: Record<string, [string, string]> = {
  home: ['政点', '考研政治 · 选择题专项'],
  practice: ['刷题', '按学科与题型练习'],
  exam: ['模拟考试', '16 单选 + 17 多选'],
  theory: ['理论与表述', '教材原句 · 易混对比 · 提法速查'],
  mind: ['思维导图', '按专题展开'],
  timeline: ['时间轴', '史纲主线 · 会议 · 著作'],
  stats: ['统计', '正确率与模考记录'],
  settings: ['设置', '进度与偏好'],
}

export default function App() {
  const [route, nav] = useRoute()
  // 所有跳转都过一道拦截：练习/考试进行中先确认再离开
  const go = useCallback(
    (to: string) => {
      requestLeave(to, () => nav(to))
    },
    [nav],
  )
  const progress = useProgress()
  const seg = segments(route)
  const page = seg[0] || 'home'

  useEffect(() => {
    document.documentElement.dataset.theme = progress.settings.theme
  }, [progress.settings.theme])

  // 把顶部栏实际高度写进 --header-h，供吸顶元素（时间轴年代）对齐
  const wrapRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const apply = () => {
      const stickyTop = parseFloat(getComputedStyle(el).top) || 0
      const h = stickyTop + el.offsetHeight
      document.documentElement.style.setProperty('--header-h', `${Math.round(h)}px`)
    }
    apply()
    const ro = new ResizeObserver(apply)
    ro.observe(el)
    window.addEventListener('resize', apply)
    return () => {
      ro.disconnect()
      window.removeEventListener('resize', apply)
    }
  }, [])

  const [title, sub] = TITLES[page] ?? TITLES.home
  const active = NAV.some((n) => n.key === page) ? page : ''

  return (
    <div className="app">
      <div className="topbar-wrap" ref={wrapRef}>
      <header className="topbar">
        <div>
          <h1>{title}</h1>
          <div className="sub">{sub}</div>
        </div>
        <div className="spacer" />
        <button className="iconbtn" title="统计" onClick={() => go('stats')}>
          <Icon name="stats" size={19} />
        </button>
        <button className="iconbtn" title="设置" onClick={() => go('settings')}>
          <Icon name="settings" size={19} />
        </button>
      </header>
      </div>

      <main className="main">
        {page === 'home' && <Home nav={go} />}
        {page === 'practice' && <Practice nav={go} key={seg.slice(1).join('/')} initial={seg.slice(1)} />}
        {page === 'exam' && <Exam nav={go} />}
        {page === 'theory' && <Theory nav={go} seg={seg.slice(1)} />}
        {page === 'mind' && <MindMap nav={go} seg={seg.slice(1)} />}
        {page === 'timeline' && <TimelinePage seg={seg.slice(1)} />}
        {page === 'stats' && <Stats nav={go} />}
        {page === 'settings' && <Settings nav={go} />}
      </main>

      <nav className="bottomnav" aria-label="主导航">
        <div className="rail-brand">
          <span className="seal">政</span>
          <span>考研政治</span>
        </div>
        {NAV.map((n) => (
          <button key={n.key} aria-current={active === n.key} onClick={() => go(n.key)}>
            <span className="ico">
              <Icon name={n.ico} size={22} />
            </span>
            <span>{n.label}</span>
          </button>
        ))}
      </nav>

      <ConfirmHost />
    </div>
  )
}
