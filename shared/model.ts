// SPDX-License-Identifier: MIT (shared/LICENSE). The rest of this repository is AGPL-3.0.
// Platform-free model shared by the PWA (app/) and the mobile app (mobile/): public JSON shapes, office rules,
// section state during election day and place names. No fetch, no storage, no env here (AD-2 / AD-4).
import { compare, type Difference, type Votes } from './ballot'

// ---------- public JSON shapes (published by server/) ----------
export interface Candidate { n: string; name: string; party: string; sq: string; status: string; votes: number; pct: string }
export interface CandidateIndex { declaredAt: string; names: Record<string, string>; offices: Record<string, Candidate[]> }
export interface Place { uf: string; municipality: string; municipalityCode: string; zone: string; section: string }
export interface DoorBallot { votes: Record<string, Votes>; time: string; submissions: number; urna: string } // votes per office
export interface TseSection { votes: Record<string, Votes>; apt: number; comp: number; received: string; urna: string; closed?: string; agg?: string }
export interface ZoneResults { sections: Record<string, TseSection> }
export interface SectionData { door?: { votes: Votes; time: string; submissions: number; urna: string }; tse?: { votes: Votes; time: string; apt: number; comp: number } }
export interface SectionDoc { status: string; differences: Difference[]; door?: { votes: Record<string, Votes>; urna: string; firstSeen: string; submissions: number } }
export interface CandidatePage {
  sq: string; name: string; fullName?: string; number?: string; office?: string; officeCode?: string; uf?: string; scope?: string
  party?: string; partyName?: string; federation?: string; coalition?: string; coalitionParties?: string; birthUf?: string
  gender?: string; education?: string; race?: string; occupation?: string; candidacyStatus?: string; result?: string; age?: number | null
  assets?: { total: number; items: { type: string; value: number }[] }
}
export interface Coverage { totalSections: number; checked: number; byStatus: Record<string, number>; byUF: Record<string, number>; updatedAt: string }
export interface Divergence { key: string; uf: string; municipality: string; zone: number; section: number; status: string; differences: Difference[]; since: string; document?: string }
/** TSE national President totals, copied from resultados.tse.jus.br by server/confere/national.py (no projection). */
export interface NationalResults {
  turn: number; election: string; updatedAt: string; pct: number; sections: { total: number; counted: number }
  votes: { valid: number; blank: number; null: number }
  candidates: { n: string; sq: string; name: string; party: string; votes: number; pct: number; status: string }[]
  source: string
}
/** results/1/<uf>/deputies.json: office ("6" federal, "7" state) → number → [sqcand, name, party, TSE result]. */
export type Deputies = Record<string, Record<string, [sq: string, name: string, party: string, result: string]>>
export interface ElectedPerson { n: string; sq: string; name: string; party: string; pct?: number }
export interface Elected { governor?: ElectedPerson; senators: ElectedPerson[]; federal: ElectedPerson[]; state: ElectedPerson[] }

/** Who the TSE declared elected in the 1st round for one UF (status copied, never inferred). */
export function electedFirstRound(uf: string, gov1: NationalResults | null, cands1: CandidateIndex | null, deps: Deputies | null): Elected {
  const g = gov1?.candidates.find(c => c.status === 'Eleito')
  const deputies = (office: string) => Object.entries(deps?.[office] ?? {})
    .filter(([, [, , , r]]) => r.startsWith('ELEITO'))
    .map(([n, [sq, name, party]]) => ({ n, sq, name, party }))
    .sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'))
  return {
    governor: g && { n: g.n, sq: g.sq, name: g.name, party: g.party, pct: g.pct },
    senators: (cands1?.offices[`5:${uf.toLowerCase()}`] ?? []).filter(c => c.status === 'Eleito').map(({ n, sq, name, party }) => ({ n, sq, name, party })),
    federal: deputies('6'),
    state: deputies('7'),
  }
}

export interface Municipality { code: number; name: string; zones: Record<string, number[]> }
export interface PlaceIndex { uf: string; municipalities: Municipality[] }

// ---------- public file paths (same on the CDN for every client, AD-3) ----------
const zonePath = (turn: number, p: Place) => `${p.uf.toLowerCase()}/${+p.municipalityCode}/${+p.zone}`
export const PATHS = {
  national: (turn: number) => `results/${turn}/national.json`,
  governor: (turn: number, uf: string) => `results/${turn}/${uf.toLowerCase()}/governor.json`,
  zone: (turn: number, p: Place) => `results/${turn}/${zonePath(turn, p)}.json`,
  candidates: (turn: number) => `results/${turn}/candidates.json`,
  city: (turn: number, p: Place) => `results/${turn}/${p.uf.toLowerCase()}/${+p.municipalityCode}/city.json`,
  deputies: (uf: string) => `results/1/${uf.toLowerCase()}/deputies.json`,
  sectionDoc: (turn: number, p: Place) => `sections/${turn}/${zonePath(turn, p)}/${+p.section}.json`,
  zoneStatus: (turn: number, p: Place) => `sections/${turn}/${zonePath(turn, p)}.json`,
  candidatePage: (sq: string) => `candidates/${sq}.json`,
  photo: (sq: string) => `photos/${sq}.webp`,
  places: (uf: string) => `places/${uf.toLowerCase()}.json`,
  coverage: (turn: number) => `aggregates/${turn}/coverage.json`,
  divergences: (turn: number) => `aggregates/${turn}/divergences.json`,
}

