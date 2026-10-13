// Cloudflare Worker: public ingest for door ballots + internal publish endpoint for the Python server.
//   POST /api/ballots   {texts: string[], turnstile?: string} → 202 {receipt, duplicate}
//   PUT  /internal/publish/<path>   (Bearer PUBLISH_TOKEN) → writes JSON to the PUBLIC bucket (served via CDN)
//   GET  /api/health
// Signature verification is NOT done here (E-521 lives in Python); this layer only absorbs the peak cheaply.
import { assemble, BallotError, isOfficial2026, sectionKey } from '../../shared/ballot'

export interface Env {
  BALLOTS: R2Bucket
  PUBLIC: R2Bucket
  SUBMISSIONS: Queue<SubmissionMessage>
  LIMITER: { limit(o: { key: string }): Promise<{ success: boolean }> }
  ALLOW_TEST_BALLOTS: string
  IP_SALT: string
  PUBLISH_TOKEN: string
  TURNSTILE_SECRET?: string
}

export interface SubmissionMessage {
  finalHash: string
  sectionKey: string
  rawKey: string
  texts: string[] // QR texts travel in the message (a few KB) so the consumer needs no R2 read
  receivedAt: string
  ipHash: string
}

const MAX_BODY = 64 * 1024
const CORS = { 'access-control-allow-origin': '*', 'access-control-allow-methods': 'POST, OPTIONS', 'access-control-allow-headers': 'content-type' }

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', ...CORS } })

async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('')
}

async function turnstileOk(env: Env, token: string | undefined, ip: string): Promise<boolean> {
  if (!env.TURNSTILE_SECRET) return true // optional until the widget is in the app
  if (!token) return false
  const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST', body: new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: token, remoteip: ip }),
  })
  return ((await r.json()) as { success: boolean }).success
}

export async function handleSubmit(req: Request, env: Env): Promise<Response> {
  const ip = req.headers.get('cf-connecting-ip') ?? 'unknown'
  if (!(await env.LIMITER.limit({ key: ip })).success) return json(429, { error: 'Muitos envios seguidos. Tente de novo em um minuto.' })
  if (Number(req.headers.get('content-length') ?? 0) > MAX_BODY) return json(413, { error: 'Envio grande demais.' })
  let body: { texts?: unknown; turnstile?: string }
  try { body = await req.json() } catch { return json(400, { error: 'JSON inválido.' }) }
  const texts = body.texts
  if (!Array.isArray(texts) || !texts.length || texts.length > 40 || !texts.every(t => typeof t === 'string' && t.length < 4000))
    return json(400, { error: 'Envie os textos dos QR Codes do boletim.' })
  if (!(await turnstileOk(env, body.turnstile, ip))) return json(403, { error: 'Verificação anti-robô falhou.' })

  let ballot
  try { ballot = await assemble(texts) } catch (e) {
    return json(422, { error: e instanceof BallotError ? e.message : 'Boletim inválido.' })
  }
  if (!isOfficial2026(ballot) && env.ALLOW_TEST_BALLOTS !== '1')
    return json(422, { error: 'Só boletins oficiais de 2026 entram na conferência.' })

  const key = sectionKey(ballot.fields)
  const rawKey = `raw/${key.replaceAll(':', '/')}/${ballot.finalHash}.json`
  const duplicate = (await env.BALLOTS.head(rawKey)) !== null
  if (!duplicate) await env.BALLOTS.put(rawKey, JSON.stringify(ballot.texts), { httpMetadata: { contentType: 'application/json' } })
  const day = new Date().toISOString().slice(0, 10)
  // Every submission is queued, even duplicates: independent senders of the same ballot are witnesses.
  await env.SUBMISSIONS.send({ finalHash: ballot.finalHash, sectionKey: key, rawKey, texts: ballot.texts, receivedAt: new Date().toISOString(), ipHash: await sha256(`${ip}|${day}|${env.IP_SALT}`) })
  return json(202, { receipt: ballot.finalHash.slice(0, 16), section: key, duplicate })
}

async function handlePublish(req: Request, env: Env, path: string): Promise<Response> {
  if (req.headers.get('authorization') !== `Bearer ${env.PUBLISH_TOKEN}` || !env.PUBLISH_TOKEN) return json(401, { error: 'unauthorized' })
  if (!/^[a-z0-9/_.:-]+\.json$/.test(path) || path.includes('..')) return json(400, { error: 'bad path' })
  await env.PUBLIC.put(path, req.body, { httpMetadata: { contentType: 'application/json', cacheControl: 'public, max-age=30' } })
  return new Response(null, { status: 204, headers: CORS })
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url)
    if (req.method === 'OPTIONS') return new Response(null, { headers: CORS })
    if (url.pathname === '/api/ballots' && req.method === 'POST') return handleSubmit(req, env)
    if (url.pathname.startsWith('/internal/publish/') && req.method === 'PUT') return handlePublish(req, env, url.pathname.slice('/internal/publish/'.length))
    if (url.pathname === '/api/health') return json(200, { ok: true })
    return json(404, { error: 'not found' })
  },
} satisfies ExportedHandler<Env>
