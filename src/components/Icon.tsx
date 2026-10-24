type Name = 'home' | 'practice' | 'theory' | 'mind' | 'timeline' | 'stats' | 'settings' | 'chevron'

interface Shape {
  d: string
  fill?: boolean
}

/** 按原来的符号形状重绘：◉ ✎ ▤ ⌗ ⏱ */
const PATHS: Record<Name, Shape[]> = {
  // ◉ 同心圆
  home: [
    { d: 'M12 3.6a8.4 8.4 0 1 0 0 16.8 8.4 8.4 0 0 0 0-16.8z' },
    { d: 'M12 8.4a3.6 3.6 0 1 0 0 7.2 3.6 3.6 0 0 0 0-7.2z', fill: true },
  ],
  // ✎ 铅笔
  practice: [
    { d: 'M4.2 19.8l1-4 10.6-10.6a1.9 1.9 0 0 1 2.7 0l1.3 1.3a1.9 1.9 0 0 1 0 2.7L9.2 19.8z' },
    { d: 'M14.6 6.6l2.8 2.8' },
  ],
  // ▤ 横纹方块
  theory: [
    { d: 'M4.5 4.5h15v15h-15z' },
    { d: 'M7.5 9.2h9' },
    { d: 'M7.5 12h9' },
    { d: 'M7.5 14.8h9' },
  ],
  // ⌗ 田字格
  mind: [
    { d: 'M4.5 4.5h15v15h-15z' },
    { d: 'M12 4.5v15' },
    { d: 'M4.5 12h15' },
  ],
  // ⏱ 秒表
  timeline: [
    { d: 'M12 6.2a7.3 7.3 0 1 0 0 14.6 7.3 7.3 0 0 0 0-14.6z' },
    { d: 'M9.8 3.6h4.4' },
    { d: 'M12 3.6v2.6' },
    { d: 'M12 13.5V9.6' },
    { d: 'M12 13.5l3 1.8' },
  ],
  chevron: [{ d: 'M9.5 6.5 15 12l-5.5 5.5' }],
  stats: [
    { d: 'M5 19V11' },
    { d: 'M12 19V5' },
    { d: 'M19 19v-5' },
  ],
  settings: [
    { d: 'M12 15.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4z' },
    {
      d: 'M19.4 13.5a7.6 7.6 0 0 0 0-3l1.7-1.3-1.8-3.1-2 .8a7.6 7.6 0 0 0-2.6-1.5L14.4 3h-3.6l-.3 2.4a7.6 7.6 0 0 0-2.6 1.5l-2-.8L4 9.2l1.7 1.3a7.6 7.6 0 0 0 0 3L4 14.8l1.8 3.1 2-.8a7.6 7.6 0 0 0 2.6 1.5l.3 2.4h3.6l.3-2.4a7.6 7.6 0 0 0 2.6-1.5l2 .8 1.8-3.1z',
    },
  ],
}

export default function Icon({ name, size = 22 }: { name: Name; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name].map((s, i) => (
        <path key={i} d={s.d} fill={s.fill ? 'currentColor' : 'none'} stroke={s.fill ? 'none' : 'currentColor'} />
      ))}
    </svg>
  )
}
