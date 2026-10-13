**Para:** qrcodenobu@tse.jus.br
**Assunto:** Verificação da assinatura do QR Code no BU (VRQR 6.0): cadeia de confiança dos certificados das urnas

Prezada equipe do TSE,

Sou desenvolvedor e estou criando um aplicativo de código aberto para que eleitores leiam o QR Code do Boletim de Urna afixado na seção e confiram se ele é idêntico ao BU publicado pelo TSE. A ideia é reforçar a transparência do processo, conforme o objetivo do próprio manual "QRCODE no Boletim de Urna: Manual para Criação de Aplicativo de Leitura" (Eleições 2026).

O manual de 2026 informa que:
- a assinatura (campo ASSI) é EdDSA, curva E-521, nas urnas UE2020/UE2022, e ECDSA P-521 nas urnas UE2013/UE2015;
- a chave pública está no certificado da urna, impresso nos QR Codes QRCE.

Para que um aplicativo de terceiros consiga confirmar que o certificado impresso pertence de fato a uma urna da Justiça Eleitoral, e não a uma chave gerada por quem quer falsificar um BU, peço, por gentileza, as seguintes informações:

1. **Cadeia de certificação:** qual Autoridade Certificadora emite os certificados das urnas, e onde obter o(s) certificado(s) raiz e intermediário(s) para validar a cadeia, com os respectivos hashes SHA-512 publicados oficialmente.
2. **Revogação:** existe lista de certificados revogados (LCR) ou outro mecanismo para as urnas substituídas ou de contingência?
3. **Correspondência urna × certificado:** é possível obter, por seção ou por código de identificação da urna (IDUE), o certificado ou a chave pública usada em cada urna? Por exemplo, a partir dos arquivos já publicados (bu.dat, vota.vsc).
4. **Biblioteca EdDSA E-521:** o manual menciona "a biblioteca fornecida pelo TSE" para verificar EdDSA. Onde ela está disponível, e sob qual licença?
5. **Especificação ASN.1 de 2026:** a especificação dos arquivos de BU, RDV e assinatura digital publicada para 2022 continua válida para 2026? Se não, onde obter a versão atual?
6. **Zerésima:** a zerésima ou o resumo da zerésima tem algum mecanismo de verificação digital (QR Code ou assinatura)? O registro de sua emissão consta do log da urna (log.jez)?

Como o 2º turno será em 25/10/2026, uma resposta breve, ainda que parcial, já seria de grande ajuda.

Agradeço a atenção e me coloco à disposição.

Atenciosamente,
[Nome completo]
[Cidade/UF]
[Telefone ou e-mail de contato]
[Link do repositório, quando publicado]
