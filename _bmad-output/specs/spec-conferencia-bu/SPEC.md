---
id: SPEC-conferencia-bu
companions:
  - tse-formatos.md
  - fluxos.md
  - stack.md
  - ../../planning-artifacts/ux-designs/ux-resultado-eleicao-2026-2026-10-11/DESIGN.md
  - ../../planning-artifacts/ux-designs/ux-resultado-eleicao-2026-2026-10-11/EXPERIENCE.md
  - ../../brainstorming/brainstorm-contagem-paralela-2026-2026-10-11/tse/manual-qrcode-2026.pdf
sources:
  - ../../brainstorming/brainstorm-contagem-paralela-2026-2026-10-11/brainstorm-intent.md
---

> **Contrato canônico.** Esta SPEC e os arquivos em `companions:` são o contrato completo. As fontes servem só para rastreabilidade.

# Conferência cidadã dos Boletins de Urna

## Why

**Mandato com prazo e lacuna de confiança.** No 1º turno (04/10/2026), o placar nacional do TSE travou por cerca de 50 minutos, e não havia outra fonte. Falta também um meio público de provar que o BU impresso e afixado na seção é o mesmo que entrou na totalização, ou seja, que ninguém trocou a mídia de resultado no caminho. O 2º turno é em 25/10/2026. Eleitores, imprensa e as duas campanhas ganham uma prova independente, aberta e verificável: se o resultado bate, reforça o TSE; se diverge, a divergência fica exposta com prova.

## Capabilities

- **CAP-1**
  - **intent:** O eleitor captura, pelo navegador do celular, todos os QR Codes de um BU (QRBU e QRCE), mesmo sem internet, e o envio acontece quando a conexão voltar. Uma foto do BU também é aceita.
  - **success:** Num celular Android de entrada em modo avião, um BU de 2026 é lido por completo; ao reconectar, ele aparece no registro público em menos de 60 s. Uma foto com QR legível produz o mesmo resultado.
- **CAP-2**
  - **intent:** O sistema confirma que o BU capturado é autêntico e íntegro: sequência completa, cadeia SHA-512 e assinatura `ASSI` com a chave do certificado `QRCE` (EdDSA E-521 ou ECDSA P-521).
  - **success:** Um BU real de 2026 passa. O mesmo BU com 1 voto alterado, 1 QR faltando ou o certificado trocado falha, com o motivo em português.
- **CAP-3**
  - **intent:** Cada captura aceita entra num registro público append-only, com hash e carimbo de tempo que qualquer pessoa pode verificar de forma independente.
  - **success:** Um terceiro, só com dados públicos, prova que o BU X estava registrado antes da hora H e que nenhuma entrada foi removida ou alterada.
- **CAP-4**
  - **intent:** O sistema obtém uma única vez o BU publicado pelo TSE para cada seção e o compara com o BU capturado, marcando a seção como ✅ igual, 🚨 divergente ou ⏳ pendente.
  - **success:** Na seção 37 de Senador Cortes/MG (pleito 3220), um BU idêntico resulta em ✅ e um BU com votos diferentes resulta em 🚨, com o campo divergente indicado.
- **CAP-5**
  - **intent:** Qualquer pessoa consulta uma página pública por seção (link verificável), uma página "Divergências encontradas" e a cobertura nacional em %, sem projetar vencedor.
  - **success:** A página da seção mostra o BU da porta lado a lado com o BU do TSE, as provas (QR, foto, entrada no registro) e o status. Nenhuma tela exibe "vencedor" ou "projeção". Uma divergência pode passar a "explicada" (documento anexado) sem sumir, e os observadores (OAB, imprensa e as duas campanhas) são alertados automaticamente.
- **CAP-6**
  - **intent:** O sistema resiste a envio em massa, a BU forjado e à contestação organizada sem exigir conta.
  - **success:** Um teste de carga com 10× o pico esperado não derruba a leitura pública. BUs duplicados são descartados. Um certificado diferente para o mesmo `IDUE` gera alerta. BUs com `ORIG` RED ou SA ficam sinalizados.
