// App data: official TSE results per zone (static JSON built by server/confere/bweb.py) + door ballots sent from this device.
// Performance: one small file per zone (median ~9 KB, ~2 KB gzipped), fetched once and memoized; the service worker caches it.
import type { Votes } from '../../shared/ballot'
import { DEFAULT_PLACE, PATHS, placeKey, sectionData as merge, type CandidateIndex, type CandidatePage, type Coverage, type Divergence, type DoorBallot, type Place, type SectionData, type SectionDoc, type ZoneResults } from '../../shared/model'
export { CITY_ONLY, DEFAULT_PLACE, OFFICE_LABEL, officeKey, officesFor, zoneTotals } from '../../shared/model'
export type { Candidate, CandidateIndex, CandidatePage, Coverage, Divergence, DoorBallot, Place, SectionData, SectionDoc, TseSection, ZoneResults } from '../../shared/model'

const BASE = import.meta.env.VITE_DATA_URL ?? import.meta.env.BASE_URL
const memo = new Map<string, Promise<unknown>>()
function getJson<T>(path: string): Promise<T | null> {
  if (!memo.has(path)) memo.set(path, fetch(`${BASE}${path}`).then(r => (r.ok ? r.json() : null)).catch(() => null))
  return memo.get(path) as Promise<T | null>
}

export const loadZone = (turn: number, p: Place) => getJson<ZoneResults>(PATHS.zone(turn, p))
export const loadCandidates = (turn: number) => getJson<CandidateIndex>(PATHS.candidates(turn))
export const loadCity = (turn: number, p: Place) => getJson<{ offices: Record<string, Votes> }>(PATHS.city(turn, p))
export const loadDeputies = (uf: string) => getJson<Record<string, Record<string, [sq: string, name: string, party: string, result: string]>>>(PATHS.deputies(uf))
/** Published by the server after each submission; never memoized (it changes during the night). */
const fresh = <T>(path: string): Promise<T | null> => fetch(`${BASE}${path}`, { cache: 'no-store' }).then(r => (r.ok ? r.json() : null)).catch(() => null)
export const loadSectionDoc = (turn: number, p: Place) => fresh<SectionDoc>(PATHS.sectionDoc(turn, p))
export const loadZoneStatus = (turn: number, p: Place) => fresh<Record<string, string>>(PATHS.zoneStatus(turn, p))
export const loadCandidatePage = (sq: string) => getJson<CandidatePage>(PATHS.candidatePage(sq))

export const photoUrl = (sq?: string) => (sq ? `${BASE}${PATHS.photo(sq)}` : '')

const read = <T>(k: string, fallback: T): T => { try { return JSON.parse(localStorage.getItem(k) ?? '') as T } catch { return fallback } }

export function doorBallot(turn: number, p: Place): DoorBallot | undefined {
  return read<Record<string, DoorBallot>>('sent', {})[placeKey(turn, p)]
}

export const sectionData = (turn: number, p: Place, office: string, zone: ZoneResults | null, doc?: SectionDoc | null): SectionData =>
  merge(p, office, zone, doc, doorBallot(turn, p))

export function recordDoorBallot(turn: number, p: Place, door: DoorBallot): void {
  localStorage.setItem('sent', JSON.stringify({ ...read('sent', {}), [placeKey(turn, p)]: door }))
}

export const savedPlace = (): Place => ({ ...DEFAULT_PLACE, ...read<Partial<Place>>('place', {}) })
export const savePlace = (p: Place) => localStorage.setItem('place', JSON.stringify(p))

export const loadCoverage = (turn: number) => fresh<Coverage>(PATHS.coverage(turn))
export const loadDivergences = (turn: number) => fresh<{ items: Divergence[]; updatedAt: string }>(PATHS.divergences(turn))
