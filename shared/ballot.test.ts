// SPDX-License-Identifier: MIT (shared/LICENSE). The rest of this repository is AGPL-3.0.
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { assemble, BallotError, compare, progress, sectionKey } from './ballot'

const fx = (n: string): string[][] => JSON.parse(readFileSync(new URL(`../fixtures/${n}`, import.meta.url), 'utf8'))
const BALLOTS_2022 = fx('ballots-2022-abroad.json')
const BALLOT_2026 = fx('ballot-2026-manual-simulated.json')

describe('assemble', () => {
  it.each(BALLOTS_2022)('accepts real 2022 ballot (%#)', async t => {
    const b = await assemble([t])
    expect(b.version).toBe('1.5')
    expect(b.fields.UNFE).toBe('ZZ')
  })

  it('accepts the 6.0 manual example in any order', async () => {
    const b = await assemble([...BALLOT_2026[0]].reverse())
    expect(b.version).toBe('6.0')
    expect(b.fields.IDUE).toBe('2250280')
    expect(b.offices.map(o => o.CARG).sort()).toEqual(['1', '3', '5', '6', '7'])
  })

  it('rejects a tampered vote', async () => {
    const t = BALLOTS_2022.find(x => x[0].includes('SECA:1693'))![0].replace(' 13:36 ', ' 13:37 ')
    await expect(assemble([t])).rejects.toThrow(/hash inválido/)
  })

  it('reports missing parts', async () => {
    await expect(assemble([BALLOT_2026[0][1]])).rejects.toThrow('Faltam os QR Codes 1 de 2')
  })

  it('rejects text that is not a ballot', async () => {
    await expect(assemble(['https://exemplo.com'])).rejects.toBeInstanceOf(BallotError)
  })

  it('builds the same section key as the server', async () => {
    const b = await assemble(BALLOTS_2022.find(x => x[0].includes('SECA:265'))!)
    expect(sectionKey(b.fields)).toBe('1:zz:30198:1:265')
  })
})

it('progress shows what is missing', () => {
  expect(progress([BALLOT_2026[0][1], 'junk'])).toEqual({ total: 2, read: [2], certificate: false })
})

it('compare returns only differences', () => {
  expect(compare({ '13': 112, '22': 98, BRAN: 3 }, { '13': 112, '22': 95, BRAN: 3 })).toEqual([{ key: '22', door: 98, tse: 95 }])
  expect(compare({ '13': 1 }, { '13': 1 })).toEqual([])
})
