# Apuração Cidadã (app name, decided 2026-10-13; code package stays `confere`): citizen check of Brazil's Boletins de Urna

Open-source (AGPL-3.0) app: voters scan the signed QR Code of the **ballot report (BU) posted on the polling-section door at 17h**; we compare it, section by section, with the BU the **TSE publishes**. Promise: prove nothing changed between the urna and the TSE totalization (or expose divergence with proof). Hard deadline: **2nd round, 25/10/2026** (voting 8h–17h Brasília).

**Owner:** Alino (pt-BR). Talk to him short and direct, in Portuguese. **All code, identifiers, comments and commits in English**; only user-facing UI strings stay in Portuguese.

## Non-negotiables
- Show **official TSE results** (per section/zone, summed from published section results) and "Eleito"/"2º turno" **only as declared by the TSE** (label "· TSE"; decision by Alino 2026-10-11). Never our own projection, never sums built from door ballots. Never say "fraude"; use "divergência / a ser explicada".
- Verdict (identical/divergent) only after the TSE publishes the section.
- Anonymous by default: no account to submit, no GPS sent, strip EXIF, IP stored only as a daily-salted hash.
- Neutral: both candidates get identical visual treatment; brand colors never red (PT) nor green-yellow/blue (PL). Don't imitate TSE identity.
- TSE sites only answer **Brazilian IPs**; the mirror must run in Brazil (or via Alino's Chrome for one-off downloads).
- Max 5 concurrent subagents (Alino's rule).

## Layout
| Path | What | Status |
|---|---|---|
| `shared/ballot.ts` | QR parse, SHA-512 chain, sums, compare (TS) — used by app/ and edge/ | done, tested |
| `server/confere/ballot.py` | Same in Python + signature verification (Ed25519 v1.5; E-521/P-521 v6.0) | done, tested; E-521 blocked (see below) |
| `app/` | PWA (Vite + plain TS, no framework). Views: section, scan, review, coverage (Brazil map), divergences, about | v0 working with **demo data** (`app/src/data.ts`) |
| `edge/` | Cloudflare Worker: POST /api/ballots (rate limit, optional Turnstile, assemble+hash check, 2026-only, raw to R2 once, every submission to Queue) + PUT /internal/publish (token) | done, 4 tests; **not deployed** |
| `server/` | Python: `ballot.py`, `bu_dat.py` (TSE bu.dat decoder), `tse_mirror.py`, `compare.py`, `pipeline.py` (ingest→recompute→publish), `run.py` (consume/mirror loops), `schema.sql` (append-only, triggers) | done, 19 tests incl. Postgres integration; **not deployed**; alerts to observers TODO |
| `brand/logo/` | Logo kit (approved 2026-10-14, "QR conferido"): SVG masters, web/PWA + Expo icons, colours, usage. **Read its README before using the logo; never redraw it** | done; placed in PWA, Expo app and README |
| `fixtures/` | Real 2022 QR texts, 2026 manual example, real TSE files for MG/53112/zone 170/section 37 (1st round) | — |
| `_bmad-output/` | Planning: brainstorm + research, SPEC, UX (DESIGN.md/EXPERIENCE.md + mockups), video scripts | reference |

## Run
```bash
pnpm --dir app install && pnpm --dir app exec vite --port 5174   # also .claude/launch.json "app"
pnpm --dir app exec vitest run                                     # TS tests (shared + app)
cd server && uv run --group dev pytest -q                          # Python tests (Postgres test needs DATABASE_URL, see tests/test_pipeline.py)
pnpm --dir edge exec vitest run && pnpm --dir edge exec wrangler deploy --dry-run   # edge
```
Demo clock: `http://localhost:5174/?agora=2026-10-25T19:00:00-03:00#/section`. Turn in `localStorage.turn`.

**Local end-to-end (no Cloudflare):**
```bash
docker run -d --rm --name confere-pg -e POSTGRES_PASSWORD=dev -p 55433:5432 postgres:17
cd server && uv run python -m confere.dev_server          # POST /api/ballots on :8787 (Vite proxies /api)
PYTHONPATH=. uv run python -c "from confere.synthetic import make; ..."   # synthetic ballots: LOCAL TESTS ONLY
```
The dev server runs the production pipeline (assemble → ingest → recompute), seeds the TSE side from `results/` (bweb), and writes `app/public/sections/<turn>/<uf>/<mun>/<zone>/<section>.json` + a zone index `<zone>.json` (`{section: status}`) — git-ignored. The comparison flattens all offices (`"office:number"`), so in the 2nd round it covers President + Governor. Integration test uses its own DB `confere_test`.
Aggregates (`server/confere/aggregates.py`): `aggregates/<turn>/coverage.json` (checked sections by status + share per UF; denominators from the place index) and `aggregates/<turn>/divergences.json` (latest divergent/conflict per section, "explained" when a `divergence_events` row has a document). Dev server republishes per submission; `run.py` publishes them each mirror pass via the edge. App reads them fresh (no cache). The section sticker uses the server verdict (all offices), so a Governor divergence never reads as "identical" on the President tab; clicking a divergence opens the diverging office.
Public log (`server/confere/public_log.py`): hash chain over `submissions` (`entry_i = sha256(prev|final_hash|section_key|received_at)`), pages `log/<turn>/page-<k>.json` + `checkpoints.json`; production publishes hourly and anchors the head in OpenTimestamps (calendar `a.pool.opentimestamps.org`, sends only the hash; verified working). Anyone verifies with `uv run python -m confere.public_log verify <dir>` (tamper test → MISMATCH). Alerts (`confere/alerts.py`): POST to `OBSERVER_WEBHOOKS` only when a section *becomes* divergent/conflict (`doc["opened"]`); public facts + "não acusação"; failures never block ingestion.

## Key facts (verified)
- QR 6.0: parts `QRBU:n:N VRQR:6.0 <data> HASH:<sha512>`; `hashN = SHA-512(data1 HASH:h1 … dataN)` (confirmed with manual example); `ASSI` only on last part; urna certificate in `QRCE:n:x CERT:<hex>` parts.
- Signature 2026: EdDSA **E-521** (SHAKE256, OID 1.3.6.1.4.1.44588.2.1) for urnas 2020/22, ECDSA **P-521** for 2013/15. **Public ecpy 1.2.5 has no Ed521** → asked TSE (email sent 2026-10-11, `_bmad-output/brainstorming/.../email-tse-qrcode.md`). Manual does not document the certificate root CA → mitigation: IDUE→certificate consistency across independent submissions + compare with TSE files.
- TSE per-section files: `https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/<pleito>/` — pleito **3220** (1st round), **3221** (2nd). `config/<uf>/<uf>-p00<pleito>-cs.json` (sections + timestamps), `dados/<uf>/<mun>/<zona>/<secao>/p00<pleito>-<uf>-m<mun>-z<zona>-s<secao>-aux.json` (status + hash + file list), then `<hash>/o00<pleito><uf><mun><zona><secao>-{bu.dat,vota.vsc,rdv.dat,log.jez}`.
- `bu.dat` 2026 is ASN.1 DER; the **official 2022 ASN.1 spec only decodes the envelope** (format changed). Heuristic decoder: `_bmad-output/brainstorming/.../prototipo/ler_bu_dat.py`. Vote tuple: `SEQ{81 type, 82 count, A3{party, code,…}, 04 sig64}`; type 1 nominal, 2 blank, 3 null, 4 party; office 1 = President.
- Scale: 517,179 sections (499,248 print their own BU), ~158.7M voters; expect ~1.5M submissions in ~4h, peak ~1k/s.

## Server plan (decided 2026-10-11)
Cloudflare Worker ingest → R2 (raw, content-addressed, append-only) + Queue → Python on Brazil VPS (validate signature, TSE mirror, compare, publish per-section JSON to R2/CDN, alerts) → **Postgres on that VPS** (append-only tables: submissions, ballots, tse_ballots, comparisons, divergences). **No Redis** (Queue + Postgres unique keys cover it; revisit only if load test demands). Public log: hourly signed hash-chain checkpoint (GitHub + OpenTimestamps). Reads are static files on CDN.
Open: which Brazil VPS (AWS sa-east-1 / Magalu / Oracle SP); Cloudflare API token var name in `~/.claude/secrets.env`; app name + domain.

## Official results (1st round, MG done)
- `app/public/results/1/<uf>/<mun>/<zone>.json` — per-section TSE votes for offices 1/3/5 (+ apt, comp, received, urna, closed, agg). Built by `server/confere/bweb.py` from `cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/buweb/bweb_1t_<UF>_051020261403.zip` (+ `.sha512`; CDN works from abroad). MG: 898 zone files, 52,062 sections, 20 MB, median 9 KB. **Generated, git-ignored**: `uv run python -m confere.bweb <zip> ../app/public/results 1,3,5`. Other UFs: same command (SP zip is 1.4 GB).
- `app/public/results/1/candidates.json` — TSE-declared status (Eleito / 2º turno / Não eleito), votes, sqcand for President (BR), Governor and Senator (MG), from `fixtures/tse-official-status-1t.json` (extracted from resultados.tse.jus.br `*-u.jws`, Brazil-only) via `confere.candidates`.
- `app/public/photos/<sqcand>.webp` — 1,857 official photos (all MG candidates + President), 96 px WebP ~1 KB, from `foto_cand2026_{MG,BR}_div.zip` on the same CDN.
- Cross-check: CSV section 37/zone 170/Senador Cortes == decoded `bu.dat` (13:109, 22:63…).
- Performance rules: one small JSON per zone, memoized fetch, lazy images with fixed size, no framework, static files only (CDN + service worker cache).

## 2nd round line-up + candidate pages
- `results/2/candidates.json`: runoff declared by the TSE — President (13 × 22) and Governor in **AC, AM, DF, ES, RN, TO** (other UFs elected in the 1st round). Built by `confere.candidates` from `fixtures/tse-official-status-1t.json` + `fixtures/tse-official-status-1t-states.json` (all UFs, Governor+Senator). Keys: `"1"` and `"<office>:<uf>"`.
- App offices: 1st round = President, Governor, Senator (zone + section) and Dep. Federal/Estadual (**city totals only**, `results/1/<uf>/<mun>/city.json` + names in `results/1/<uf>/deputies.json`); 2nd round = President + Governor where there is a runoff. Before results exist, the runoff shows both candidates ordered by number (no ranking).
- `app/public/candidates/<sq>.json`: 20,989 candidate pages (all Brazil) from `consulta_cand_2026.zip` + `bem_candidato_2026.zip` (cdn.tse.jus.br/estatistica/sead/odsele/...) via `confere.candidate_pages` — **allow-list only; CPF, título, e-mail never copied**. Route `#/candidate/<sq>`; names/photos are links everywhere.
- `app/public/photos/<sq>.webp`: 20,986 official photos (all UFs, 21 MB, ~1 KB each) via `foto_cand2026_<UF>_div.zip` → `confere.photos` (96 px WebP, top-square crop).

## Load test (`server/loadtest.py`, story 9)
Consumer path is the bottleneck (reads are static). Results on Alino's Mac, one consumer process, local Postgres, P-521-signed synthetic ballots, 3 witnesses/section, 20k sections / 60k submissions: **~285 submissions/s, flat as the DB grows** (target ≥105/s → 1.5M in ~1.5h; scale by running more consumers). Edge validation (`shared/ballot.ts` assemble) **0.046 ms/ballot** (Cloudflare free limit 10 ms CPU).
Findings applied: missing index `submissions(final_hash)` caused a full scan per recompute (214→107/s as data grew; fixed → 285/s); P-521 verification via `cryptography`/OpenSSL (0.37 ms) instead of pure-Python ecpy (54 ms); signature checked once per distinct ballot, not per witness. **Open risk:** E-521 (urnas 2020/22, the majority) has no fast library yet — if the TSE library is slow, verify in a separate worker pool (status starts `unverified`). Self-signed forgeries are signature-valid by construction (test_signature.py) → needs IDUE→certificate check against TSE files.

## Place index
`app/public/places/<uf>.json` (28 files, 2.1 MB, 5,757 municipalities, 517,179 sections) built by `server/confere/places.py` from the TSE cs.json (1st round, pleito 3220). Feeds the cascading selector UF → municipality → zone → section (native selects, each unlocks the next; section optional). **Default view = whole zone** (all sections of the city in that zone with status chips, no vote sums); tapping a chip opens the section. Section numbers are per zone (zones span several cities), so numbers skip — this is correct, the UI explains it. State flags: `app/public/flags/<uf>.png` (Wikimedia Commons thumbnails, public domain); ZZ uses 🌎. Regenerate places for the 2nd round from pleito 3221 configs.

## Deploy (deferred: Alino doesn't want to pay yet — build everything locally first; `wrangler dev` runs the edge locally for free)
1. Cloudflare (token var name from Alino): `wrangler r2 bucket create apuracao-cidada-ballots` and `apuracao-cidada-public` (public via custom domain), `wrangler queues create apuracao-cidada-submissions`, `wrangler queues consumer http add apuracao-cidada-submissions`, `wrangler secret put IP_SALT|PUBLISH_TOKEN`, `wrangler deploy`.
2. Brazil VPS: Postgres + `psql -f server/schema.sql`; `uv sync`; env from `server/.env.example`; systemd running `uv run python -m confere.run all`.
3. App: `VITE_API_URL=<edge url>`; replace demo data in `app/src/data.ts` with fetch of `sections/<turn>/<uf>/<mun>/<zone>/<section>.json` from the public bucket.

## Next steps (stories: `_bmad-output/specs/spec-conferencia-bu/stories.yaml`)
1. Deploy edge + server (needs: Cloudflare token var name, Brazil VPS). Run the mirror for pleito 3220 to backfill 1st round.
2. Done locally: aggregates, observer alerts, hourly public log. Pending: council decides webhook list; OTS proof upgrade (`ots upgrade`) after Bitcoin confirmation.
3. Wire app to real API/static JSON; candidate photos from mirror; name→code lookup from cs.json.
4. Pilot with 1st-round ballots (story 8) after legal review of public texts.
5. Load test 10× peak (story 9). WhatsApp bot (10), zerésima (11), auditors (12) are "should".
UI polish will be done by a separate agent using `_bmad-output/planning-artifacts/ux-designs/ux-resultado-eleicao-2026-2026-10-11/`.

## Replay + national sum (1st round, President)
`server/confere/replay.py`: `extract <bweb.zip> <cache>` (President rows per section + `DT_BU_RECEBIDO`) for all 27 UFs + ZZ, then `build <cache> app/public/results/1/candidates.json app/public/aggregates/1` → `national.json` (sum vs TSE-declared) + `replay.json` (cumulative per minute by receipt time). App route `#/replay` (linked from About). Result (2026-10-13): 499,206 sections, **sum == declared for all 12 candidates**; no jump in the 19:14–20:04 "aba Brasil" pause (max 0.098 pp/min vs 0.075 outside); the lead shrank because later-arriving sections (BA, CE, PE, MA…) were Lula-heavy (Lula 49.1% in the pause window, 55.2% after).

## Mobile app (`mobile/`, Expo SDK 55, decided 2026-10-14) — proprietary, private repo `wanderleyjunr/apuracao-cidada-mobile` (git-ignored here)
Architecture: `_bmad-output/planning-artifacts/architecture/architecture-mobile-2026-10-13/ARCHITECTURE-SPINE.md` (thin client over the static-file contract; Expo, not Capacitor).
- Pure logic shared with the PWA: `shared/ballot.ts` + `shared/model.ts`. Mobile imports them as `@shared/*` from a synced copy (`npm run sync-shared`, runs on `npm start`); edit only the open-source originals here.
- `mobile/src/polyfills.ts` gives RN what the browser had: `crypto.subtle.digest` (SHA-512 via expo-crypto), `randomUUID`, `localStorage` (expo-sqlite). Imported first in `app/_layout.tsx`.
- Routes (expo-router): `(tabs)/index` section/zone, `coverage`, `divergences`, `about`, `scan-tab` (opens `/scan`), `scan` (expo-camera QR + gallery via `scanFromURLAsync`), `review`, `place`, `candidate/[sq]`.
- Only permission: camera. `.npmrc legacy-peer-deps=true` (react-dom optional web peer). Dev data: `.env.development` → Vite on :5174.
- Run: `cd mobile && npx expo start --ios` (Expo Go). Verified 2026-10-14: zone/section with real TSE data, gallery QR → assemble + SHA-512 chain in RN.
- EAS: project `@wanderleyalino/apuracao-cidada` (id 1626a101-…), bundle `com.apuracaocidada.app`, EAS Update on `u.expo.dev`. Icons/splash are still the Expo template (design pass pending).
- **National results (default screen, 2026-10-14):** `server/confere/national.py` mirrors the TSE's signed `br-c0001-e<ele>-u.jws` (ele 6257 = 1st round, **6258 = 2nd round**, from `/oficial/comum/config/ele-c.json`) every `NATIONAL_INTERVAL_S` (30 s, in `run.py mirror|all`) → `results/<turn>/national.json` (`NationalResults` in `shared/model.ts`). Copied, never computed. Mobile tab order: **Brasil** (default) · Seção · [Escanear] · Cobertura · Divergências; Sobre = ⓘ in the Brasil top bar. Before 17h: countdown + both candidates by number; from the first TSE number (0 → >0%): full-screen "A apuração começou" (`mobile/src/CountStart.tsx`, once per turn per device, key `count-start-shown:<turn>`), then animated bars, same color for every candidate. Generate locally: `uv run python -m confere.national <turn> ../app/public/results` (works from here; TSE answered our IP).
- **Onboarding (2026-10-14):** first launch = `mobile/app/welcome.tsx` (4 animated steps → "Em qual estado você vota?" → `/place?uf=` city → zone → section → Seção tab). No default city anywhere (`savedPlace()` may be null). Governor races: `results/<turn>/<uf>/governor.json` from `confere.national` (2nd round: AC, AM, DF, ES, RN per TSE config; TSE marked TO "2º turno" in the 1st round but publishes no TO runoff file).
- **Sponsors:** `app/public/sponsors.json` (`enabled` remote kill switch) + build flag `EXPO_PUBLIC_SPONSORS` (eas.json). Slots `brasil`, `sent`, `welcome`, `list` (Sobre). Spec + sales rules: `docs/patrocinio.md`. Submit to stores with `enabled: false`.
