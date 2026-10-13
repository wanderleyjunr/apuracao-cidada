// App data: official TSE results per zone (static JSON built by server/confere/bweb.py) + door ballots sent from this device.
// Performance: one small file per zone (median ~9 KB, ~2 KB gzipped), fetched once and memoized; the service worker caches it.
import type { Votes } from '../../shared/ballot'

export interface Candidate { n: string; name: string; party: string; sq: string; status: string; votes: number; pct: string }
export interface CandidateIndex { declaredAt: string; names: Record<string, string>; offices: Record<string, Candidate[]> }
export interface Place { uf: string; municipality: string; municipalityCode: string; zone: string; section: string }
export interface DoorBallot { votes: Record<string, Votes>; time: string; submissions: number; urna: string } // votes per office
export interface TseSection { votes: Record<string, Votes>; apt: number; comp: number; received: string; urna: string; closed?: string; agg?: string }
export interface ZoneResults { sections: Record<string, TseSection> }
export interface SectionData { door?: { votes: Votes; time: string; submissions: number; urna: string }; tse?: { votes: Votes; time: string; apt: number; comp: number } }

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

const BASE = import.meta.env.VITE_DATA_URL ?? import.meta.env.BASE_URL
const memo = new Map<string, Promise<unknown>>()
function getJson<T>(path: string): Promise<T | null> {
  if (!memo.has(path)) memo.set(path, fetch(`${BASE}${path}`).then(r => (r.ok ? r.json() : null)).catch(() => null))
  return memo.get(path) as Promise<T | null>
}

export const loadZone = (turn: number, p: Place) => getJson<ZoneResults>(`results/${turn}/${p.uf.toLowerCase()}/${+p.municipalityCode}/${+p.zone}.json`)
export const loadCandidates = (turn: number) => getJson<CandidateIndex>(`results/${turn}/candidates.json`)
export const loadCity = (turn: number, p: Place) => getJson<{ offices: Record<string, Votes> }>(`results/${turn}/${p.uf.toLowerCase()}/${+p.municipalityCode}/city.json`)
export const loadDeputies = (uf: string) => getJson<Record<string, Record<string, [sq: string, name: string, party: string, result: string]>>>(`results/1/${uf.toLowerCase()}/deputies.json`)
/** Published by the server after each submission; never memoized (it changes during the night). */
const fresh = <T>(path: string): Promise<T | null> => fetch(`${BASE}${path}`, { cache: 'no-store' }).then(r => (r.ok ? r.json() : null)).catch(() => null)
const sectionPath = (turn: number, p: Place) => `sections/${turn}/${p.uf.toLowerCase()}/${+p.municipalityCode}/${+p.zone}`
export interface SectionDoc { status: string; differences: { key: string; door: number; tse: number }[]; door?: { votes: Record<string, Votes>; urna: string; firstSeen: string; submissions: number } }
export const loadSectionDoc = (turn: number, p: Place) => fresh<SectionDoc>(`${sectionPath(turn, p)}/${+p.section}.json`)
export const loadZoneStatus = (turn: number, p: Place) => fresh<Record<string, string>>(`${sectionPath(turn, p)}.json`)
export const loadCandidatePage = (sq: string) => getJson<CandidatePage>(`candidates/${sq}.json`)

export interface CandidatePage {
  sq: string; name: string; fullName?: string; number?: string; office?: string; officeCode?: string; uf?: string; scope?: string
  party?: string; partyName?: string; federation?: string; coalition?: string; coalitionParties?: string; birthUf?: string
  gender?: string; education?: string; race?: string; occupation?: string; candidacyStatus?: string; result?: string; age?: number | null
  assets?: { total: number; items: { type: string; value: number }[] }
}
export const photoUrl = (sq?: string) => (sq ? `${BASE}photos/${sq}.webp` : '')

export const sectionKey = (turn: number, p: Place) => `${turn}:${p.uf.toLowerCase()}:${+p.municipalityCode}:${+p.zone}:${+p.section}`

const read = <T>(k: string, fallback: T): T => { try { return JSON.parse(localStorage.getItem(k) ?? '') as T } catch { return fallback } }

export function doorBallot(turn: number, p: Place): DoorBallot | undefined {
  return read<Record<string, DoorBallot>>('sent', {})[sectionKey(turn, p)]
}

export function sectionData(turn: number, p: Place, office: string, zone: ZoneResults | null, doc?: SectionDoc | null): SectionData {
  const tse = zone?.sections[String(+p.section)]
  const local = doorBallot(turn, p)
  // server document wins (counts every witness); local copy covers offline / not yet sent
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

export function recordDoorBallot(turn: number, p: Place, door: DoorBallot): void {
  localStorage.setItem('sent', JSON.stringify({ ...read('sent', {}), [sectionKey(turn, p)]: door }))
}

export const savedPlace = (): Place => ({ ...DEFAULT_PLACE, ...read<Partial<Place>>('place', {}) })
export const savePlace = (p: Place) => localStorage.setItem('place', JSON.stringify(p))

export interface Coverage { totalSections: number; checked: number; byStatus: Record<string, number>; byUF: Record<string, number>; updatedAt: string }
export interface Divergence { key: string; uf: string; municipality: string; zone: number; section: number; status: string; differences: { key: string; door: number; tse: number }[]; since: string; document?: string }
export const loadCoverage = (turn: number) => fresh<Coverage>(`aggregates/${turn}/coverage.json`)
export const loadDivergences = (turn: number) => fresh<{ items: Divergence[]; updatedAt: string }>(`aggregates/${turn}/divergences.json`)
