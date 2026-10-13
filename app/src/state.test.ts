import { expect, it } from 'vitest'
import { order, sectionState } from './state'

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
