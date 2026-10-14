// Place index for the cascading selector. One file per UF built by server/confere/places.py from the TSE cs.json.
// ponytail: served from app/public/places in dev (only MG generated so far); production reads the public CDN.
import { PATHS, type PlaceIndex } from '../../shared/model'
export { titleCase, UFS, type PlaceIndex } from '../../shared/model'

const BASE = import.meta.env.VITE_DATA_URL ?? `${import.meta.env.BASE_URL}`
const cache = new Map<string, Promise<PlaceIndex | null>>()

export function loadPlaces(uf: string): Promise<PlaceIndex | null> {
  if (!cache.has(uf)) cache.set(uf, fetch(`${BASE}${PATHS.places(uf)}`).then(r => (r.ok ? r.json() : null)).catch(() => null))
  return cache.get(uf)!
}

