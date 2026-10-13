# Teste 01: leitura do QR de BUs reais (2026-10-11)

**Amostra:** 3 fotos da internet, que são da eleição de **2022**, 1º turno, no exterior (UF ZZ): Wellington, mun. 30805, e Nagóia, mun. 30198.

| Item | Resultado |
|---|---|
| QR lido | 5 de 6 boletins visíveis. A foto 1 (webp, de longe) não leu; a foto 2, ampliada 2x, leu os 4 |
| Cadeia de hash SHA-512 | ✅ confere nos 5 |
| Assinatura Ed25519 | ⏳ falta a chave pública oficial `ozzqrcode.pub` do TSE (site devolve 403 para robôs) |
| Votos extraídos | ✅ por candidato, brancos, nulos, total, urna, seção |

**Regra do hash (formato 1.5):** `HASH = SHA-512(dados)`, onde `dados` é o texto entre o cabeçalho (`QRBU VRQR VRCH`) e ` HASH:`.
**Assinatura:** Ed25519 sobre os bytes do HASH, com a chave `o<uf>qrcode.pub` (oficial) ou `s<uf>` (simulado).
**Formato de 2026 (6.0):** muda. A chave fica no certificado da urna (QRCE) e a curva é E-521 ou P-521. **É preciso um BU real de 2026 para testar.**

**Lições:**
- A foto precisa ser de perto, com o QR ocupando boa parte da imagem. Ampliar no servidor ajuda.
- Hash não é prova de autenticidade (qualquer pessoa recalcula). Só a assinatura prova.

Arquivos: `prototipo/ler_bu.py`, `prototipo/saida-teste.txt`. Base: repositório `fabricioluna/apuracaojuntos` (`src/bu/hash.ts`, `signature.ts`).
