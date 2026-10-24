#!/usr/bin/env node
/**
 * 从 知识点/subjects.json 生成可导出 PDF 的维护版 Markdown。
 * 输出：知识点/政治_知识点背诵与速查_维护版.md
 *
 * 排版沿用 study-notes 的约定：
 *   - 条目写成 `- **关键词**：内容`
 *   - 章之间用 --- 分隔
 *   - 目录用 > [!abstract]+ 默认展开
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const base = path.resolve(here, '..', '..')
const SRC = path.join(here, '..', 'src', 'data', 'subjects.json')
const OUT = path.join(base, '知识点', '政治_知识点背诵与速查_维护版.md')

const subjects = JSON.parse(fs.readFileSync(SRC, 'utf8'))
const KEYWORDS = ['根本', '本质', '前提', '决定', '源泉', '根源', '第一', '标志', '里程碑']
const CN = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']

const clean = (s) => String(s ?? '').replace(/\s+/g, ' ').trim()

const lines = []
lines.push('---')
lines.push('cssclasses: study-notes')
lines.push('tags: [考研政治]')
lines.push('---')
lines.push('')
lines.push('# 政治知识点背诵与速查')
lines.push('')
lines.push('> 依据肖秀荣《背诵手册》上、下册与《精讲精练》整理，表述以教材原句为准。')
lines.push('')
lines.push('> [!abstract]+ 目录')
subjects.forEach((s, si) => {
  lines.push(`> - **第${CN[si]}部分 ${s.name}**`)
  for (const p of s.parts) lines.push(`>   - [[#${p.no} ${p.title}]]`)
})
lines.push('')

subjects.forEach((s, si) => {
  lines.push('---')
  lines.push('')
  lines.push(`## 第${CN[si]}部分 ${s.name}`)
  lines.push('')
  lines.push(`> 大纲占比约 ${s.examShare}%。`)
  lines.push('')

  for (const p of s.parts) {
    lines.push(`### ${p.no} ${p.title}`)
    lines.push('')
    if (p.summary) {
      lines.push(`*${clean(p.summary)}*`)
      lines.push('')
    }
    for (const pt of p.points) {
      lines.push(`- **${clean(pt.title)}**：${clean(pt.core)}`)
      if (pt.quote && clean(pt.quote) !== clean(pt.core)) {
        lines.push(`  - 原文：${clean(pt.quote)}`)
      }
      for (const d of pt.detail) lines.push(`  - ${clean(d)}`)
      if (pt.confusions?.length) {
        lines.push('  - 易混：')
        for (const c of pt.confusions) lines.push(`    - **${c.a}** ↔ **${c.b}**：${clean(c.diff)}`)
      }
      if (pt.refs?.length) lines.push(`  - 出处：${pt.refs.join('；')}`)
    }
    lines.push('')
  }
})

lines.push('---')
lines.push('')
lines.push('## 提法速查')
lines.push('')
for (const k of KEYWORDS) {
  const hits = []
  for (const s of subjects)
    for (const p of s.parts)
      for (const pt of p.points)
        if (pt.keywords.includes(k) || pt.core.includes(k)) hits.push(pt)
  if (!hits.length) continue
  lines.push(`### “${k}”的提法`)
  lines.push('')
  for (const pt of hits) lines.push(`- **${clean(pt.title)}**：${clean(pt.core)}`)
  lines.push('')
}

fs.mkdirSync(path.dirname(OUT), { recursive: true })
fs.writeFileSync(OUT, lines.join('\n'), 'utf8')
console.log(`✓ 已生成 ${OUT}`)
