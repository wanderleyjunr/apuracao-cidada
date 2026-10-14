// Funciona offline: páginas pela rede com fallback do cache; arquivos estáticos do cache primeiro.
const CACHE = 'apuracao-cidada-v2' // bump when cached static files change (v2: logo + icons)
self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', e => e.waitUntil(caches.keys()
  .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
  .then(() => self.clients.claim())))
self.addEventListener('fetch', e => {
  const req = e.request
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin || req.url.includes('/api/')) return
  const guardar = res => { const c = res.clone(); caches.open(CACHE).then(cache => cache.put(req, c)); return res }
  e.respondWith(req.mode === 'navigate'
    ? fetch(req).then(guardar).catch(() => caches.match(req).then(r => r || caches.match('./')))
    : caches.match(req).then(r => r || fetch(req).then(guardar)))
})
