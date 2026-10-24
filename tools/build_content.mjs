#!/usr/bin/env node
/**
 * 把 知识点/ 下的源数据校验后打包进 App。
 *
 * 源文件（知识点/）：
 *   subjects.json    Subject[]（五大学科）
 *   questions.json   Question[]
 *   timeline.json    TimelineEvent[]
 *   mindmaps.json    MindTree[]
 *
 * 输出（src/data/）：
 *   subjects.json questions.json timeline.json mindmaps.json meta.json
 *
 * 用法：node tools/build_content.mjs [--ocr]
 *   --ocr 额外校验每个 quote 能否在 原始OCR/ 里找到（防改写教材表述）
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const appRoot = path.resolve(here, '..')
const base = path.resolve(appRoot, '..')
const SRC = path.join(base, '知识点')
const DST = path.join(appRoot, 'src', 'data')
const OCR = path.join(base, '原始OCR')

const withOcr = process.argv.includes('--ocr')
const errors = []
const warns = []

const read = (f, fallback) => {
  const p = path.join(SRC, f)
  if (!fs.existsSync(p)) return fallback
  return JSON.parse(fs.readFileSync(p, 'utf8'))
}

const subjectDir = path.join(SRC, 'subjects')
const subjects = fs.existsSync(subjectDir)
  ? fs
      .readdirSync(subjectDir)
      .filter((f) => f.endsWith('.json'))
      .map((f) => JSON.parse(fs.readFileSync(path.join(subjectDir, f), 'utf8')))
  : read('subjects.json', [])
const questions = read('questions.json', [])
const shizheng = read('questions_shizheng.json', [])
questions.push(...shizheng)
questions.push(...read('questions_mcq.json', []))
questions.push(...read('questions_mcq2.json', []))
questions.push(...read('questions_hats.json', []))
questions.push(...read('questions_zhenti.json', []))
// 判断题库：背诵卡与判断题合并后的唯一来源；旧判断题与旧背诵卡（type=card）都不再打包
questions.splice(0, questions.length, ...questions.filter((q) => q.type !== 'judge' && q.type !== 'card'))
questions.push(...read('questions_panduan.json', []))
// 专题按文件拆分：知识点/parts/<subject>-<no>.json，按文件名排序合并
const partsDir = path.join(SRC, 'parts')
for (const s of subjects) {
  if (s.parts?.length) continue
  if (!fs.existsSync(partsDir)) continue
  s.parts = fs
    .readdirSync(partsDir)
    .filter((f) => f.startsWith(s.id + '-') && f.endsWith('.json'))
    .sort()
    .map((f) => JSON.parse(fs.readFileSync(path.join(partsDir, f), 'utf8')))
}

const timeline = read('timeline.json', [])
const mindmaps = read('mindmaps.json', [])

const LETTER = /^[A-D]$/
const seenPoint = new Set()
const seenQ = new Set()

let pointCount = 0
for (const s of subjects) {
  if (!s.id || !s.parts) errors.push(`学科缺少 id/parts: ${JSON.stringify(s.id)}`)
  for (const p of s.parts ?? []) {
    if (!p.id) errors.push(`专题缺少 id: ${s.id}/${p.title}`)
    if (!p.points?.length) warns.push(`专题无考点: ${p.id}`)
    for (const pt of p.points ?? []) {
      pointCount++
      if (!pt.id || seenPoint.has(pt.id)) errors.push(`考点 id 缺失或重复: ${pt.id}`)
      seenPoint.add(pt.id)
      for (const k of ['title', 'quote', 'core']) {
        if (!pt[k] || !String(pt[k]).trim()) errors.push(`考点 ${pt.id} 缺少 ${k}`)
      }
      if (!Array.isArray(pt.refs) || pt.refs.length === 0) errors.push(`考点 ${pt.id} 缺少 refs`)
      if (!Array.isArray(pt.detail)) errors.push(`考点 ${pt.id} detail 必须是数组`)
    }
  }
}

for (const q of questions) {
  if (!q.id || seenQ.has(q.id)) errors.push(`题目 id 缺失或重复: ${q.id}`)
  seenQ.add(q.id)
  if (!q.subject) errors.push(`题目 ${q.id} 缺少 subject`)
  if (!q.stem?.trim()) errors.push(`题目 ${q.id} 缺少题干`)

  if (q.type === 'single') {
    if (!LETTER.test(q.answer)) errors.push(`单选 ${q.id} 答案不是 A-D: ${q.answer}`)
    if (q.options?.length !== 4) errors.push(`单选 ${q.id} 选项不是 4 个`)
  } else if (q.type === 'multi') {
    if (!Array.isArray(q.answer) || q.answer.length < 2) errors.push(`多选 ${q.id} 至少两个正确项`)
    for (const a of q.answer ?? []) if (!LETTER.test(a)) errors.push(`多选 ${q.id} 含非法选项 ${a}`)
  } else if (q.type === 'judge') {
    if (typeof q.answer !== 'boolean') errors.push(`判断 ${q.id} 答案必须是布尔值`)
  } else if (q.type === 'card') {
    if (typeof q.answer !== 'string') errors.push(`背诵卡 ${q.id} 答案必须是字符串`)
  } else {
    errors.push(`题目 ${q.id} 类型非法: ${q.type}`)
  }

  if (q.type === 'single' || q.type === 'multi') {
    const opts = (q.options ?? []).map((o) => o.trim()[0])
    const right = q.type === 'multi' ? q.answer : [q.answer]
    for (const r of right) if (!opts.includes(r)) errors.push(`题目 ${q.id} 答案 ${r} 不在选项内`)
    for (const [k, d] of Object.entries(q.distractors ?? {})) {
      if (right.includes(k)) errors.push(`题目 ${q.id} 的干扰项 ${k} 其实是正确项`)
      if (!d.why || !d.trap) errors.push(`题目 ${q.id} 干扰项 ${k} 缺少 why/trap`)
    }
    const rightCount = Array.isArray(q.answer) ? q.answer.length : 1
    const missing = (q.options ?? []).length - rightCount - Object.keys(q.distractors ?? {}).length
    if (missing > 0 && q.source !== 'textbook') warns.push(`题目 ${q.id} 有 ${missing} 个错误项没写解析`)
  }
  if (!q.explain?.trim()) warns.push(`题目 ${q.id} 没有解析`)
}

if (withOcr) {
  const corpus = fs.existsSync(OCR)
    ? fs
        .readdirSync(OCR)
        .filter((f) => f.endsWith('.md') && !f.includes('.clean.'))
        .map((f) => fs.readFileSync(path.join(OCR, f), 'utf8'))
        .join('\n')
    : ''
  const norm = (s) => s.replace(/[\s，。、；：！？（）()“”‘’"'《》·．.,;:!?—\-]/g, '')
  const flat = norm(corpus)

  // 用 6 字滑窗做模糊匹配：容忍个别 OCR 错字，但能抓住整句改写
  const SHINGLE = 6
  const grams = new Set()
  for (let i = 0; i + SHINGLE <= flat.length; i++) grams.add(flat.slice(i, i + SHINGLE))

  let miss = 0
  for (const s of subjects)
    for (const p of s.parts ?? [])
      for (const pt of p.points ?? []) {
        if (pt.quoteExempt || s.id === 'shizheng') continue
        // 表格型考点允许用“｜”分段，逐段与原文比对
        const frags = pt.quote.split(/[｜|]/).map(norm).filter((f) => f.length >= SHINGLE * 2)
        if (!frags.length) continue
        for (const q of frags) {
          let hit = 0
          let total = 0
          for (let i = 0; i + SHINGLE <= q.length; i++) {
            total++
            if (grams.has(q.slice(i, i + SHINGLE))) hit++
          }
          const ratio = total ? hit / total : 0
          if (ratio < 0.8) {
            miss++
            warns.push(`原句与 OCR 差异较大（命中 ${(ratio * 100).toFixed(0)}%）: ${pt.id} 「${q.slice(0, 26)}…」`)
            break
          }
        }
      }
  console.log(`原句比对：${pointCount - miss}/${pointCount} 命中（阈值 80%）`)
}

const counts = {}
for (const q of questions) counts[q.subject] = (counts[q.subject] ?? 0) + 1

if (errors.length) {
  console.error(`\n✗ 校验未通过（${errors.length}）：`)
  for (const e of errors.slice(0, 40)) console.error('  - ' + e)
  process.exit(1)
}

fs.mkdirSync(DST, { recursive: true })
const write = (name, data) =>
  fs.writeFileSync(path.join(DST, name), JSON.stringify(data, null, 2) + '\n', 'utf8')

write('subjects.json', subjects)
write('questions.json', questions)
write('timeline.json', timeline)
write('mindmaps.json', mindmaps)
write('meta.json', {
  generatedAt: new Date().toISOString(),
  points: pointCount,
  questions: questions.length,
  bySubject: counts,
})

console.log(`✓ 打包完成：${pointCount} 个考点，${questions.length} 道题`)
console.log('  分学科题量：', counts)
for (const w of warns.slice(0, 20)) console.log('  ! ' + w)
if (warns.length > 20) console.log(`  … 另有 ${warns.length - 20} 条提示`)
