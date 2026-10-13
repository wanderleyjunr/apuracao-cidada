// Ballot (Boletim de Urna) QR Code parsing and validation — formats 1.5 and 6.0.
// Mirror of server/confere/ballot.py: both must pass the same fixtures. Used by app/ and edge/.
// Signature verification happens on the server. User-facing messages stay in Portuguese.

export class BallotError extends Error {}

export interface Part { index: number; total: number; version: string; data: string; hash: string; signature?: string }
export interface Office { CARG: string; votes: Record<string, number>; [field: string]: unknown }
export interface Ballot {
  version: string
  fields: Record<string, string> // UNFE, MUNI, ZONA, SECA, IDUE, ORIG, TURN, FASE, DTPL, HRFC...
  offices: Office[]
  finalHash: string
  signature?: string
  certificate?: string // hex of the concatenated QRCE parts
  texts: string[]
}

const QRBU_RE = /^QRBU:(\d+):(\d+) VRQR:(\S+)(?: VRCH:(\d+))? (.*?) HASH:([0-9A-F]{128})(?: ASSI:([0-9A-F]+))?$/s
const QRCE_RE = /^QRCE:(\d+):(\d+) (.*)$/s

export async function sha512(text: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-512', new TextEncoder().encode(text))
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase()
}

export function parsePart(text: string): Part {
  const m = QRBU_RE.exec(text.trim())
  if (!m) throw new BallotError('Este QR Code não é de um boletim de urna ou está incompleto. Leia de novo.')
  if (m[3] !== '1.5' && m[3] !== '6.0') throw new BallotError(`Formato de QR Code não suportado (versão ${m[3]}).`)
  return { index: +m[1], total: +m[2], version: m[3], data: m[5], hash: m[6], signature: m[7] }
}

/** hash1 = SHA-512(data1); hashN = SHA-512(data1 HASH:h1 ... dataN). Returns the signed (final) hash. */
export async function checkChain(parts: Part[]): Promise<string> {
  let acc = ''
  for (const p of parts) {
    const payload = acc ? `${acc} ${p.data}` : p.data
    if ((await sha512(payload)) !== p.hash)
      throw new BallotError(`O QR Code ${p.index} de ${p.total} não confere (hash inválido). O boletim pode ter sido alterado.`)
    acc = `${payload} HASH:${p.hash}`
  }
  return parts[parts.length - 1].hash
}

function records(data: string): [string, string][] {
  return data.split(' ').map(r => { const i = r.indexOf(':'); return [r.slice(0, i), r.slice(i + 1)] })
}

export function interpret(data: string): { fields: Record<string, string>; offices: Office[] } {
  const fields: Record<string, string> = {}
  const offices: Office[] = []
  let current: Office | null = null
  for (const [k, v] of records(data)) {
    if (k === 'CARG') { current = { CARG: v, votes: {} }; offices.push(current) }
    else if (!current) fields[k] = v
    else if (/^\d+$/.test(k)) current.votes[k] = (current.votes[k] ?? 0) + +v
    else current[k] = v
  }
  return { fields, offices }
}

export function checkSums(offices: Office[]): void {
  for (const o of offices) {
    if (o.TOTC === undefined) continue
    const total = ['NOMI', 'LEGC', 'BRAN', 'NULO'].reduce((s, k) => s + Number(o[k] ?? 0), 0)
    if (total !== Number(o.TOTC))
      throw new BallotError(`Cargo ${o.CARG}: a soma dos votos (${total}) não bate com o total apurado (${o.TOTC}).`)
  }
}

/** Partial scan state: which QR parts were read and which are missing. */
export function progress(texts: string[]): { total: number; read: number[]; certificate: boolean } {
  let total = 0
  const read: number[] = []
  let certificate = false
  for (const t of texts) {
    if (t.startsWith('QRCE:')) { certificate = true; continue }
    try { const p = parsePart(t); total = p.total; read.push(p.index) } catch { /* ignore unrelated QR */ }
  }
  return { total, read: [...new Set(read)].sort((a, b) => a - b), certificate }
}

export async function assemble(texts: string[]): Promise<Ballot> {
  const parts = new Map<number, Part>()
  const certs = new Map<number, { n: number; cert: string }>()
  const unique = [...new Set(texts.map(t => t.trim()))]
  for (const t of unique) {
    const ce = QRCE_RE.exec(t)
    if (ce) { certs.set(+ce[1], { n: +ce[2], cert: Object.fromEntries(records(ce[3])).CERT ?? '' }); continue }
    const p = parsePart(t)
    parts.set(p.index, p)
  }
  if (!parts.size) throw new BallotError('Nenhum QR Code de boletim encontrado.')
  const total = [...parts.values()][0].total
  const missing = Array.from({ length: total }, (_, i) => i + 1).filter(i => !parts.has(i))
  if (missing.length) throw new BallotError(`Faltam os QR Codes ${missing.join(', ')} de ${total}. Leia todos os do boletim.`)
  const ordered = Array.from({ length: total }, (_, i) => parts.get(i + 1)!)
  const finalHash = await checkChain(ordered)
  const { fields, offices } = interpret(ordered.map(p => p.data).join(' '))
  checkSums(offices)
  let certificate: string | undefined
  if (certs.size) {
    const n = [...certs.values()][0].n
    if (certs.size !== n) throw new BallotError('Faltam QR Codes do certificado da urna (QRCE) no fim do boletim.')
    certificate = Array.from({ length: n }, (_, i) => certs.get(i + 1)?.cert ?? '').join('')
  }
  return { version: ordered[0].version, fields, offices, finalHash, signature: ordered[total - 1].signature, certificate, texts: unique }
}

export const isOfficial2026 = (b: Ballot) => b.fields.FASE === 'O' && (b.fields.DTPL ?? '').startsWith('2026')

/** Canonical section key, same as server: "<turn>:<uf>:<municipality>:<zone>:<section>". */
export const sectionKey = (f: Record<string, string>) => `${f.TURN}:${f.UNFE.toLowerCase()}:${+f.MUNI}:${+f.ZONA}:${+f.SECA}`

// ---------- door × TSE comparison ----------

export type Votes = Record<string, number> // candidate number | 'BRAN' | 'NULO' -> count
export interface Difference { key: string; door: number; tse: number }

export function compare(door: Votes, tse: Votes): Difference[] {
  const keys = new Set([...Object.keys(door), ...Object.keys(tse)])
  return [...keys].map(key => ({ key, door: door[key] ?? 0, tse: tse[key] ?? 0 })).filter(d => d.door !== d.tse)
}

export function officeVotes(o: Office): Votes {
  return { ...o.votes, BRAN: Number(o.BRAN ?? 0), NULO: Number(o.NULO ?? 0) }
}
