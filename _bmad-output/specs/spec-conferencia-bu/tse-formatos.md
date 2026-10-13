# Formatos e fontes do TSE

## QR Code do BU, versão 2026 (`VRQR:6.0`)
Fonte: `manual-qrcode-2026.pdf`, seções 1.4 a 1.7.

- **Partes de dados:** `QRBU:n:N VRQR:6.0 <dados> HASH:<sha512hex>`. Só o último QR traz `ASSI:<hex>`.
- **Cadeia de hash:** `hash1 = SHA-512(dados1)` e `hashN = SHA-512(conteúdo(N-1) + " " + dadosN)`, sendo `conteúdo = dados HASH:hash ...`. Implementação de referência para o formato 1.5: `fabricioluna/apuracaojuntos`, `src/bu/hash.ts`.
- **Assinatura:** feita sobre os bytes de `hashN`.
  - Urnas UE2020/UE2022: EdDSA E-521 (SHAKE256, `hash_len=132`).
  - Urnas UE2013/UE2015: ECDSA P-521.
- **Certificado:** `QRCE:n:x` com o campo `CERT` em hex. É PEM nas urnas 2020/22 e DER nas 2013/15. É a única fonte da chave pública.
- **Campos-chave:** `UNFE` (UF), `MUNI`, `ZONA`, `SECA`, `AGRE` (seções agregadas), `LOCA`, `IDUE` (urna), `ORIG` (VOTA/RED/SA), `DTAB/HRAB` (abertura), `DTFC/HRFC` (fechamento), `APTO`, `COMP`, `FALT`, votos `<numero>:<qtd>`, `BRAN`, `NULO`, `TOTC`.
- **Nomes de candidatos:** JSON de complemento assinado em `qrcodenobu.tse.jus.br/json-bu/...`, com chave `s99999br-av.js` (Ed25519).
- **Formato 1.5 (2018–2024):** Ed25519 com chave por UF (`o<uf>qrcode.pub`). `HASH = SHA-512(dados)`, onde os dados não incluem o cabeçalho `QRBU VRQR VRCH`. Validado em 5 BUs de 2022 (teste 01).

## Arquivos de urna publicados por seção
Base: `https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/<pleito>/`. Pleito **3220** = 1º turno; **3221** = 2º turno. Exige IP brasileiro.

| Arquivo | Caminho |
|---|---|
| Lista de seções da UF | `config/<uf>/<uf>-p00<pleito>-cs.json` → `abr[].mu[]{cd,nm,zon[]{cd,sec[]{ns,da,ha}}}` |
| Índice da seção | `dados/<uf>/<mun>/<zona>/<secao>/p00<pleito>-<uf>-m<mun>-z<zona>-s<secao>-aux.json` → `st`, `hashes[]{hash, dr, hr, arq[]}` |
| Arquivos | `.../<secao>/<hash>/o00<pleito><uf><mun><zona><secao>-{bu.dat, vota.vsc, rdv.dat, log.jez}` |

- O índice traz a data e hora em que o TSE recebeu os dados (`dr`, `hr`). No exemplo: 04/10 às 18:47.
- `bu.dat` usa ASN.1 DER (cerca de 8 KB). Cada voto por candidato é `SEQ{81 tipo, 82 qtd, A3 {partido, código, ...}, 04 assinatura64}`, com tipo 1 = nominal, 2 = branco, 3 = nulo, 4 = legenda. O cargo 1 é presidente.
- Especificação oficial: "Formato dos arquivos de BU, RDV e assinatura digital", publicada para 2022 em `tse.jus.br/eleicoes/eleicoes-2022/documentacao-tecnica-do-software-da-urna-eletronica`. Não foi encontrada versão para 2026.
- CSV agregado por UF (`bweb_*`) em `dadosabertos.tse.jus.br`, publicado cerca de 2 dias após a eleição.

## Exemplo validado (seção 37 de Senador Cortes/MG, 1º turno)
`mun 53112`, `zona 0170`. Presidente: 13 = 109, 22 = 63, 55 = 8, 70 = 6, 14/30/80 = 1, brancos 2, nulos 4, total 195. Arquivos em `../../brainstorming/brainstorm-contagem-paralela-2026-2026-10-11/tse/secao-mg-53112-0170-0037/`.

## Zerésima
Não tem QR nem assinatura digital. É assinada à mão, afixada em local visível e traz `IDUE`, data e hora (TRE-SP, 03/10/2026).
