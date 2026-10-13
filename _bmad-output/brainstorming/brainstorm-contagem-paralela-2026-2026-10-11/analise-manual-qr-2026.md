# Manual do QR Code no BU 2026: o que importa (2026-10-11)

Fonte: `tse/manual-qrcode-2026.pdf` (baixado pelo Alino; o TSE só aceita acesso do Brasil). Texto em `tse/manual-qrcode-2026.txt`.

| Item | Manual 2026 |
|---|---|
| Formato | `VRQR:6.0`; vários QRs `QRBU:n:N` com hash SHA-512 acumulado; `ASSI` só no último |
| Assinatura | Feita pelo hardware de segurança da própria urna |
| Algoritmo | Urnas 2020/2022: EdDSA curva **E-521** (SHAKE256). Urnas 2013/2015: **ECDSA P-521** (verificável com OpenSSL) |
| Chave pública | Vem no **certificado da urna**, impresso no próprio BU em QRs `QRCE:n:x` (`CERT`, em DER nas urnas antigas e PEM nas novas) |
| Código de exemplo | Python com `ecpy` (`EDDSA(shake_256, hash_len=132)`) e `asn1crypto` (p. 21–23) |
| Nomes de candidatos | JSON de complemento assinado: `qrcodenobu.tse.jus.br/json-bu/...` (chave `s99999br-av.js`) |
| Cadeia de confiança do certificado | ❌ **O manual não diz** quem emite o certificado da urna nem onde fica a raiz |

## Consequência

Sozinha, a assinatura prova apenas que "este BU foi assinado pela chave do certificado impresso nele". Um falsário poderia gerar uma chave, um certificado e um BU falsos, todos coerentes entre si.

**Como fechar essa brecha, sem depender da raiz do TSE:**
1. **Âncora cidadã:** cada certificado `IDUE → chave pública` recebido na noite da eleição vai para o log público com carimbo de tempo. Se várias capturas independentes da mesma urna trazem o mesmo certificado, ele é confiável.
2. **Âncora TSE:** depois, conferir esse certificado com os arquivos de urna que o TSE publica (`bu_imgbu_logjez_rdv_vscmr`). Certificado diferente para o mesmo `IDUE` é um alarme.
3. **Pedir ao TSE** (qrcodenobu@tse.jus.br) a AC raiz dos certificados das urnas.

## Limite do teste com dados do TSE
Os arquivos publicados pelo TSE servem para **testar o código** do verificador, mas **não detectam divergência**, porque vêm da mesma fonte que se quer auditar. A divergência só aparece com o BU fotografado na porta.

## Pendências
- Um BU real de 2026 (foto nítida com todos os QRBU e QRCE) para testar a verificação E-521.
- Confirmar se `ecpy` está disponível ou se é preciso usar a biblioteca do TSE.
