// SPDX-License-Identifier: MIT (shared/LICENSE). The rest of this repository is AGPL-3.0.
import { expect, it } from 'vitest'
import { electedFirstRound, order, sectionState } from './model'

const at = (s: string) => new Date(s)
const tse = { time: '18:47', votes: { '13': 112, '22': 95 } }
const door = { time: '17:06', submissions: 1, urna: 'x', votes: { '13': 112, '22': 98 } }

it('states along election day', () => {
  expect(sectionState(2, {}, at('2026-10-20T12:00:00-03:00')).kind).toBe('before')
  expect(sectionState(2, {}, at('2026-10-25T10:00:00-03:00')).kind).toBe('voting')
  expect(sectionState(2, {}, at('2026-10-25T17:30:00-03:00')).kind).toBe('no-ballot')
  expect(sectionState(2, { door }, at('2026-10-25T17:30:00-03:00')).kind).toBe('waiting')
  expect(sectionState(2, { tse }, at('2026-10-25T19:00:00-03:00')).kind).toBe('tse-only')
  expect(sectionState(2, { door: { ...door, votes: tse.votes }, tse }, at('2026-10-25T19:00:00-03:00')).kind).toBe('identical')
  expect(sectionState(2, { door, tse }, at('2026-10-25T19:00:00-03:00'))).toEqual({ kind: 'divergent', differences: [{ key: '22', door: 98, tse: 95 }] })
})

it('orders by votes, otherwise by number', () => {
  expect(order(['22', '13'])).toEqual(['13', '22'])
  expect(order(['13', '22'], { '13': 5, '22': 9 })).toEqual(['22', '13'])
})

it('elected in the 1st round: only what the TSE declared', () => {
  const gov = { candidates: [{ n: '10', sq: 'g1', name: 'A', party: 'X', votes: 9, pct: 55, status: 'Eleito' }, { n: '13', sq: 'g2', name: 'B', party: 'Y', votes: 7, pct: 45, status: 'Não eleito' }] } as never
  const cands = { declaredAt: '', names: {}, offices: { '5:sp': [{ n: '111', sq: 's1', name: 'S', party: 'Z', status: 'Eleito', votes: 1, pct: '' }, { n: '222', sq: 's2', name: 'T', party: 'Z', status: 'Não eleito', votes: 1, pct: '' }] } }
  const deps = { '6': { '1001': ['d1', 'ZÉ', 'P', 'ELEITO POR QP'], '1002': ['d2', 'ANA', 'P', 'ELEITO POR MÉDIA'], '1003': ['d3', 'BIA', 'P', 'SUPLENTE'] }, '7': {} } as never
  const e = electedFirstRound('SP', gov, cands, deps)
  expect(e.governor?.sq).toBe('g1')
  expect(e.senators.map(x => x.sq)).toEqual(['s1'])
  expect(e.federal.map(x => x.name)).toEqual(['ANA', 'ZÉ'])
  expect(e.state).toEqual([])
})