// ---------- offices ----------
export const OFFICE_LABEL: Record<string, string> = { '1': 'Presidente', '3': 'Governador', '5': 'Senador', '6': 'Dep. Federal', '7': 'Dep. Estadual' }
export const CITY_ONLY = new Set(['6', '7']) // proportional offices: city totals only (performance)

/** Index key: President is national, the others are per UF. */
export const officeKey = (office: string, uf: string) => (office === '1' ? '1' : `${office}:${uf.toLowerCase()}`)

/** Offices available for a turn/UF: 1st round = all; 2nd round = the ones the TSE declared a runoff for. */
export function officesFor(turn: number, uf: string, idx: CandidateIndex | null): string[] {
  if (turn === 1) return ['1', '3', '5', '6', '7']
  return ['1', '3'].filter(o => idx?.offices[officeKey(o, uf)]?.length)
}
export const DEFAULT_PLACE: Place = { uf: 'MG', municipality: 'Senador Cortes', municipalityCode: '53112', zone: '170', section: '' } // '' = whole zone
export const placeKey = (turn: number, p: Place) => `${turn}:${p.uf.toLowerCase()}:${+p.municipalityCode}:${+p.zone}:${+p.section}`

/** One office of one section: the server document wins (counts every witness); the local copy covers offline / not yet sent. */
export function sectionData(p: Place, office: string, zone: ZoneResults | null, doc?: SectionDoc | null, local?: DoorBallot): SectionData {
  const tse = zone?.sections[String(+p.section)]
  const door = doc?.door ? { votes: doc.door.votes, urna: doc.door.urna, submissions: doc.door.submissions, time: new Date(doc.door.firstSeen).toTimeString().slice(0, 5) } : local
  return {
    tse: tse?.votes[office] ? { votes: tse.votes[office], time: tse.received.slice(11, 16), apt: tse.apt, comp: tse.comp } : undefined,
    door: door?.votes[office] ? { ...door, votes: door.votes[office] } : undefined,
  }
}

/** Official zone totals for one office = sum of the TSE section results (not a projection: published numbers). */
export function zoneTotals(zone: ZoneResults | null, office: string): Votes {
  const total: Votes = {}
  for (const s of Object.values(zone?.sections ?? {})) for (const [k, v] of Object.entries(s.votes[office] ?? {})) total[k] = (total[k] ?? 0) + v
  return total
}

// ---------- section state during election day (EXPERIENCE.md · State Patterns). Verdict only after the TSE publishes ----------
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

// ---------- places ----------
export const UFS: [code: string, name: string][] = [
  ['ac', 'Acre'], ['al', 'Alagoas'], ['ap', 'Amapá'], ['am', 'Amazonas'], ['ba', 'Bahia'], ['ce', 'Ceará'], ['df', 'Distrito Federal'],
  ['es', 'Espírito Santo'], ['go', 'Goiás'], ['ma', 'Maranhão'], ['mt', 'Mato Grosso'], ['ms', 'Mato Grosso do Sul'], ['mg', 'Minas Gerais'],
  ['pa', 'Pará'], ['pb', 'Paraíba'], ['pr', 'Paraná'], ['pe', 'Pernambuco'], ['pi', 'Piauí'], ['rj', 'Rio de Janeiro'],
  ['rn', 'Rio Grande do Norte'], ['rs', 'Rio Grande do Sul'], ['ro', 'Rondônia'], ['rr', 'Roraima'], ['sc', 'Santa Catarina'],
  ['sp', 'São Paulo'], ['se', 'Sergipe'], ['to', 'Tocantins'], ['zz', 'Exterior'],
]

const LOWER = new Set(['de', 'da', 'do', 'das', 'dos', 'e', "d'"])
/** "SENADOR CORTES" → "Senador Cortes"; "SAO JOAO DEL REI" keeps connectors lowercase. */
export function titleCase(name: string): string {
  return name.toLowerCase().split(' ').map((w, i) => (i > 0 && LOWER.has(w) ? w : w.charAt(0).toUpperCase() + w.slice(1))).join(' ')
}
