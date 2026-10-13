import './style.css'
import { assemble, BallotError, isOfficial2026, officeVotes, progress, type Ballot, type Votes } from '../../shared/ballot'
import {
  CITY_ONLY, OFFICE_LABEL, loadCoverage, loadDivergences, loadCandidatePage, loadCandidates, loadCity, loadDeputies, loadZone, officeKey, officesFor,
  loadSectionDoc, loadZoneStatus, photoUrl, recordDoorBallot, savedPlace, savePlace, sectionData, zoneTotals, type Candidate, type CandidateIndex, type Place,
} from './data'
import { loadPlaces, titleCase, UFS, type PlaceIndex } from './places'
import { enqueue, flush, queue } from './queue'
import { order, sectionState, type SectionState } from './state'

const app = document.querySelector<HTMLDivElement>('#app')!
const esc = (s: unknown) => String(s ?? '').replace(/[&<>"']/g, c => `&#${c.charCodeAt(0)};`) // QR content is untrusted input
const fmt = (n: number) => n.toLocaleString('pt-BR')
const pct = (n: number) => (n > 0 && n < 0.001 ? '<0,1%' : `${(n * 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`)

// ?agora=2026-10-25T19:00 simulates the clock (demos and manual tests)
const now = () => new Date(new URLSearchParams(location.search).get('agora') ?? Date.now())
const turn = () => Number(localStorage.getItem('turn') ?? 2)
/** Current office, clamped to what exists for this turn/UF (2nd round: President + Governor where there is a runoff). */
const office = (idx: CandidateIndex | null, uf: string) => {
  const allowed = officesFor(turn(), uf, idx)
  const o = localStorage.getItem('office') ?? '1'
  return allowed.includes(o) ? o : allowed[0] ?? '1'
}

const ICON = {
  section: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>',
  coverage: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>',
  divergences: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 3 2 20h20L12 3zM12 10v4M12 17h.01"/></svg>',
  about: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/></svg>',
  scan: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3M8 12h8"/></svg>',
}

function nav(route: string): string {
  const item = (r: string, label: string, icon: string) => `<a href="#/${r}" ${route === r ? 'aria-current="page"' : ''}>${icon}<span>${label}</span></a>`
  return `<nav class="nav" aria-label="Navegação">${item('section', 'Seção', ICON.section)}${item('coverage', 'Cobertura', ICON.coverage)}<span></span>
    ${item('divergences', 'Divergências', ICON.divergences)}${item('about', 'Sobre', ICON.about)}</nav>
    <a class="fab" href="#/scan" aria-label="Escanear boletim">${ICON.scan}</a>`
}

const flag = (uf: string) => uf.toLowerCase() === 'zz'
  ? '<span class="flag flag-globe" aria-hidden="true">🌎</span>'
  : `<img class="flag" src="${import.meta.env.BASE_URL}flags/${esc(uf.toLowerCase())}.png" alt="" width="30" height="21">`

function header(p: Place): string {
  const t = turn()
  return `<header class="top-bar"><div class="row"><div class="brand">Apuração Cidadã<small>#EuFiscalizo · código aberto</small></div>
    <div class="turn-toggle" role="group" aria-label="Turno">${[1, 2].map(n => `<button data-turn="${n}" aria-pressed="${t === n}">${n}º</button>`).join('')}</div></div>
    <button class="place-button" id="change-place">${flag(p.uf)}<span class="place-text">${esc(p.municipality)}, ${esc(p.uf)}<small>Zona ${esc(p.zone)} · ${p.section ? `Seção ${esc(p.section)}` : 'todas as seções'}</small></span><span aria-hidden="true">▾</span></button></header>`
}

function officeTabs(current: string, idx: CandidateIndex | null, uf: string, sectionLevel = false): string {
  const list = officesFor(turn(), uf, idx).filter(o => !(sectionLevel && CITY_ONLY.has(o)))
  if (list.length < 2) return ''
  return `<div class="chips" role="tablist" aria-label="Cargo">${list.map(c => `<button role="tab" data-office="${c}" aria-pressed="${current === c}">${OFFICE_LABEL[c]}</button>`).join('')}</div>`
}

const candLink = (c: Candidate | undefined, inner: string) => (c?.sq ? `<a class="cand-link" href="#/candidate/${esc(c.sq)}">${inner}</a>` : inner)

const queueNotice = () => { const n = queue().length; return n ? `<div class="offline">📶 ${n} boletim(ns) salvo(s) no celular, aguardando envio. Enviamos sozinhos assim que der.</div>` : '' }

const avatar = (c: Candidate | undefined, n: string) => c?.sq
  ? `<img class="photo" src="${photoUrl(c.sq)}" alt="" width="56" height="56" loading="lazy" decoding="async">`
  : `<div class="photo" aria-hidden="true">${esc(n)}</div>`

/** Badge only when the TSE declared it (Alino's decision, 2026-10-11). */
function statusBadge(c?: Candidate): string {
  if (!c || turn() !== 1) return ''
  if (c.status === 'Eleito') return '<span class="badge elected" title="Declarado pelo TSE">Eleito · TSE</span>'
  if (c.status === '2º turno') return '<span class="badge runoff" title="Declarado pelo TSE">2º turno · TSE</span>'
  return ''
}

// ---------- Section ----------
function sticker(s: SectionState, doorTime?: string, tseTime?: string): string {
  const a = (cls: string, tag: string, title: string, sub: string) => `<div class="sticker ${cls}" role="status"><span class="tag">${tag}</span><b>${title}</b><small>${sub}</small></div>`
  switch (s.kind) {
    case 'before': return a('sticker-voting', 'EM BREVE', `Votação em ${turn() === 2 ? '25/10' : '04/10'}`, 'Às 17h, depois de votar, fotografe o boletim na porta da seção.')
    case 'voting': return a('sticker-voting', '● AO VIVO', 'Votação em andamento', 'A urna fecha às 17h. Depois, fotografe o boletim na porta da seção.')
    case 'no-ballot': return a('sticker-neutral', 'SEM BOLETIM', 'Ninguém enviou esta seção ainda', 'O boletim está pregado na porta. Seja a primeira pessoa a enviar.')
    case 'waiting': return a('sticker-waiting', '⏳ AGUARDANDO TSE', 'Boletim da porta registrado', `Enviado às ${esc(doorTime)} · boletim íntegro`)
    case 'tse-only': return a('sticker-neutral', 'FALTA A PORTA', 'O TSE já publicou esta seção', `Recebido pelo TSE às ${esc(tseTime)}. Falta o boletim da porta para conferir: tem a foto? Escaneie.`)
    case 'identical': return a('sticker-identical', '✓ IDÊNTICO', 'Idêntico ao TSE', `Boletim da porta (${esc(doorTime)}) = publicado pelo TSE (${esc(tseTime)})`)
    case 'divergent': {
      const d = s.differences[0]
      const label = d.key === 'BRAN' ? 'brancos' : d.key === 'NULO' ? 'nulos' : d.key
      return a('sticker-divergent', '⚠ DIVERGÊNCIA', 'Diferente do TSE', `${esc(label)}: porta ${d.door} · TSE ${d.tse}. Precisa de explicação; não é acusação.`)
    }
  }
}

async function viewSection(): Promise<void> {
  const p = savedPlace()
  if (!p.section) return viewZone(p)
  const t = turn()
  const [zone, cands, runoff, doc] = await Promise.all([loadZone(t, p), loadCandidates(1), loadCandidates(2), loadSectionDoc(t, p)])
  const lineup = t === 2 ? runoff : cands
  let o = office(lineup, p.uf)
  if (CITY_ONLY.has(o)) o = '1' // deputies only at city level
  const byNumber = Object.fromEntries((cands?.offices[officeKey(o, p.uf)] ?? []).map(c => [c.n, c]))
  const d = sectionData(t, p, o, zone, doc)
  const local = sectionState(t, d, now())
  // the server verdict covers every office: a divergence in another office must not read as "identical" here
  const s: SectionState = doc && (doc.status === 'divergent' || doc.status === 'conflict') && local.kind !== 'divergent'
    ? { kind: 'divergent', differences: doc.differences.map(x => ({ ...x, key: `${OFFICE_LABEL[x.key.split(':')[0]] ?? ''} ${x.key.split(':')[1]}` })) }
    : local
  const ref = d.door?.votes ?? d.tse?.votes
  const numbers = t === 2 ? (runoff?.offices[officeKey(o, p.uf)] ?? []).map(c => c.n) : Object.keys(ref ?? {}).filter(k => /^\d+$/.test(k))
  const diverging = new Set(s.kind === 'divergent' ? s.differences.map(x => x.key) : [])
  const cards = order(numbers, ref).map(n => {
    const c = byNumber[n]
    const dv = d.door?.votes[n], tv = d.tse?.votes[n]
    const status = !(d.door && d.tse) ? '' : diverging.has(n) ? `<div class="status bad">✕ diverge (${(tv ?? 0) - (dv ?? 0)})</div>` : '<div class="status ok">✓ confere</div>'
    return `<div class="candidate ${diverging.has(n) ? 'divergent' : ''}">${candLink(c, `${avatar(c, n)}
      <div class="party">${esc(c?.party ?? '')} – ${esc(n)}</div><div class="name">${esc(c?.name ?? `Candidato ${n}`)}</div>`)}${statusBadge(c)}
      <div class="votes"><span>PORTA<b>${dv ?? '—'}</b></span><span>TSE<b>${tv ?? (d.door ? '…' : '—')}</b></span></div>${status}</div>`
  }).join('')
  const blanks = (d.door || d.tse) ? `<div class="card"><div class="list-row"><b>Brancos / Nulos</b><span>porta ${d.door ? `${d.door.votes.BRAN ?? 0} / ${d.door.votes.NULO ?? 0}` : '—'} · TSE ${d.tse ? `${d.tse.votes.BRAN ?? 0} / ${d.tse.votes.NULO ?? 0}` : '—'}</span></div>
    ${d.tse ? `<div class="list-row"><b>Comparecimento</b><span>${fmt(d.tse.comp)} de ${fmt(d.tse.apt)} aptos</span></div>` : ''}</div>` : ''
  const proofs = d.door ? `<div class="card"><h3>Provas</h3>📄 Boletim da porta · ${d.door.submissions} envio(s)<br>🔏 Urna ${esc(d.door.urna)} · cadeia de hash conferida${d.tse ? `<br>🏛 Arquivo do TSE recebido às ${esc(d.tse.time)}` : ''}
    <br>🧾 <a href="${import.meta.env.BASE_URL}log/${t}/checkpoints.json" target="_blank" rel="noopener">Registro público (cadeia de hashes)</a></div>` : ''
  const actions = s.kind === 'before' || s.kind === 'voting'
    ? `<a class="btn" href="${reminderIcs()}" download="apuracao-cidada-17h.ics">Me lembrar às 17h</a>`
    : s.kind === 'identical' || s.kind === 'divergent' ? `<button class="btn amber" id="share">Compartilhar a prova ↗</button>`
    : `<a class="btn amber" href="#/scan">Escanear o boletim</a>`
  const explain = s.kind === 'divergent' ? `<div class="card muted">Divergência é um fato a ser explicado (urna de contingência, recuperação de dados, erro de leitura), não prova de fraude.</div>` : ''
  const back = `<button class="btn outline" id="whole-zone">← Ver todas as seções da zona ${esc(p.zone)}</button>`
  app.innerHTML = header(p) + sticker(s, d.door?.time, d.tse?.time) + queueNotice() + officeTabs(o, lineup, p.uf, true) + `<div class="candidates">${cards}</div>` + blanks + explain + actions + proofs + back + nav('section')
  bindCommon()
  document.querySelector('#whole-zone')!.addEventListener('click', () => { savePlace({ ...p, section: '' }); render() })
  document.querySelector('#share')?.addEventListener('click', () => share(p, s))
}

// ---------- Zone (default) ----------
const STATUS_LABEL: Record<SectionState['kind'] | 'aggregated' | 'conflict', [string, string]> = {
  before: ['—', 'muted'], voting: ['—', 'muted'], 'no-ballot': ['sem boletim', 'muted'], waiting: ['aguardando TSE', 'waiting'],
  'tse-only': ['falta a porta', 'muted'], identical: ['idêntico', 'ok'], divergent: ['diverge', 'bad'], aggregated: ['agregada', 'muted'],
  conflict: ['conflito', 'bad'], // two door ballots disagree: alert, no verdict
}

/** Official TSE totals of the zone (sum of published section results) + the conference status of every section. */
function officialTotals(totals: Votes, cands: CandidateIndex | null, o: string, uf: string, scopeLabel: string, limit = 0): string {
  const byNumber = Object.fromEntries((cands?.offices[officeKey(o, uf)] ?? []).map(c => [c.n, c]))
  const numbers = Object.keys(totals).filter(k => /^\d+$/.test(k))
  if (!numbers.length) return ''
  const valid = numbers.reduce((s, k) => s + totals[k], 0)
  const sorted = order(numbers, totals)
  const rows = (limit ? sorted.slice(0, limit) : sorted).map(n => {
    const c = byNumber[n]
    const fallback = CITY_ONLY.has(o) && n.length <= 2 ? `Voto na legenda ${n}` : `Candidato ${n}`
    return candLink(c, `<div class="result-row">${avatar(c, n)}<div class="result-name"><b>${esc(c?.name ?? fallback)}</b><small>${esc(c?.party ?? '')} · ${esc(n)}</small>${statusBadge(c)}</div>
      <div class="result-num"><b>${pct(totals[n] / valid)}</b><small>${fmt(totals[n])} votos</small></div></div>`)
  }).join('') + (limit && sorted.length > limit ? `<p class="muted" style="margin-top:6px">Mostrando os ${limit} mais votados de ${sorted.length}.</p>` : '')
  return `<div class="card"><h3>Resultado oficial do TSE · ${esc(scopeLabel)}</h3>${rows}
    <div class="muted" style="margin-top:6px">Brancos ${fmt(totals.BRAN ?? 0)} · Nulos ${fmt(totals.NULO ?? 0)} · "Eleito" e "2º turno" são declarações do TSE${cands ? ` (${esc(cands.declaredAt)})` : ''}.</div></div>`
}

/** 2nd round before results: the two candidates the TSE declared for the runoff, same treatment for both. */
function runoffLineup(idx: CandidateIndex | null, o: string, uf: string): string {
  const list = [...(idx?.offices[officeKey(o, uf)] ?? [])].sort((a, b) => +a.n - +b.n) // by number: no ranking before votes exist
  if (!list.length) return ''
  return `<div class="card"><h3>${OFFICE_LABEL[o]} · 2º turno</h3><div class="candidates" style="margin:8px 0 0">${list.map(c => `<div class="candidate">${candLink(c, `${avatar(c, c.n)}
    <div class="party">${esc(c.party)} – ${esc(c.n)}</div><div class="name">${esc(c.name)}</div>`)}</div>`).join('')}</div>
    <p class="muted" style="margin-top:8px">Candidatos declarados para o 2º turno pelo TSE. Toque para ver o perfil.</p></div>`
}

async function viewZone(p: Place): Promise<void> {
  const t = turn()
  const [index, zone, cands, runoff, published] = await Promise.all([loadPlaces(p.uf.toLowerCase()), loadZone(t, p), loadCandidates(1), loadCandidates(2), loadZoneStatus(t, p)])
  const lineup = t === 2 ? runoff : cands
  const o = office(lineup, p.uf)
  const sectionOffice = CITY_ONLY.has(o) ? '1' : o
  const sections = index?.municipalities.find(m => String(m.code) === p.municipalityCode)?.zones[String(+p.zone)] ?? []
  const states = sections.map(n => {
    const sp = { ...p, section: String(n) }
    const d = sectionData(t, sp, sectionOffice, zone)
    const hasOwnBu = !zone || zone.sections[String(n)] || d.door
    const server = published?.[String(n)] as keyof typeof STATUS_LABEL | undefined // server verdict (all offices) wins
    return { n, kind: server && server in STATUS_LABEL ? server : (hasOwnBu || t === 2 ? sectionState(t, d, now()).kind : 'aggregated') as keyof typeof STATUS_LABEL }
  })
  const count = (k: string) => states.filter(x => x.kind === k).length
  const checked = count('identical') + count('divergent') + count('waiting')
  const dayState = sectionState(t, {}, now()).kind // before / voting are the same for every section
  const open = dayState === 'before' || dayState === 'voting'
  const summary = open
    ? sticker({ kind: dayState } as SectionState)
    : `<div class="sticker sticker-neutral" role="status"><span class="tag">ZONA ${esc(p.zone)}</span><b>${checked} de ${sections.length - count('aggregated')} seções conferidas</b><small>${count('identical')} idênticas · ${count('divergent')} divergentes · ${count('waiting')} aguardando o TSE · ${count('tse-only')} sem boletim da porta</small></div>`
  const grid = states.map(({ n, kind }) => `<button class="section-chip ${STATUS_LABEL[kind][1]}" data-section="${n}" aria-label="Seção ${n}: ${STATUS_LABEL[kind][0]}">
      <b>${n}</b><small>${STATUS_LABEL[kind][0]}</small></button>`).join('')
  let results: string
  if (CITY_ONLY.has(o)) {
    const [city, deps] = await Promise.all([loadCity(t, p), loadDeputies(p.uf)])
    const asCands: CandidateIndex = { declaredAt: cands?.declaredAt ?? '', names: {}, offices: { [officeKey(o, p.uf)]: Object.entries(deps?.[o] ?? {}).map(([n, [sq, name, party, result]]) =>
      ({ n, sq, name, party, status: result === 'ELEITO' || result.startsWith('ELEITO') ? 'Eleito' : '', votes: 0, pct: '' })) } }
    results = officialTotals(city?.offices[o] ?? {}, asCands, o, p.uf, `${OFFICE_LABEL[o]} · total de ${p.municipality}`, 30)
  } else if (t === 2 && !zone) {
    results = runoffLineup(runoff, o, p.uf)
  } else {
    results = officialTotals(zoneTotals(zone, o), cands, o, p.uf, `zona ${p.zone} de ${p.municipality}`)
  }
  app.innerHTML = header(p) + summary + queueNotice() + officeTabs(o, lineup, p.uf) + results +
    `<div class="card"><h3>Seções de ${esc(p.municipality)} na zona ${esc(p.zone)}</h3>
      <p class="muted">${sections.length} seções. A numeração é da zona, que pode incluir outras cidades; por isso os números pulam.${count('aggregated') ? ` ${count('aggregated')} são agregadas: os votos saem no boletim de outra seção.` : ''}</p>
      ${grid ? `<div class="section-grid">${grid}</div>` : '<p class="muted">Lista indisponível para esta cidade.</p>'}</div>` + nav('section')
  bindCommon()
  document.querySelectorAll<HTMLButtonElement>('[data-section]').forEach(b => b.addEventListener('click', () => { savePlace({ ...p, section: b.dataset.section! }); render() }))
}

function reminderIcs(): string {
  const ics = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Apuracao Cidada//PT-BR', 'BEGIN:VEVENT', `UID:apuracao-cidada-${turn()}@confere`,
    `DTSTART:${turn() === 2 ? '20261025' : '20261004'}T200000Z`, 'DURATION:PT30M', 'SUMMARY:Fotografar o boletim na porta da seção',
    'BEGIN:VALARM', 'TRIGGER:PT0M', 'ACTION:DISPLAY', 'DESCRIPTION:Hora de fotografar o boletim', 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR'].join('\r\n')
  return `data:text/calendar;charset=utf-8,${encodeURIComponent(ics)}`
}

async function share(p: Place, s: SectionState): Promise<void> {
  const text = s.kind === 'identical'
    ? `Seção ${p.section} de ${p.municipality}/${p.uf}: idêntico ao TSE. Conferi com o boletim da porta.`
    : `Seção ${p.section} de ${p.municipality}/${p.uf}: divergência em análise, com provas abertas.`
  // ponytail: shares text + link; the 9:16 story card image comes later
  const url = `${location.origin}${location.pathname}#/section`
  if (navigator.share) await navigator.share({ text, url }).catch(() => {})
  else { await navigator.clipboard.writeText(`${text} ${url}`); alert('Link copiado.') }
}

function bindCommon(): void {
  document.querySelectorAll<HTMLButtonElement>('[data-turn]').forEach(b => b.addEventListener('click', () => { localStorage.setItem('turn', b.dataset.turn!); render() }))
  document.querySelectorAll<HTMLButtonElement>('[data-office]').forEach(b => b.addEventListener('click', () => { localStorage.setItem('office', b.dataset.office!); render() }))
  document.querySelector('#change-place')?.addEventListener('click', placeDialog)
}

/** Cascading native selects: UF → municipality → zone → section (optional: '' = whole zone). */
function placeDialog(): void {
  const p = savedPlace()
  const dlg = document.createElement('dialog')
  const opt = (value: string | number, label: string, selected = false) => `<option value="${esc(value)}"${selected ? ' selected' : ''}>${esc(label)}</option>`
  dlg.innerHTML = `<form method="dialog"><h3>Minha seção</h3><p class="muted">Ao escanear o boletim, a seção é preenchida sozinha.</p>
    <label>Estado<span class="select-flag"><span id="uf-flag"></span><select name="uf" required>${opt('', 'Escolha o estado')}${UFS.map(([c, n]) => opt(c, `${n} (${c.toUpperCase()})`, c === p.uf.toLowerCase())).join('')}</select></span></label>
    <label>Município<select name="municipality" required disabled></select></label>
    <label>Zona<select name="zone" required disabled></select></label>
    <label>Seção<select name="section" disabled></select></label>
    <p class="muted" id="place-hint" role="status"></p>
    <button class="btn" style="width:100%;margin:14px 0 0" disabled>Salvar</button></form>`
  document.body.append(dlg)
  const form = dlg.querySelector('form')!
  const sel = (n: string) => form.querySelector<HTMLSelectElement>(`select[name="${n}"]`)!
  const [uf, mun, zone, sec] = ['uf', 'municipality', 'zone', 'section'].map(sel)
  const save = form.querySelector<HTMLButtonElement>('button')!
  const hint = form.querySelector('#place-hint')!
  let index: PlaceIndex | null = null
  const fill = (s: HTMLSelectElement, placeholder: string, options: string) => { s.innerHTML = opt('', placeholder) + options; s.disabled = !options }
  const municipality = () => index?.municipalities.find(m => String(m.code) === mun.value)

  async function onUf(keep = false) {
    fill(mun, 'Escolha o município', ''); fill(zone, 'Escolha a zona', ''); fill(sec, 'Escolha a seção', ''); save.disabled = true
    form.querySelector('#uf-flag')!.innerHTML = uf.value ? flag(uf.value) : ''
    if (!uf.value) return
    hint.textContent = 'Carregando municípios…'
    index = await loadPlaces(uf.value)
    hint.textContent = index ? '' : 'Lista deste estado ainda indisponível. Escaneie o boletim para preencher sozinho.'
    fill(mun, 'Escolha o município', (index?.municipalities ?? []).map(m => opt(m.code, titleCase(m.name), keep && String(m.code) === p.municipalityCode)).join(''))
    if (keep && mun.value) onMun(true)
  }
  function onMun(keep = false) {
    fill(sec, 'Escolha a seção', ''); save.disabled = true
    const zones = municipality()?.zones ?? {}
    fill(zone, 'Escolha a zona', Object.keys(zones).map(z => opt(z, `Zona ${z} · ${zones[z].length} seções`, keep && z === String(+p.zone))).join(''))
    if (keep && zone.value) onZone(true)
  }
  function onZone(keep = false) {
    const list = municipality()?.zones[zone.value] ?? []
    sec.innerHTML = list.length ? opt('', `Todas as seções da zona (${list.length})`) + list.map(s => opt(s, `Seção ${s}`, keep && String(s) === String(+p.section))).join('') : ''
    sec.disabled = !list.length
    save.disabled = !zone.value
  }
  uf.addEventListener('change', () => onUf())
  mun.addEventListener('change', () => onMun())
  zone.addEventListener('change', () => onZone())
  form.addEventListener('submit', () => {
    const m = municipality()!
    savePlace({ uf: uf.value.toUpperCase(), municipality: titleCase(m.name), municipalityCode: String(m.code), zone: zone.value, section: sec.value })
    dlg.remove(); render()
  })
  dlg.addEventListener('close', () => dlg.remove())
  dlg.showModal()
  onUf(true)
}

// ---------- Scan ----------
let reads: string[] = []
let stopCamera: (() => void) | null = null

async function viewScan(): Promise<void> {
  reads = []
  app.innerHTML = `<div class="camera"><video playsinline muted></video><div class="viewfinder" aria-hidden="true"></div>
    <div class="camera-top"><a href="#/section" aria-label="Fechar"><button>✕</button></a><span>Escanear boletim</span><span style="width:44px"></span></div>
    <div class="sheet" aria-live="polite"><b id="title">Aponte para o QR Code do boletim</b><div class="muted" id="sub">Leia todos os QR Codes, um de cada vez.</div>
    <div class="qr-parts" id="qrs"></div><div id="error"></div>
    ${navigator.onLine ? '' : '<div class="offline" style="margin:8px 0">📶 Sem internet. Tudo fica salvo no celular e é enviado quando a conexão voltar.</div>'}
    <label class="btn outline" style="width:100%;margin:8px 0 0">Usar foto da galeria<input type="file" accept="image/*" class="sr" id="photo"></label></div></div>`
  const { startCamera, readImage } = await import('./scanner')
  document.querySelector<HTMLInputElement>('#photo')!.addEventListener('change', async ev => {
    const f = (ev.target as HTMLInputElement).files?.[0]
    if (f) (await readImage(f)).forEach(onRead)
  })
  try { stopCamera = await startCamera(document.querySelector('video')!, onRead) }
  catch { document.querySelector('#sub')!.textContent = 'Não conseguimos abrir a câmera. Use uma foto da galeria.' }
}

async function onRead(text: string): Promise<void> {
  if (!reads.includes(text)) reads.push(text)
  const p = progress(reads)
  const qrs = document.querySelector('#qrs')
  if (!qrs) return
  qrs.innerHTML = Array.from({ length: p.total }, (_, i) => `<span class="${p.read.includes(i + 1) ? 'read' : ''}">${i + 1}</span>`).join('') +
    (p.total ? `<span class="${p.certificate ? 'read' : ''}">certificado</span>` : '')
  document.querySelector('#title')!.textContent = p.total ? `Lido ${p.read.length} de ${p.total}` : 'Aponte para o QR Code do boletim'
  document.querySelector('#sub')!.textContent = p.total && p.read.length < p.total ? 'Aproxime o próximo QR Code.' : ''
  if (!p.total || p.read.length < p.total) return
  try {
    const ballot = await assemble(reads)
    stopCamera?.(); stopCamera = null
    sessionStorage.setItem('ballot-read', JSON.stringify(ballot))
    location.hash = '#/review'
  } catch (e) {
    document.querySelector('#error')!.innerHTML = `<div class="error-box" style="margin:8px 0">${esc(e instanceof BallotError ? e.message : 'Não foi possível ler o boletim.')}</div>`
  }
}

// ---------- Review (ballot read) ----------
async function viewReview(): Promise<void> {
  const ballot = JSON.parse(sessionStorage.getItem('ballot-read') ?? 'null') as Ballot | null
  if (!ballot) { location.hash = '#/scan'; return }
  const f = ballot.fields
  const president = ballot.offices.find(o => o.CARG === '1') ?? ballot.offices[0]
  const v = officeVotes(president)
  const other = !isOfficial2026(ballot) // only official 2026 ballots count
  const cands = other ? null : await loadCandidates(1) // 2026 names only apply to the 2026 election
  const byNumber = Object.fromEntries((cands?.offices['1'] ?? []).map(c => [c.n, c]))
  const rows = order(Object.keys(v).filter(k => /^\d+$/.test(k)), v).map(n =>
    `<div class="list-row"><div><b>${esc(byNumber[n]?.name ?? `Candidato ${n}`)}</b><small>${esc(byNumber[n]?.party ?? '')} · ${esc(n)}</small></div><b>${v[n]}</b></div>`).join('')
  const otherMsg = `${f.FASE !== 'O' ? 'Este é um boletim de simulação ou treinamento' : `Este boletim é de outra eleição (${esc(f.DTPL?.slice(0, 4))})`}. Ele está íntegro, mas não entra na conferência de 2026.`
  app.innerHTML = `<header class="top-bar"><div class="brand">Boletim lido<small>Zona ${esc(f.ZONA)} · Seção ${esc(f.SECA)} · ${esc(f.UNFE)} · município ${esc(f.MUNI)}</small></div></header>
    <div class="card"><span class="pill" style="background:var(--ok)">✓ BOLETIM ÍNTEGRO</span>
      <div style="margin-top:8px">Urna <b>${esc(f.IDUE)}</b> · fechada às <b>${esc((f.HRFC ?? '').replace(/(\d\d)(\d\d)\d\d/, '$1:$2'))}</b><br>
      ${ballot.texts.filter(t => t.startsWith('QRBU')).length} QR Code(s) · cadeia de hash e somas conferidas${ballot.certificate ? ' · certificado lido' : ''}<br>
      <span class="muted">A assinatura da urna é verificada no servidor, ao enviar.</span></div></div>
    <div class="card">${rows}<div class="list-row"><b>Brancos / Nulos</b><b>${v.BRAN} / ${v.NULO}</b></div></div>
    <div class="card muted">🔒 Enviamos só o boletim, sem a sua localização. Você não precisa criar conta.</div>
    ${other ? `<div class="error-box">${otherMsg}</div>` : '<button class="btn" id="send">Enviar e registrar</button>'}<a class="btn outline" href="#/scan">Ler de novo</a>`
  document.querySelector('#send')?.addEventListener('click', async () => {
    const saved = savedPlace()
    const p: Place = { uf: f.UNFE, municipality: saved.municipalityCode === f.MUNI ? saved.municipality : `Município ${f.MUNI}`, municipalityCode: f.MUNI, zone: f.ZONA, section: f.SECA }
    savePlace(p)
    localStorage.setItem('turn', f.TURN ?? String(turn()))
    const votes = Object.fromEntries(ballot.offices.map(o => [o.CARG, officeVotes(o)]))
    recordDoorBallot(Number(f.TURN ?? turn()), p, { votes, time: new Date().toTimeString().slice(0, 5), submissions: 1, urna: f.IDUE })
    enqueue(ballot.texts)
    await flush()
    sessionStorage.removeItem('ballot-read')
    location.hash = '#/section'
  })
}

// ---------- Coverage ----------
let ufPaths: Record<string, string> | null = null
const updated = (iso?: string) => (iso ? `atualizado ${new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}` : 'sem envios ainda')

async function viewCoverage(): Promise<void> {
  const t = turn()
  const [C, paths] = await Promise.all([loadCoverage(t), ufPaths ?? fetch(`${import.meta.env.BASE_URL}uf-paths.json`).then(r => r.json())])
  ufPaths = paths
  const total = C?.totalSections ?? 517179, st = C?.byStatus ?? {}
  const share = (n = 0) => n / total
  const color = (x: number) => (x > .7 ? 'var(--cov-hi)' : x >= .4 ? 'var(--cov-mid)' : x > 0 ? 'var(--cov-lo)' : '#E2ECEA')
  const map = Object.entries(ufPaths!).map(([uf, d]) => `<path d="${d}" fill="${color(C?.byUF[uf] ?? 0)}"><title>${uf}: ${pct(C?.byUF[uf] ?? 0)}</title></path>`).join('')
  app.innerHTML = `<header class="top-bar"><div class="brand">Cobertura<small>${fmt(total)} seções · ${t}º turno · ${updated(C?.updatedAt)}</small></div></header>
    <div class="card"><div class="big">${pct(share(C?.checked))}</div><div class="muted">${fmt(C?.checked ?? 0)} seções já têm o boletim da porta enviado</div>
      <div class="bar"><i style="width:${share(st.identical) * 100}%;background:var(--ok)"></i><i style="width:${share(st.waiting) * 100}%;background:var(--secondary)"></i><i style="width:${share((st.divergent ?? 0) + (st.conflict ?? 0)) * 100}%;background:var(--bad)"></i></div>
      <div class="legend"><span><i style="background:var(--ok)"></i>idênticas ${fmt(st.identical ?? 0)}</span><span><i style="background:var(--secondary)"></i>aguardando TSE ${fmt(st.waiting ?? 0)}</span><span><i style="background:var(--bad)"></i>divergentes ${fmt((st.divergent ?? 0) + (st.conflict ?? 0))}</span><span><i style="background:#E2ECEA"></i>sem envio</span></div></div>
    <div class="card"><h3>Por estado</h3><svg class="map" viewBox="0 0 300 300" role="img" aria-label="Mapa do Brasil: cobertura por estado">${map}</svg>
      <div class="muted">Exterior (ZZ): <b>${pct(C?.byUF.ZZ ?? 0)}</b></div>
      <div class="legend"><span><i style="background:var(--cov-hi)"></i>&gt;70%</span><span><i style="background:var(--cov-mid)"></i>40–70%</span><span><i style="background:var(--cov-lo)"></i>até 40%</span><span><i style="background:#E2ECEA"></i>nenhum envio</span></div></div>
    <a class="btn outline" href="#/section">Ver a minha cidade →</a>` + nav('coverage')
}

// ---------- Divergences ----------
let divFilter = ''
async function viewDivergences(): Promise<void> {
  const t = turn()
  const data = await loadDivergences(t)
  const items = data?.items ?? []
  const ufs = [...new Set(items.map(d => d.uf))].sort()
  const shown = items.filter(d => !divFilter || d.uf === divFilter)
  const label = (k: string) => { const [o, n] = k.split(':'); return `${OFFICE_LABEL[o] ?? ''} ${n === 'BRAN' ? 'brancos' : n === 'NULO' ? 'nulos' : n}`.trim() }
  const rows = shown.map((d, i) => `<button class="list-row div-row" data-i="${items.indexOf(d)}"><div><b>${esc(titleCase(d.municipality))}, ${esc(d.uf)}</b>
      <small>Zona ${d.zone} · Seção ${d.section} · ${d.status === 'conflict' ? 'boletins da porta diferentes entre si' : d.differences.slice(0, 2).map(x => `${esc(label(x.key))}: ${x.door} × ${x.tse}`).join(' · ')}</small></div>
      <span class="pill" style="background:${d.status === 'explained' ? 'var(--pend)' : 'var(--bad)'}">${d.status === 'explained' ? 'explicada' : d.status === 'conflict' ? 'conflito' : `${d.differences.length} campo(s)`}</span></button>`).join('')
  app.innerHTML = `<header class="top-bar"><div class="brand">Divergências encontradas<small>${t}º turno · ${updated(data?.updatedAt)}</small></div></header>
    ${ufs.length > 1 ? `<div class="chips" role="group" aria-label="Filtrar por estado"><button data-uf="" aria-pressed="${!divFilter}">Brasil</button>${ufs.map(u => `<button data-uf="${u}" aria-pressed="${divFilter === u}">${u}</button>`).join('')}</div>` : ''}
    <div class="card"><div class="big" style="color:var(--bad)">${shown.filter(d => d.status !== 'explained').length}</div><div class="muted">seções com diferença entre a porta e o TSE</div></div>
    <div class="card">${rows || '<p class="muted">Nenhuma divergência até agora.</p>'}</div>
    <div class="card muted">Divergência é um fato a ser explicado (urna de contingência, erro de leitura etc.), não prova de fraude. Cada caso tem as provas abertas.</div>` + nav('divergences')
  document.querySelectorAll<HTMLButtonElement>('[data-uf]').forEach(b => b.addEventListener('click', () => { divFilter = b.dataset.uf!; viewDivergences() }))
  document.querySelectorAll<HTMLButtonElement>('.div-row').forEach(b => b.addEventListener('click', () => {
    const d = items[+b.dataset.i!]
    savePlace({ uf: d.uf, municipality: titleCase(d.municipality), municipalityCode: d.key.split(':')[2], zone: String(d.zone), section: String(d.section) })
    if (d.differences[0]) localStorage.setItem('office', d.differences[0].key.split(':')[0]) // open the diverging office
    location.hash = '#/section'
  }))
}

// ---------- Candidate page ----------
const brl = (n: number) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
const cap = (s?: string) => (s ? titleCase(s) : '')

async function viewCandidate(sq: string): Promise<void> {
  const c = await loadCandidatePage(sq)
  if (!c) { app.innerHTML = `<div class="card">Candidato não encontrado.</div>` + nav(''); return }
  const resultBadge = c.result === 'ELEITO' || c.result?.startsWith('ELEITO')
    ? '<span class="badge elected">Eleito · TSE</span>' : c.result === '2º TURNO' ? '<span class="badge runoff">2º turno · TSE</span>' : ''
  const row = (label: string, value?: string | number | null) => (value || value === 0 ? `<div class="list-row"><span class="muted">${label}</span><b>${esc(value)}</b></div>` : '')
  const assets = c.assets ? `<div class="card"><h3>Bens declarados ao TSE</h3><div class="big">${brl(c.assets.total)}</div>
      ${c.assets.items.map(i => `<div class="list-row"><span>${esc(i.type)}</span><b>${brl(i.value)}</b></div>`).join('')}</div>` : ''
  app.innerHTML = `<header class="top-bar"><div class="row"><a href="javascript:history.back()" class="back" aria-label="Voltar">←</a><div class="brand">${esc(cap(c.office))}<small>${esc(cap(c.scope))}</small></div></div></header>
    <div class="card profile"><img class="photo big-photo" src="${photoUrl(c.sq)}" alt="Foto oficial de ${esc(c.name)}" width="96" height="96">
      <div><div class="big">${esc(c.name)}</div><div class="muted">${esc(c.party)} · ${esc(c.number)}</div>${resultBadge}</div></div>
    <div class="card">${row('Nome completo', cap(c.fullName))}${row('Partido', cap(c.partyName))}${row('Federação', cap(c.federation))}${row('Coligação', cap(c.coalition))}
      ${row('Partidos da coligação', c.coalitionParties)}${row('Situação da candidatura', cap(c.candidacyStatus))}${row('Resultado (TSE)', cap(c.result))}</div>
    <div class="card">${row('Idade na eleição', c.age ? `${c.age} anos` : '')}${row('Gênero', cap(c.gender))}${row('Cor/raça (autodeclarada)', cap(c.race))}
      ${row('Escolaridade', cap(c.education))}${row('Ocupação declarada', cap(c.occupation))}${row('UF de nascimento', c.birthUf)}</div>
    ${assets}
    <div class="card muted">Fonte: TSE, dados abertos de candidaturas 2026 (cadastro e bens declarados). Não exibimos CPF, título eleitoral nem e-mail.</div>` + nav('')
}

// ---------- Replay (1st round): national sum + how the count moved, from TSE per-section data ----------
type ReplayPoint = { t: string; sections: number; pct: number; valid: number; votes: Record<string, number> }
const PAUSE = ['2026-10-04 19:14', '2026-10-04 20:04'] // "Brasil" tab frozen at 64,81% (TSE note, 06/10)

async function viewReplay(): Promise<void> {
  const base = `${import.meta.env.BASE_URL}aggregates/1/`
  const get = (f: string) => fetch(base + f, { cache: 'no-cache' }).then(r => (r.ok ? r.json() : null)).catch(() => null)
  const [N, R, idx] = await Promise.all([get('national.json'), get('replay.json'), loadCandidates(1)])
  if (!N || !R) { app.innerHTML = `<div class="card">Dados da apuração ainda não gerados.</div>` + nav(''); return }
  const top = (idx?.offices['1'] ?? []).slice(0, 2) as Candidate[]
  const colors = ['var(--primary)', 'var(--accent)']
  const pts = (R.points as ReplayPoint[]).filter(p => p.pct >= 1)
  const share = (p: ReplayPoint, n: string) => (p.votes[n] ?? 0) / p.valid * 100
  const ms = (t: string) => Date.parse(t.replace(' ', 'T') + ':00-03:00')
  const end = pts.find(p => p.pct >= 99.5) ?? pts[pts.length - 1]
  const shown = pts.filter(p => ms(p.t) <= ms(end.t))
  const [t0, t1] = [ms(shown[0].t), ms(end.t)]
  const vals = shown.flatMap(p => top.map(c => share(p, c.n)))
  const [y0, y1] = [Math.floor(Math.min(...vals)) - 1, Math.ceil(Math.max(...vals)) + 1]
  const W = 320, H = 180, x = (t: number) => (t - t0) / (t1 - t0) * W, y = (v: number) => H - (v - y0) / (y1 - y0) * H
  const line = (n: string) => shown.map((p, i) => `${i ? 'L' : 'M'}${x(ms(p.t)).toFixed(1)},${y(share(p, n)).toFixed(1)}`).join('')
  const hhmm = (t: string) => t.slice(11, 16)
  const at = (t: string) => [...shown].reverse().find(p => p.t <= t) ?? shown[0]
  const pause = PAUSE.map(t => x(ms(t)))
  const rows = top.map(c => `<div class="list-row"><span>${esc(c.name)} (${c.n})</span><b>${fmt(N.votes[c.n] ?? 0)}</b><span class="muted">TSE ${fmt(N.declared[c.n])} · dif. ${fmt(N.diff[c.n])}</span></div>`).join('')
  app.innerHTML = `<header class="top-bar"><div class="row"><a href="javascript:history.back()" class="back" aria-label="Voltar">←</a><div class="brand">Refaça a apuração<small>Presidente · 1º turno · dados oficiais do TSE</small></div></div></header>
    <div class="card"><h3>Soma pública</h3><div class="big" style="color:${N.match ? 'var(--ok)' : 'var(--bad)'}">${N.match ? 'Bate com o TSE' : 'Diferença a ser explicada'}</div>
      <div class="muted">Somamos os votos das ${fmt(N.sections)} seções publicadas pelo TSE, uma a uma, e comparamos com o total declarado.</div>${rows}</div>
    <div class="card"><h3>A apuração minuto a minuto</h3><div class="muted">Cada seção entra na hora em que o TSE recebeu o boletim. % dos votos válidos.</div>
      <svg viewBox="-28 -8 ${W + 36} ${H + 24}" role="img" aria-label="Evolução dos votos válidos durante a apuração" style="width:100%;height:auto">
        <rect x="${pause[0]}" y="0" width="${pause[1] - pause[0]}" height="${H}" fill="var(--off-bg)"/>
        <text x="${(pause[0] + pause[1]) / 2}" y="10" font-size="8" text-anchor="middle" fill="var(--off-ink)">aba Brasil parada</text>
        ${[y0, (y0 + y1) / 2, y1].map(v => `<text x="-4" y="${y(v) + 3}" font-size="8" text-anchor="end" fill="var(--ink-2)">${Math.round(v)}%</text>`).join('')}
        ${[shown[0].t, PAUSE[0], PAUSE[1], end.t].map(t => `<text x="${x(ms(t))}" y="${H + 12}" font-size="8" text-anchor="middle" fill="var(--ink-2)">${hhmm(t)}</text>`).join('')}
        ${top.map((c, i) => `<path d="${line(c.n)}" fill="none" stroke="${colors[i]}" stroke-width="2"/>`).join('')}
        <line id="cursor" x1="0" x2="0" y1="0" y2="${H}" stroke="var(--ink)" stroke-dasharray="2 2"/></svg>
      <input id="scrub" type="range" min="0" max="${shown.length - 1}" value="${shown.indexOf(at(PAUSE[0]))}" style="width:100%" aria-label="Momento da apuração">
      <div id="readout" class="muted"></div>
      <div class="legend">${top.map((c, i) => `<span><i style="background:${colors[i]}"></i>${esc(c.name)}</span>`).join('')}</div></div>
    <div class="card muted">Por que a curva se move? Os boletins não chegam todos juntos: cada região transmite num ritmo, então a vantagem muda conforme as seções entram. Isso não é projeção nem prova de nada: é a ordem de chegada dos dados oficiais. Às ${hhmm(PAUSE[0])} o site do TSE parou de atualizar a aba "Brasil" em 64,81% e voltou às ${hhmm(PAUSE[1])}. O gráfico mostra o que os boletins já recebidos somavam a cada minuto, inclusive nessa janela.</div>
    <div class="card muted">Fonte: TSE, boletins de urna por seção (dados abertos, bweb 1º turno). Qualquer pessoa refaz: <pre class="code">uv run python -m confere.replay build</pre></div>` + nav('')
  const scrub = document.querySelector<HTMLInputElement>('#scrub')!, cursor = document.querySelector('#cursor')!, readout = document.querySelector('#readout')!
  const show = () => {
    const p = shown[+scrub.value]
    cursor.setAttribute('x1', String(x(ms(p.t)))); cursor.setAttribute('x2', String(x(ms(p.t))))
    readout.innerHTML = `<b>${hhmm(p.t)}</b> · ${p.pct.toLocaleString('pt-BR')}% das seções · ${top.map(c => `${esc(c.name)} ${share(p, c.n).toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`).join(' · ')}`
  }
  scrub.addEventListener('input', show); show()
}

// ---------- About ----------
function viewAbout(): void {
  app.innerHTML = `<header class="top-bar"><div class="brand">Como funciona<small>conferência cidadã · código aberto</small></div></header>
    <div class="card"><h3>1. Às 17h, o boletim vai para a porta</h3>Por lei, cada urna imprime o boletim com todos os votos da seção, assinado digitalmente, e ele fica afixado na porta.</div>
    <div class="card"><h3>2. Você escaneia o QR Code</h3>O app confere no celular se o boletim está íntegro. Sem internet? Fica salvo e é enviado depois.</div>
    <div class="card"><h3>3. Comparamos com o TSE</h3>Quando o TSE publica a sua seção, mostramos se é idêntico ou se há divergência, sempre com as provas.</div>
    <div class="card"><h3>Verificar sem o app</h3>Todo envio entra num registro público encadeado por hashes, com checkpoints de hora em hora ancorados no OpenTimestamps. Qualquer pessoa baixa o registro e confere com o código aberto:
      <pre class="code">uv run python -m confere.public_log verify log/2</pre>
      <a href="${import.meta.env.BASE_URL}log/${turn()}/checkpoints.json" target="_blank" rel="noopener">Ver checkpoints do ${turn()}º turno</a></div>
    <div class="card"><h3>Refaça a apuração do 1º turno</h3>Somamos as seções publicadas pelo TSE e mostramos, minuto a minuto, como a contagem andou.<br><a href="#/replay">Ver a soma e a curva →</a></div>
    <div class="card muted">Resultados e situação dos candidatos ("Eleito", "2º turno") vêm do TSE. Não fazemos projeção. Não pedimos conta nem localização. Código aberto (AGPL-3.0): qualquer pessoa refaz a conta.</div>` + nav('about')
}

// ---------- router ----------
let renderSeq = 0
function render(): void {
  if (location.hash !== '#/scan') { stopCamera?.(); stopCamera = null }
  const route = location.hash.replace('#/', '') || 'section'
  if (route.startsWith('candidate/')) { viewCandidate(route.slice('candidate/'.length)); window.scrollTo(0, 0); return }
  const views: Record<string, () => void | Promise<void>> = { section: viewSection, scan: viewScan, review: viewReview, coverage: viewCoverage, divergences: viewDivergences, about: viewAbout, replay: viewReplay }
  const seq = ++renderSeq
  Promise.resolve((views[route] ?? viewSection)()).then(() => { if (seq === renderSeq) window.scrollTo(0, 0) })
}

addEventListener('hashchange', render)
addEventListener('online', async () => { await flush(); render() })
render()
if ('serviceWorker' in navigator && import.meta.env.PROD) navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`)
