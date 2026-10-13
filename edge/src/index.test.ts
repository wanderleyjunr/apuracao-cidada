import { readFileSync } from 'node:fs'
import { expect, it } from 'vitest'
import worker, { type Env, type SubmissionMessage } from './index'

const ballots2022: string[][] = JSON.parse(readFileSync(new URL('../../fixtures/ballots-2022-abroad.json', import.meta.url), 'utf8'))

function fakeEnv(over: Partial<Env> = {}) {
  const objects = new Map<string, string>()
  const sent: SubmissionMessage[] = []
  const env = {
    BALLOTS: { head: async (k: string) => (objects.has(k) ? {} : null), put: async (k: string, v: string) => void objects.set(k, v) },
    PUBLIC: { put: async (k: string) => void objects.set(k, 'published') },
    SUBMISSIONS: { send: async (m: SubmissionMessage) => void sent.push(m) },
    LIMITER: { limit: async () => ({ success: true }) },
    ALLOW_TEST_BALLOTS: '1', IP_SALT: 'salt', PUBLISH_TOKEN: 'tok',
    ...over,
  } as unknown as Env
  return { env, objects, sent }
}

const post = (body: unknown) => new Request('https://x/api/ballots', { method: 'POST', body: JSON.stringify(body), headers: { 'cf-connecting-ip': '1.2.3.4' } })

it('accepts a valid ballot, stores it once and queues every submission', async () => {
  const { env, objects, sent } = fakeEnv()
  const r1 = await worker.fetch(post({ texts: ballots2022[0] }), env)
  const r2 = await worker.fetch(post({ texts: ballots2022[0] }), env)
  expect(r1.status).toBe(202)
  expect(await r2.json()).toMatchObject({ duplicate: true })
  expect(objects.size).toBe(1)
  expect(sent).toHaveLength(2)
  expect(sent[0].ipHash).not.toContain('1.2.3.4')
  expect(sent[0].sectionKey).toBe('1:zz:30198:1:265')
})

it('rejects tampered ballots and non-2026 ballots in production', async () => {
  const { env } = fakeEnv()
  const bad = await worker.fetch(post({ texts: [ballots2022[0][0].replace('22:315', '22:316')] }), env)
  expect(bad.status).toBe(422)
  const prod = fakeEnv({ ALLOW_TEST_BALLOTS: '0' })
  expect((await worker.fetch(post({ texts: ballots2022[0] }), prod.env)).status).toBe(422)
})

it('rate limits and validates input', async () => {
  const { env } = fakeEnv({ LIMITER: { limit: async () => ({ success: false }) } })
  expect((await worker.fetch(post({ texts: ballots2022[0] }), env)).status).toBe(429)
  expect((await worker.fetch(post({ texts: 'x' }), fakeEnv().env)).status).toBe(400)
})

it('publish requires the token and a safe path', async () => {
  const { env, objects } = fakeEnv()
  const put = (path: string, auth: string) => new Request(`https://x/internal/publish/${path}`, { method: 'PUT', body: '{}', headers: { authorization: auth } })
  expect((await worker.fetch(put('sections/2/mg/53112/170/37.json', 'Bearer nope'), env)).status).toBe(401)
  expect((await worker.fetch(put('sections/2/mg/53112/170/37.json', 'Bearer tok'), env)).status).toBe(204)
  expect(objects.has('sections/2/mg/53112/170/37.json')).toBe(true)
})
