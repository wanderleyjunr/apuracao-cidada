// Section state during election day (EXPERIENCE.md · State Patterns). Verdict only after the TSE publishes.
import { compare, type Difference } from '../../shared/ballot'
import type { SectionData } from './data'

export type SectionState =
  | { kind: 'before' } // before election day
  | { kind: 'voting' } // 8h–17h
  | { kind: 'no-ballot' } // after 17h, nobody submitted
  | { kind: 'waiting' } // door ballot sent, TSE not published
  | { kind: 'tse-only' } // TSE published, door ballot missing
  | { kind: 'identical' }
  | { kind: 'divergent'; differences: Difference[] }

export const ELECTION_DAY: Record<number, string> = { 1: '2026-10-04', 2: '2026-10-25' }

export function sectionState(turn: number, d: SectionData, now: Date): SectionState {
  const opens = new Date(`${ELECTION_DAY[turn]}T08:00:00-03:00`)
  const closes = new Date(`${ELECTION_DAY[turn]}T17:00:00-03:00`)
  if (now < opens) return { kind: 'before' }
  if (now < closes) return { kind: 'voting' }
  if (!d.door && !d.tse) return { kind: 'no-ballot' }
  if (!d.tse) return { kind: 'waiting' }
  if (!d.door) return { kind: 'tse-only' }
  const differences = compare(d.door.votes, d.tse.votes)
  return differences.length ? { kind: 'divergent', differences } : { kind: 'identical' }
}

/** Order: most votes in the section first; without votes, by candidate number. */
export function order(numbers: string[], votes?: Record<string, number>): string[] {
  return [...numbers].sort((a, b) => (votes ? (votes[b] ?? 0) - (votes[a] ?? 0) : 0) || +a - +b)
}
