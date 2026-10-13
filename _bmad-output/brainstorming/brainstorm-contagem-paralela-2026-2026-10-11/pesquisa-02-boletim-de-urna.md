# Pesquisa 02: Boletim de Urna (BU)

Data: 2026-10-11. Legenda: **[confirmado]** fonte oficial ou dado baixado e conferido; **[secundário]** imprensa ou repositório de terceiros; **[incerto]** não confirmado.

## TL;DR

- **Leia o QR Code, não a foto.** O BU traz QR Codes com todos os votos em texto `CHAVE:VALOR`. São várias partes (`QRBU:i:n`) ligadas por uma cadeia de hashes SHA-512, e a última leva a assinatura (`ASSI`). A foto entra como prova e como plano B (OCR ou digitação).
- **Formato em 2026:** é a versão `VRQR:6.0`, assinada com a chave da própria urna. O certificado da urna também vai impresso, em QR Codes `QRCE`. Até 2024 a versão era `1.5`, com Ed25519 e chave pública por UF. **[secundário]** O manual oficial de 2026 existe, mas o servidor do TSE bloqueou o download (403), então não consegui confirmar.
- **Base legal:** a urna imprime 5 vias obrigatórias. Uma vai afixada na seção e as outras vão para os fiscais e para a Junta.
- **Números de 2026 (1º turno, 4/10):** 517.179 seções em 95.570 locais de votação, 2.641 zonas e 158.745.463 eleitores. São 499.248 seções principais (com urna e BU próprios) e 17.931 agregadas. No exterior (UF `ZZ`) são 2.715 seções em 458 locais, com 918.876 eleitores. **[confirmado, CSV do TSE]**
- **Dados abertos:** o TSE publica o BU de cada seção em CSV (`bweb_*`). Também publica os arquivos brutos da urna (BU, imagem do BU, log, RDV e assinaturas). Os de 2026 saíram em 06/10, cerca de 2 dias após a eleição. Isso permite comparar com a contagem cidadã seção a seção.
- **Identificação da seção:** o dataset "Eleitorado por local de votação 2026" traz endereço, latitude/longitude e as agregações de cada seção.

---

## 1. Conteúdo do BU impresso

Campos documentados **[secundário: roteiro TRE-SP 2016; formato atual conferido pelo CSV de 2026]**:
- Data da eleição, UF, município, zona e seção. Quando houver, também as seções agregadas.
- Horários de abertura e de encerramento, e data/hora de emissão do BU.
- Identificação da urna:
  - número de série (`IDUE`);
  - código de identificação da carga, a "correspondência" (`IDCA`, até 24 dígitos);
  - identificação do flashcard e data da carga.
- Eleitores aptos, comparecimento e faltosos. Também os eleitores habilitados por ano de nascimento (biometria sem habilitação).
- Votos por cargo:
  - votos por candidato (nominais);
  - votos de legenda por partido, nos cargos proporcionais;
  - brancos, nulos e total do cargo.
- QR Codes com os mesmos dados, mais o hash e a assinatura digital.

**Formato físico:** papel térmico em bobina da impressora da urna. O comprimento varia com o número de cargos e candidatos. **[incerto]** Não achei a largura oficial da bobina. Em eleição geral (6 cargos), o BU é longo e traz vários QR Codes.

Não existe um campo "hash" impresso legível fora do QR. O hash e a assinatura ficam dentro do QR. **[secundário]**

## 2. QR Code do BU

**Especificação oficial:** "QR Code no Boletim de Urna: Manual para Criação de Aplicativo de Leitura". A edição de 2026 tem 36 páginas. Dúvidas sobre o manual vão para `qrcodenobu@tse.jus.br`. As edições de 2016 e 2018 traziam um anexo de verificação de assinatura, a lista de SHA-512 das chaves públicas e BUs de exemplo.

