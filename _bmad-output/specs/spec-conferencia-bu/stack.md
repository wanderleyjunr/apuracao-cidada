# Stack recomendada (não obrigatória)

Fonte: `pesquisa-04-arquitetura-seguranca.md`. São recomendações. As restrições obrigatórias estão no SPEC.md.

- **Leitura de QR:** zxing-cpp em WASM no navegador; `zxing-cpp` em Python no servidor, para fotos (validado no teste 01).
- **Assinatura:** `ecpy` (EdDSA E-521 com SHAKE256; ECDSA P-521) e `asn1crypto`, conforme o exemplo do manual. Em ECDSA, OpenSSL como alternativa.
- **Ingestão:** um worker na borda recebe, e uma fila valida de forma assíncrona. Fotos em object storage.
- **Dados:** Postgres append-only, mais um log Merkle público (Tessera/C2SP) e âncora opcional em OpenTimestamps.
- **Leitura pública:** JSON e HTML estáticos em CDN, regenerados por seção.
- **Espelho TSE:** coletor em servidor com IP brasileiro, com cache imutável por hash do `aux.json`.
- **Anti-abuso:** ALTCHA/Cap (PoW) ou Turnstile, rate limit por IP e prefixo, e hash perceptual de fotos.
- **WhatsApp:** Cloud API oficial da Meta. Exige aprovação: começar o processo já.
- **OCR de fallback (Could):** Gemma 3 12B ou docTR.
- **Custo estimado do evento:** US$ 200–500, mais o servidor no Brasil.
