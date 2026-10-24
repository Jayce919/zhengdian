/** 进度码：把全部进度压缩后编码成一段可复制文本，跨设备粘贴即可同步。 */

const PREFIX = 'ZZ1'
const HEAD = `${PREFIX}:g:` // gzip
const HEAD_RAW = `${PREFIX}:r:` // 未压缩（环境不支持压缩时）

function b64urlEncode(bytes: Uint8Array): string {
  let bin = ''
  const chunk = 0x8000
  for (let i = 0; i < bytes.length; i += chunk) {
    bin += String.fromCharCode(...bytes.subarray(i, i + chunk))
  }
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function b64urlDecode(s: string): Uint8Array {
  const b64 = s.replace(/-/g, '+').replace(/_/g, '/')
  const pad = b64.length % 4 ? '='.repeat(4 - (b64.length % 4)) : ''
  const bin = atob(b64 + pad)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out
}

async function gzip(bytes: Uint8Array): Promise<Uint8Array> {
  const stream = new Blob([bytes as unknown as BlobPart]).stream().pipeThrough(new CompressionStream('gzip'))
  return new Uint8Array(await new Response(stream).arrayBuffer())
}

async function gunzip(bytes: Uint8Array): Promise<Uint8Array> {
  const stream = new Blob([bytes as unknown as BlobPart]).stream().pipeThrough(new DecompressionStream('gzip'))
  return new Uint8Array(await new Response(stream).arrayBuffer())
}

const canCompress = () =>
  typeof CompressionStream !== 'undefined' && typeof DecompressionStream !== 'undefined'

/** 进度 JSON → 进度码 */
export async function encodeProgress(json: string): Promise<string> {
  const raw = new TextEncoder().encode(json)
  if (!canCompress()) return HEAD_RAW + b64urlEncode(raw)
  return HEAD + b64urlEncode(await gzip(raw))
}

/** 进度码 → 进度 JSON（格式不对会抛错） */
export async function decodeProgress(code: string): Promise<string> {
  const text = code.replace(/\s+/g, '')
  if (!text.startsWith(`${PREFIX}:`)) throw new Error('不是本应用的进度码')
  if (text.startsWith(HEAD)) {
    const bytes = await gunzip(b64urlDecode(text.slice(HEAD.length)))
    return new TextDecoder().decode(bytes)
  }
  if (text.startsWith(HEAD_RAW)) {
    return new TextDecoder().decode(b64urlDecode(text.slice(HEAD_RAW.length)))
  }
  throw new Error('进度码版本无法识别')
}

export interface ProgressSummary {
  answered: number
  mistakes: number
  exams: number
  days: number
}

export function summarize(json: string): ProgressSummary | null {
  try {
    const p = JSON.parse(json)
    return {
      answered: Object.keys(p.answers ?? {}).length,
      mistakes: Object.values((p.flags ?? {}) as Record<string, { mistake?: number }>).filter((f) => (f.mistake ?? 0) > 0).length,
      exams: (p.exams ?? []).length,
      days: p.streak?.days ?? 0,
    }
  } catch {
    return null
  }
}