- **CAP-7**
  - **intent:** Antes do 2º turno, eleitores com BU do 1º turno (pleito 3220) já conseguem conferir sua seção.
  - **success:** Piloto público com pelo menos 100 seções conferidas até 22/10/2026.
- **CAP-8** *(Should)*
  - **intent:** O eleitor envia fotos do BU por WhatsApp, e o bot pede os QRs que faltarem até completar o BU.
  - **success:** Uma sequência de fotos enviadas como documento resulta em BU completo e no link da seção como resposta.
- **CAP-9** *(Should)*
  - **intent:** O eleitor registra a foto da zerésima, e o sistema cruza o código da urna e o horário com o BU final e com o log da urna.
  - **success:** Uma zerésima com `IDUE` diferente do BU final da mesma seção gera alerta "troca de urna, conferir ata".
- **CAP-10** *(Should)*
  - **intent:** Um BU sem QR legível vai para auditores voluntários sorteados, que transcrevem os números. Há consenso quando 3 de 5 concordam.
  - **success:** Uma transcrição divergente de um auditor não altera o resultado. Auditores calibrados por BUs-gabarito ocultos.

## Constraints

- Prazo fixo: o 2º turno é em 25/10/2026, com votação das 8h às 17h (Brasília). Pico estimado de ~500 mil BUs em cerca de 4h após o fechamento.
- `resultados.tse.jus.br` e `tse.jus.br` só respondem a IP brasileiro: o espelho e a coleta rodam no Brasil.
- Anônimo por padrão: sem conta para enviar, nenhum GPS enviado ao servidor, EXIF removido e rostos e assinaturas borrados nas fotos.
- Código aberto sob AGPL-3.0. Ficam fechados apenas segredos, limiares de anti-abuso e dados de auditores.
- Linguagem sempre de "conferência". Nunca exibir vencedor ou projeção. Textos públicos revisados por advogado eleitoral antes do lançamento.
- Web/PWA é o caminho crítico. Apps de loja e WhatsApp não podem bloquear o lançamento.
- Não sobrecarregar o TSE: cada arquivo oficial é baixado uma vez e servido a partir do espelho.
- Leitura pública servida como arquivos estáticos via CDN, para resistir a DDoS.
- Neutralidade visível: governança aberta às duas campanhas, OAB, universidades e imprensa. Nenhum elemento partidário na interface.
- Orientação a quem fotografa: só o papel, sem pessoas, do lado de fora da seção, sem confronto.

## Non-goals

- Projetar ou anunciar vencedor.
- Verificar se a urna registrou corretamente o que o eleitor digitou (RDV, teste de integridade).
- Recontagem voto a voto.
- Cadastro ou geolocalização obrigatórios para enviar.
- Apps nativos nas lojas antes de 25/10.

## Success signal

- Na noite de 25/10/2026, qualquer pessoa abre o link de uma seção e vê o BU da porta, assinado, comparado ao BU oficial com status ✅ ou 🚨. Um terceiro consegue reproduzir a verificação com o código aberto e os dados públicos, sem confiar no app.

## Assumptions


- A meta de 100 seções no piloto do CAP-7 foi definida por Claude, não pelo Alino.

## Open Questions

- **Bloqueante para CAP-2 e CAP-4:** a especificação ASN.1 de 2022 não decodifica o conteúdo do `bu.dat`/`vota.vsc` de 2026. Hoje só funciona o decodificador heurístico. E o ecpy público não tem a curva Ed521: verificar E-521 depende da biblioteca do TSE ou de implementação própria (e-mail ao TSE, perguntas 4 e 5).

- Qual AC raiz valida os certificados das urnas? E-mail ao TSE redigido: `../../brainstorming/brainstorm-contagem-paralela-2026-2026-10-11/email-tse-qrcode.md`.
- O `log.jez` registra a emissão da zerésima? (CAP-9)
- Nome do produto e domínio?
- Quem faz a revisão jurídica, e até quando?
- Could, fora do escopo mínimo: OCR/IA de fallback, âncora OpenTimestamps, cruzamento entre 1º e 2º turno por seção. Entram se sobrar tempo?
- Falta um BU real de 2026 (foto com todos os QRBU e QRCE) para validar o CAP-2.
