# Teste 02: arquivo da urna publicado pelo TSE, Senador Cortes/MG, zona 170, seção 37 (2026-10-11)

**Como obter (só funciona com IP do Brasil, então usei o Chrome do Alino):**
1. Lista de seções: `resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3220/config/mg/mg-p003220-cs.json`. O pleito do 1º turno de 2026 é o **3220**; o do 2º turno é o **3221**. Senador Cortes é o município **53112**.
2. Índice da seção: `.../arquivo-urna/3220/dados/mg/53112/0170/0037/p003220-mg-m53112-z0170-s0037-aux.json`. Mostra o status (Totalizada), o hash e a lista de arquivos, recebidos em 04/10 às 18:47.
3. Arquivos: `.../0037/<hash>/o03220mg5311201700037-{bu.dat, vota.vsc, rdv.dat, log.jez}`. Tamanhos: BU 8,4 KB; assinaturas 62 KB; RDV 12 KB; log 90 KB.

**Resultado:** o `bu.dat` é ASN.1 DER. Decodifiquei com um parser heurístico (`prototipo/ler_bu_dat.py`):

| Presidente (cargo 1) | Votos |
|---|---|
| 13 | 109 |
| 22 | 63 |
| 55 | 8 |
| 70 | 6 |
| 14, 30, 80 | 1 cada |
| Brancos (tipo 2) | 2 |
| Nulos (tipo 3) | 4 |
| **Total** | **195** |

Saída completa, com todos os cargos: `tse/secao-mg-53112-0170-0037/votos-decodificados.txt`. O tipo 4 é voto de legenda.

**Descobertas:**
- O TSE publica o BU **por seção**, em arquivo pequeno, com uma assinatura de 64 bytes **por candidato** dentro do BU.
- O índice traz o **horário de recebimento** (18:47 no 1º turno). Isso ajuda a medir o caminho entre a urna e o TSE.
- O `vota.vsc` (assinaturas) não baixou: o Chrome bloqueia vários downloads seguidos. Precisa de uma nova tentativa.
- **Isso viabiliza o teste do 1º turno já:** quem tem foto do BU do 1º turno escaneia, e o app compara com este arquivo da mesma seção.

**Pendências:** decodificar com o `bu.asn1` oficial (o parser atual é heurístico); verificar as assinaturas do `vota.vsc`; mapear os códigos de candidato para nomes (JSON de complemento do TSE).