**Formato (consolidado de repositórios que implementam o manual) [secundário]:**
- O texto é ASCII com pares `CHAVE:VALOR` separados por espaço. Cada QR comporta no máximo cerca de 1.100 caracteres; o código da urna decompilado mostra `tamanhoMaximo = 1100`. **[incerto]**
- **Cabeçalho de cada QR:** `QRBU:i:n VRQR:<versão>`. Na versão 1.5 vem também `VRCH:<versão da chave>`.
- **Campos de identificação:**
  - `ORIG`;
  - `FASE`: O = oficial, S = simulado, T = treinamento;
  - `PROC`, `PLEI`, `DTPL`, `TURN`;
  - `UNFE`, `MUNI`, `ZONA`, `SECA`;
  - `AGRE`: seções agregadas, separadas por `.`;
  - `IDUE`, `IDCA`, `VERS`.
- **Comparecimento:** `APTO`, `COMP`, `FALT`.
- **Votos de cada eleição (`IDEL`):**
  - Cada cargo abre com `CARG:<cód> TIPO:<0 maj | 1 prop> VERC:...`.
  - Seguem os pares `<número do candidato>:<votos>`. Nos cargos proporcionais, os candidatos ficam agrupados por partido (`PART`, `LEGP`, `TOTP`).
  - O cargo fecha com `APTA`, `NOMI`, `LEGC`, `BRAN`, `NULO`, `TOTC`.
  - **Só aparecem candidatos com voto.** Candidato ausente tem 0.
- **Segurança, ao fim de cada QR:** `HASH:<SHA-512 em 128 hex>`. Só o último QR traz `ASSI:<hex>`.

**Cadeia de hashes [secundário]:**
- `hash1 = SHA512(dados1)`
- `hashN = SHA512(dados1 + " HASH:" + hash1 + " " + dados2 + … + " " + dadosN)`

Ou seja, o hash de cada QR cobre todos os anteriores, e a assinatura cobre os bytes do último hash.

**Assinatura:**
- **v1.5 (2018–2024):** Ed25519 com chave pública por UF e fase, em arquivos `o<uf>qrcode.pub` / `s<uf>qrcode.pub`. A autenticidade da chave se confere pela lista de SHA-512 publicada pelo TSE. **[secundário, coerente com o manual 2018]**
- **v6.0 (2026):** a assinatura é feita pela chave da própria urna, via PKCS#11. O certificado da urna sai impresso em QR Codes à parte, `QRCE:i:n` com `IDUE`, `MDUE` e `CERT` em hex. Um repositório diz que o algoritmo é EdDSA E-521. **[incerto]** É preciso confirmar no manual de 2026. Fato oficial: desde 2022, cada urna assina com chave privada própria e tem certificado digital próprio.
- **Para validar:** remontar as partes em ordem, recalcular a cadeia de hashes e verificar `ASSI` sobre o último hash. Na v6.0, a verificação usa o certificado `QRCE`, que deve ser da mesma `IDUE`; conferir também a cadeia do certificado até a AC da Justiça Eleitoral. **[incerto]** A cadeia de certificação não foi confirmada.

**App oficial:** o "Boletim na Mão" lê o QR offline e guarda o BU no aparelho. Em 2026 ele foi incorporado ao e-Título (menu "mais opções") e permite compartilhar vários BUs. **[secundário]**

**Projetos open source (GitHub) [secundário, sem auditoria]:**

