# Intent: Conferência cidadã dos Boletins de Urna (nome provisório: resultado-eleicao-2026)

**Data:** 2026-10-11 · **Prazo:** 2º turno em 25/10/2026, das 8h às 17h (horário de Brasília) · **Fonte:** `.memlog.md` e as pesquisas 01 a 05 e testes 01 e 02 desta pasta.

## Problema
No 1º turno (04/10/2026), o placar nacional do TSE travou por cerca de 50 minutos. Não havia outra fonte. Falta também uma forma pública de provar que **o que a urna imprimiu na seção é o que chegou à totalização**, ou seja, que a mídia de resultado não foi trocada no caminho.

## Promessa (única)
Provar, seção por seção, que o BU afixado na porta é **idêntico** ao BU publicado pelo TSE. Se for, o app reforça a confiança no TSE. Se não for, a divergência fica pública e com prova.
**Não faz:** projetar vencedor, recontar votos individuais nem verificar se a urna registrou certo o que o eleitor digitou.

## Fatos técnicos que sustentam o produto
- O QR do BU de 2026 (`VRQR:6.0`) traz todos os votos e a identificação da seção: UF, município, zona, seção, agregadas, local e `IDUE`. A cadeia de hashes é SHA-512, e a assinatura `ASSI` é EdDSA E-521 (urnas 2020/22) ou ECDSA P-521 (urnas 2013/15). O certificado da urna vem nos QRs `QRCE`. A especificação está em `tse/manual-qrcode-2026.pdf`.
- **Brecha:** o manual não descreve a cadeia de confiança do certificado. A mitigação é a consistência `IDUE → certificado` entre capturas independentes, cruzada com os arquivos do TSE.
- O TSE publica por seção, em `resultados.tse.jus.br/oficial/ele2026/arquivo-urna/<pleito>/dados/<uf>/<mun>/<zona>/<secao>/`, os arquivos `bu.dat` (ASN.1, cerca de 8 KB), `vota.vsc`, `rdv.dat` e `log.jez`. O pleito é 3220 no 1º turno e 3221 no 2º. **Acesso só de IP brasileiro.**
- A leitura de QR a partir de foto já foi provada (teste 01). A decodificação do `bu.dat` já foi provada de forma heurística (teste 02).
- A zerésima não tem assinatura digital. É assinada à mão, afixada na seção e traz o `IDUE` e a hora.

## Princípios
Anônimo por padrão (sem GPS no servidor, EXIF removido) · open source AGPL-3.0 · neutralidade visível (as duas campanhas, OAB, universidades e imprensa convidadas) · linguagem de "conferência", nunca de "vencedor" · tudo auditável: log append-only, carimbo de tempo e link verificável por seção.

## Escopo MoSCoW (até 25/10)
**Must**
1. PWA web: escanear todos os QRs do BU, offline, com fila de envio; aceitar também upload de foto.
2. Validador: sequência, cadeia SHA-512 e assinatura E-521/P-521 via `QRCE`, com consistência do certificado por `IDUE`.
3. Log público append-only, com hash de cada captura e carimbo de tempo.
4. Espelho próprio dos arquivos do TSE por seção. Comparação BU da porta × `bu.dat` com status ✅ igual / 🚨 divergente / ⏳ pendente.
5. Página pública por seção (link verificável), página "Divergências encontradas" e cobertura em %.
6. Anti-abuso sem conta: proof-of-work ou Turnstile, rate limit, deduplicação e alerta para BUs com `ORIG` RED/SA.
7. **Piloto no 1º turno:** quem tem foto do BU de 04/10 escaneia e compara agora.
8. Revisão dos textos por advogado eleitoral antes de lançar.

**Should:** bot de WhatsApp (o bot pede os QRs que faltam; orientar envio "como documento") · foto da zerésima cruzada com `IDUE`/`HRAB` e com o `log.jez` · auditores voluntários para os BUs sem QR legível (consenso de 3 a 5) · conselho de neutralidade.
**Could:** OCR/IA de fallback (Gemma 3 12B) · âncora OpenTimestamps · cruzamento entre 1º e 2º turno por seção · apps nativos nas lojas.
**Won't (agora):** projeção de resultado · auditoria de RDV/digitação · cadastro obrigatório · geolocalização obrigatória.

## Riscos principais
O prazo de 14 dias · a cadeia de confiança do certificado não documentada (pedir a AC raiz a qrcodenobu@tse.jus.br) · o bloqueio geográfico do TSE (o espelho precisa rodar no Brasil) · prints falsos ("sem link, não vale") · enquadramento como desinformação (Res. 23.610, art. 323 do CE) · DDoS (CDN e JSON estático).

## Pendências imediatas
1. Um BU real de 2026 (foto com todos os QRBU e QRCE) para testar a assinatura E-521.
2. Baixar o `vota.vsc` e o `bu.asn1` oficial (decodificador não heurístico).
3. Confirmar se o `log.jez` registra a zerésima.
