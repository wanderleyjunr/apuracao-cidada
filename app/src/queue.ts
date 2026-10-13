// Offline send queue: the ballot stays on the device until it can be sent.
// ponytail: localStorage is enough for a few ballots per person; IndexedDB if the queue starts holding photos.
const KEY = 'send-queue'
const API = `${import.meta.env.VITE_API_URL ?? ''}/api/ballots` // edge/ worker (story 6)

export interface QueueItem { id: string; texts: string[]; createdAt: string }

export const queue = (): QueueItem[] => { try { return JSON.parse(localStorage.getItem(KEY) ?? '[]') } catch { return [] } }
const save = (items: QueueItem[]) => localStorage.setItem(KEY, JSON.stringify(items))

export function enqueue(texts: string[]): void {
  save([...queue(), { id: crypto.randomUUID(), texts, createdAt: new Date().toISOString() }])
}

/** Sends pending items; returns how many are still pending. */
export async function flush(): Promise<number> {
  if (!navigator.onLine) return queue().length
  const pending: QueueItem[] = []
  for (const item of queue()) {
    try {
      const r = await fetch(API, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ texts: item.texts }) })
      if (!r.ok && r.status !== 409) pending.push(item) // 409 = already received: done
    } catch { pending.push(item) }
  }
  save(pending)
  return pending.length
}