| Repositório | O que faz |
|---|---|
| [fabricioluna/apuracaojuntos](https://github.com/fabricioluna/apuracaojuntos) | TS. Interpreta as versões 1.5 e 6.0, confere a cadeia SHA-512 e verifica Ed25519 (v1.5). Lê `QRCE`. Na v6.0 ainda **não** verifica a assinatura. Melhor referência encontrada. |
| [lucas-zimerman/urna-validador](https://github.com/lucas-zimerman/urna-validador) | JS, parser simples (`src/lib/qrbu.js`) focado em Presidente. |
| [lucas-daniel-sm/verificador_boletim_urna](https://github.com/lucas-daniel-sm/verificador_boletim_urna) | App Flutter mais backend Kotlin para contagem. O próprio autor diz que não está finalizado. |
| [josejacobpn-png/Apuracao2026](https://github.com/josejacobpn-png/Apuracao2026), [C5Web/votoaudit](https://github.com/C5Web/votoaudit) | Leitores de QR de BU para 2026. Não avaliados. |
| [igoroalonge/urna-vota-decompiled](https://github.com/igoroalonge/urna-vota-decompiled) | Decompilação não oficial do software da urna, com o gerador do QR (`cgeradorbuqrcode`). Serve só como pista. |

O TSE publicou, para 2022, a especificação ASN.1 dos arquivos de BU, RDV e assinatura, com scripts Python. Isso vale para os **arquivos** da mídia, não para o QR.

## 3. Regras legais

- **Código Eleitoral, art. 179 [confirmado, texto legal]:** o boletim segue o modelo do TSE. O § 3º manda afixar imediatamente um exemplar "em local que possa ser copiado por qualquer pessoa"; o texto original fala na sede da Junta. O § 4º manda entregar cópia autenticada a cada partido, por meio do delegado ou fiscal, mediante recibo.
- **Código Eleitoral, art. 313:** é crime deixar de expedir o BU imediatamente após o encerramento.
- **Prática atual [secundário: TSE e TRE]:**
  - A urna imprime **5 vias obrigatórias**. Uma é **afixada em local visível da seção** e outra segue com a ata para a Junta.
  - As demais vias ficam com os fiscais e delegados de partido, federação e coligação presentes. Eles podem pedir vias extras; resoluções antigas falavam em até 10.
- **Resolução vigente:** Res.-TSE 23.736/2024 ("atos gerais do processo eleitoral"). Uma fonte secundária cita o art. 176 para o conteúdo do BU. **[incerto]** Não consegui abrir o texto (403), então o número exato dos artigos sobre afixação e vias está pendente.
- **Partidos:** os arquivos da totalização ficam 3 dias à disposição para exame, com mais 2 dias para reclamação (aviso do TRE-PR, 2026).

## 4. Números (Eleições 2026, 1º turno em 04/10/2026)

Os números abaixo foram calculados por mim a partir de `eleitorado_local_votacao_2026_BRASIL.csv`, gerado em 11/10/2026. **[confirmado]**

| Item | Valor |
|---|---|
| Seções (1º turno) | 517.179. A imprensa cita 517.206; a diferença é pequena. |
| Seções principais, que imprimem BU | 499.248 |
| Seções agregadas, cujos votos vão no BU da principal | 17.931 |
| Locais de votação | 95.570 |
| Zonas | 2.641 |
| Municípios, incluindo cidades no exterior | 5.757 (5.571 no Brasil + 186 no exterior) |
| Eleitores aptos | 158.745.463 |
| Exterior (UF `ZZ`) | 2.715 seções, 458 locais, 918.876 eleitores |
| Urnas disponíveis | 563.910, incluindo contingência **[secundário]** |
| Locais sem coordenada | cerca de 1.217 |

Também há 3.145 seções em locais temporários, 245 em presídios (preso provisório) e 155 de voto em trânsito.

## 5. Dados abertos do TSE

- **Portal Resultados** (resultados.tse.jus.br) → "Arquivos de Urna": mostra por seção o BU, o RDV e o log da urna. Os dados entram progressivamente na noite da apuração. **[secundário]**
- **dadosabertos.tse.jus.br**, conferido pela API CKAN: **[confirmado]**
  - **`resultados-2026-boletim-de-urna`:** CSV `bweb_1t_<UF>_051020261403.zip` por UF, com um `.sha512` por arquivo, publicado em **06/10/2026**. Tem uma linha por seção × cargo × votável. Colunas principais:
    - identificação: `NR_ZONA`, `NR_SECAO`, `NR_LOCAL_VOTACAO`;
    - totais: `QT_APTOS`, `QT_COMPARECIMENTO`, `NR_VOTAVEL`, `QT_VOTOS`;
    - urna: `NR_URNA_EFETIVADA`, `CD_CARGA_1_URNA_EFETIVADA`;
    - agregação e horários: `DS_SECOES_AGREGADAS`, `DT_ABERTURA`, `DT_ENCERRAMENTO`, `DT_EMISSAO_BU`, `DT_BU_RECEBIDO`.
  - **`resultados-2026-arquivos-transmitidos-para-totalizacao`:** `bu_imgbu_logjez_rdv_vscmr_2026_1t_<UF>.zip`, com BU binário, imagem do BU, log, RDV e assinaturas. Também publicado em 06/10. O arquivo do AC tem cerca de 373 MB.
  - Também existe o "Relatório de Totalização 2026" por UF.
- **Prazo:** cerca de 2 dias após o 1º turno para os arquivos em lote. Não achei norma que fixe esse prazo. **[incerto]**
- **Comparação seção a seção:**
  - A chave é UF + município + zona + seção. Isso vale tanto para o QR (`UNFE/MUNI/ZONA/SECA`) quanto para o CSV.
  - Também dá para cruzar `IDUE` e `IDCA` do QR com `NR_URNA_EFETIVADA` e `CD_CARGA_*`, o que detecta uma urna substituída.
  - O código de município é o código TSE de 5 dígitos, **não** o código IBGE.

## 6. Tabela de zonas, seções e locais com endereço e coordenadas

- **Dataset:** "Eleitorado por local de votação - 2026", em `cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip`. São 176 MB zipados, com um CSV por UF, um BRASIL e um leiame. A codificação é Latin-1 com separador `;`. **[confirmado]**
- **Colunas úteis:**
  - identificação: `SG_UF`, `CD_MUNICIPIO`, `NM_MUNICIPIO`, `NR_ZONA`, `NR_SECAO`, `NR_TURNO`;
  - agregação: `DS_TIPO_SECAO_AGREGADA` (Principal/Agregada), `NR_SECAO_PRINCIPAL`;
  - local: `NR_LOCAL_VOTACAO`, `NM_LOCAL_VOTACAO`, `DS_TIPO_LOCAL`, `DS_ENDERECO`, `NM_BAIRRO`, `NR_CEP`;
  - coordenadas: **`NR_LATITUDE`, `NR_LONGITUDE`**, com vírgula decimal;
  - situação: `DS_SITU_SECAO`;
  - eleitorado: `QT_ELEITOR_SECAO`.
- Ele é atualizado também depois da eleição (arquivo gerado em 11/10/2026) e já inclui as linhas do 2º turno.
- O perfil do eleitorado por seção também está disponível, em `perfil_eleitor_secao_2026_<UF>.zip`.

---

## Implicações para o app

1. **O QR é a fonte primária e a foto é a evidência.**
   - Decodificar todas as partes `QRBU:i:n` (e as `QRCE`), validar a cadeia SHA-512 e marcar o BU como "íntegro".
   - A assinatura v6.0 só deve ser marcada como "verificada" depois de implementada conforme o manual de 2026. Até lá, o status fica "hash ok / assinatura pendente".
   - OCR e digitação ficam como fallback, com peso de confiança menor.
2. **A chave de deduplicação é UF + MUNI + ZONA + SECA + TURN.** O hash final do BU serve como impressão digital: duas fotos do mesmo BU dão o mesmo hash, e hashes diferentes para a mesma seção indicam um conflito a investigar.
3. **Seção agregada não tem BU próprio.** Use `AGRE` e o dataset de locais para marcar como "coberta" a seção agregada quando chegar o BU da principal. A meta de cobertura é 499.248 BUs (a contar no 2º turno), e não 517 mil.
4. **Pré-carregar o dataset de locais.** Ele permite ao app sugerir local e seções por GPS, mostrar o mapa de cobertura e validar se a seção lida existe. Cerca de 1,2 mil locais vão precisar de geocodificação. Use o código de município TSE, não o IBGE.
5. **Conferência oficial automática.** Após cerca de 2 dias, baixe os `bweb_*` e os `.sha512` e compare voto a voto por seção. Na noite da eleição, compare com o Portal Resultados. Confira também `IDUE`/`IDCA` contra a urna efetivada.

## Pendências

- Baixar e ler o manual QR 2026 (403 aqui). Tentar navegador ou e-mail `qrcodenobu@tse.jus.br`. É preciso confirmar o algoritmo e a cadeia de certificação da v6.0.
- Confirmar os artigos da Res.-TSE 23.736/2024 sobre vias e afixação.
- Confirmar o tamanho e a largura do papel do BU.

## Fontes

- Manual QR Code no BU 2026 (PDF): https://www.tse.jus.br/eleicoes/eleicoes-2026-content/arquivos/manual-do-qr-code-no-boletim-de-urna/@@display-file/file/manual-do-qr-code-no-boletim-de-urna.pdf
- Manual QR Code no BU 2024: https://www.tse.jus.br/eleicoes/eleicoes-2024-content/arquivos/qr-code-no-boletim-de-urna
- Manual 2018 (página com anexos, chaves e hashes): https://www.tse.jus.br/eleicoes/eleicoes-2018/qr-code-no-boletim-de-urna-manual-para-criacao-de-aplicativos-de-leitura
- Manual 2016: https://www.tse.jus.br/eleicoes/eleicoes-anteriores/eleicoes-2016/votacao-e-resultados/qr-code-no-boletim-de-urna-manual-para-a-criacao-de-aplicativos-de-leitura
- Documentação técnica da urna 2022 (ASN.1 de BU/RDV/assinatura): https://www.tse.jus.br/eleicoes/eleicoes-2022/documentacao-tecnica-do-software-da-urna-eletronica
- Código Eleitoral, art. 179: https://www.legjur.com/legislacao/art/lei_00047371965-179
- TSE Temas Selecionados (BU: expedição, afixação, distribuição): https://temasselecionados.tse.jus.br/temas-selecionados/apuracao-de-votos-e-eleicoes-extraordinarias/recontagem-de-votos/cabimento/boletim-de-urna-2013-expedicao-afixacao-e-distribuicao
- TSE, BU traz resultado impresso da seção (2021): https://www.tse.jus.br/imprensa/noticias-tse/2021/Junho/boletim-de-urna-traz-o-resultado-impresso-da-secao-de-votacao
- Roteiro de totalização TRE-SP 2016: https://www.tre-sp.jus.br/eleicoes/eleicoes-anteriores/eleicoes-2016/arquivos/tre-sp-roteiro-de-totalizacao-dos-votos
- Números 2026 (Agência Brasil via Brasil 61): https://brasil61.com/n/eleicoes-2026-158-7-milhoes-de-brasileiros-estao-aptos-a-votar-neste-domingo-bras2617212
- Boletim na Mão no e-Título 2026: https://portaldeprefeitura.com.br/bastidores-da-politica/eleicoes-2026-boletim-de-urna-permite-conferir-totalizacao-dos-votos/633460/
- TSE, como acompanhar resultados 2026: https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/terminada-a-votacao-saiba-como-acompanhar-os-resultados-das-eleicoes
- Como ver o BU por seção: https://investnews.com.br/economia/como-ver-resultado-da-secao-eleitoral/
- TRE-PR, totalização 1º turno 2026 (prazo de 3+2 dias): https://www.tre-pr.jus.br/comunicacao/noticias/2026/Outubro/eleicoes-2026-resultados-da-totalizacao-do-1o-turno-no-parana
- Dados abertos, BU 2026: https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna
- Dados abertos, arquivos transmitidos 2026: https://dadosabertos.tse.jus.br/dataset/resultados-2026-arquivos-transmitidos-para-totalizacao
- Dados abertos, Eleitorado 2026 (locais de votação): https://dadosabertos.tse.jus.br/dataset/eleitorado-2026
- CSV de locais 2026: https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip
- Repositórios GitHub: https://github.com/fabricioluna/apuracaojuntos · https://github.com/lucas-zimerman/urna-validador · https://github.com/lucas-daniel-sm/verificador_boletim_urna · https://github.com/igoroalonge/urna-vota-decompiled
- TabNews (discussão sobre leitura do QR do BU): https://www.tabnews.com.br/ThalissonM/0a065507-73fc-4986-ac49-d62f00c42b69
