# Apuração Cidadã

**#EuFiscalizo** · Citizen check of Brazil's election ballot reports (Boletins de Urna).

At 17h every voting machine prints a signed ballot report (BU) with a QR Code and posts it on the polling-section door. Voters scan it; we compare it, section by section, with the BU the TSE publishes. Identical → proof. Different → a public divergence, with the photo, to be explained.

- `app/` PWA (Vite + TypeScript): scan, section status, coverage map, divergences, 1st-round replay
- `edge/` Cloudflare Worker: ingestion, rate limit, raw storage, queue
- `server/` Python: TSE mirror, `bu.dat` decoder, signature checks, comparison, public hash-chain log (OpenTimestamps)
- `shared/` QR parsing and hash chain (TypeScript)
- `_bmad-output/` research, spec and UX planning

Anonymous by default (no account, no GPS, EXIF stripped). Neutral: we never project results; official results only as declared by the TSE.

Run and architecture notes: see [CLAUDE.md](CLAUDE.md).

License: [AGPL-3.0](LICENSE), except `shared/` (QR parsing, hash chain, public data model), which is [MIT](shared/LICENSE) so anyone can reuse the ballot check in any app.
