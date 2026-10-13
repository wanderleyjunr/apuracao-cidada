// Place index for the cascading selector. One file per UF built by server/confere/places.py from the TSE cs.json.
// ponytail: served from app/public/places in dev (only MG generated so far); production reads the public CDN.
export const UFS: [code: string, name: string][] = [
  ['ac', 'Acre'], ['al', 'Alagoas'], ['ap', 'Amapá'], ['am', 'Amazonas'], ['ba', 'Bahia'], ['ce', 'Ceará'], ['df', 'Distrito Federal'],
  ['es', 'Espírito Santo'], ['go', 'Goiás'], ['ma', 'Maranhão'], ['mt', 'Mato Grosso'], ['ms', 'Mato Grosso do Sul'], ['mg', 'Minas Gerais'],
  ['pa', 'Pará'], ['pb', 'Paraíba'], ['pr', 'Paraná'], ['pe', 'Pernambuco'], ['pi', 'Piauí'], ['rj', 'Rio de Janeiro'],
  ['rn', 'Rio Grande do Norte'], ['rs', 'Rio Grande do Sul'], ['ro', 'Rondônia'], ['rr', 'Roraima'], ['sc', 'Santa Catarina'],
  ['sp', 'São Paulo'], ['se', 'Sergipe'], ['to', 'Tocantins'], ['zz', 'Exterior'],
]

export interface Municipality { code: number; name: string; zones: Record<string, number[]> }
export interface PlaceIndex { uf: string; municipalities: Municipality[] }

const BASE = import.meta.env.VITE_DATA_URL ?? `${import.meta.env.BASE_URL}`
const cache = new Map<string, Promise<PlaceIndex | null>>()

export function loadPlaces(uf: string): Promise<PlaceIndex | null> {
  if (!cache.has(uf)) cache.set(uf, fetch(`${BASE}places/${uf}.json`).then(r => (r.ok ? r.json() : null)).catch(() => null))
  return cache.get(uf)!
}

const LOWER = new Set(['de', 'da', 'do', 'das', 'dos', 'e', "d'"])
/** "SENADOR CORTES" → "Senador Cortes"; "SAO JOAO DEL REI" keeps connectors lowercase. */
export function titleCase(name: string): string {
  return name.toLowerCase().split(' ').map((w, i) => (i > 0 && LOWER.has(w) ? w : w.charAt(0).toUpperCase() + w.slice(1))).join(' ')
}
