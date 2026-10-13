# Pesquisa 03 — Precedentes e aspectos legais da contagem paralela por fotos de BU

Data: 2026-10-11. Legenda: **[confirmado]** = fonte encontrada; **[incerto]** = não confirmado no texto oficial / fonte secundária; **[inferência]** = raciocínio meu, sem fonte.

## TL;DR

- Já foi feito e funciona como **conferência**, não como apuração: KawalPemilu (Indonésia) digitalizou ~100% das atas em ~6 dias com voluntários; Venezuela 2024 provou que atas fotografadas viram prova pública quando o órgão oficial esconde dados.
- No Brasil, todas as conferências por amostra de BU em 2022 (TCU, Forças Armadas) **não acharam divergência**. Risco real não é achar fraude: é virar munição de desinformação (caso PL/IVL, multa de R$ 22,9 mi).
- Legal: conferir e publicar BU é legal; o BU é documento público e o próprio TSE publica os BUs no dia da eleição. Proibido: divulgar "fatos sabidamente inverídicos" sobre integridade da apuração (Res. TSE 23.610 + 23.714/2022) e crime do art. 323 do Código Eleitoral. Não é "pesquisa" nem "boca de urna" (não pergunta voto ao eleitor). **[inferência; confirmar com advogado eleitoral]**
- Posicionamento seguro: "espelho auditável dos BUs, que confere a totalização do TSE", nunca "resultado alternativo". Divergência = "a verificar", com foto + hash + QR, antes de qualquer alarme.
- Maior ameaça operacional: **envios falsos/spam em massa** (KawalPemilu 2019 recebeu centenas de fotos repetidas, C1 forjados, fotos não-C1). Solução: QR code do BU (assinado) + consenso de múltiplos envios + moderadores.

## Precedentes

| País/ano | Modelo | Resultado | Lição |
|---|---|---|---|
| Indonésia 2014 — KawalPemilu | 3 fundadores no exterior; ~700 voluntários digitaram scans dos formulários C1 que a KPU publicou (~470 mil TPS). Sistema aberto em 13/jul. | 97% dos dados em 6 dias; terminou quase junto com o anúncio oficial (22/jul). Sem vínculo com KPU ou partido. **[confirmado]** | Se o órgão oficial publica as imagens, o crowd só precisa digitar e conferir — escala rápido. Neutralidade declarada foi central. |
| Indonésia 2019 — KawalPemilu | Voluntários fotografavam C1 plano no TPS e subiam em upload.kawalpemilu.org, login via Facebook; parceria com agência estatal ANTARA e com Banser (ala jovem do NU). 809,5 mil TPS-alvo. | Ataque por envios falsos: C1 sem holograma, votos acima do eleitorado, até ~200 fotos iguais do mesmo TPS, fotos não-C1 em massa → atrasou a verificação. **[confirmado]** Resultado final vs KPU: **[incerto, não achei]** | Identidade do voluntário + dedup + regras de sanidade (votos ≤ eleitores) + moderação. Verificação em 2 etapas com 3 moderadores por TPS foi descrita para app parceiro (PesanKita/XecureIT) — **[incerto se era do KawalPemilu]**. |
| Venezuela 2024 — resultadosconvzla.com | Testemunhas da oposição fotografaram/guardaram as atas impressas (com QR e hash) e publicaram em site. | ~81,7% das mesas (24.532) publicadas (MOE Colômbia). CNE nunca publicou atas por mesa. Painel da ONU: gestão do CNE sem transparência mínima; Carter Center chamou as atas de confiáveis. Repressão: ~2.400 presos. **[confirmado]** | Ata com QR/hash = prova verificável por terceiros. Funciona porque o oficial é opaco — no Brasil o TSE publica os BUs, então o papel é conferência, não substituição. |
| Nigéria 2023 — IReV + Yiaga PVT | INEC publica fotos das atas por seção (IReV); Yiaga Africa fez PVT com 3.014 observadores em 1.507 seções amostradas. | Upload oficial atrasou (25.503 de 176.848 na manhã seguinte; 73% depois); Yiaga apontou resultados de Imo e Rivers inconsistentes com sua observação. **[confirmado; detalhes de Imo/Rivers incertos]** | Portal de imagens não garante confiança se atrasa. Amostra estatística (PVT) dá resposta rápida mesmo sem 100%. |
| Quênia 2013 — Uchaguzi (Ushahidi) | Crowdsourcing de incidentes (SMS/web), não de votos; fontes "confiáveis" x "não verificadas". | ~2.300 SMS deram retrato coerente com Carter Center/ELOG; crowd fala pouco de formalidades do processo. **[confirmado — tese UiB]** | Crowd é bom em tempo/local; precisa perguntas estruturadas. |
| Quênia 2022 — Form 34A | IEBC publicou formulários 34A por seção num portal; mídia e campanhas tabularam. | TVs mostraram totais diferentes (Media Council interveio); Nation achou erros de digitação; Suprema Corte: sem diferença relevante e **logs de "prova" de fraude eram forjados**. **[confirmado]** | Tabulações paralelas divergem entre si; contestação organizada pode usar evidência falsa — guarde trilha de auditoria imutável. |
| México — PREP (oficial) | Foto da acta na casilla via app "PREP Casilla"; captura dupla por pessoas distintas; publica imagem. Conteo rápido estatístico (>17 mil casillas em 2024). | Cidadão confere sua casilla na imagem publicada; auditorias externas (ex.: UAM). **[confirmado]** Iniciativas cidadãs paralelas específicas: **[não encontrei]** | Padrão-ouro de UX: foto na fonte + dupla digitação + imagem pública. |
| Ucrânia — OPORA (2014/2019) e 2004 | PVT por amostra (~1.500 seções, erro ≤2,9%). 2004: exit polls x oficial → Revolução Laranja, nova eleição. | 2014: PVT acertou o partido vencedor quando todos os exit polls erraram. **[confirmado]** | Amostra bem feita > volume desorganizado. |
| Rússia 2011–2024 — Golos/Shpilkin | Análise estatística dos dados oficiais + bot Telegram (@uik_protocol_bot) para observadores enviarem protocolos. | Estimativas de milhões de votos irregulares; Golos e Shpilkin perseguidos ("agente estrangeiro"). **[confirmado]** | Útil em regime opaco; método contestado. Mostra o risco político para quem audita. |
| NDI — PVT/PRVT (método) | Observadores treinados em amostra probabilística de seções; projeção com margem de erro; também observa o processo. | Referência internacional (Gana, Quênia, Nigéria etc.). **[confirmado]** | Um projeto "100% crowd" é complementar a PVT; publicar margem de erro e cobertura. |
| Brasil 2014 — Você Fiscal (Diego Aranha) | App Android/e-mail para foto de BU; crowdfunding (~R$ 65 mil). | ~10,7 mil BUs recebidos de 400 mil+ urnas no 1º turno; Aranha reconheceu limites (não detecta fraude no software da urna nem do mesário). Balanço final de divergências: **[não encontrei]**. Vídeo de 2014 reciclado como desinformação em 2022. **[confirmado]** | Cobertura baixa limita conclusões. Conteúdo antigo é reaproveitado fora de contexto — datar tudo. |
| Brasil 2022 — oficial/institucional | TSE: app Boletim na Mão (lê QR do BU, valida autenticidade) e BUs publicados online durante a apuração. TCU: 4.161 BUs (1º turno) e 604 (2º) → zero divergência. Forças Armadas: amostra sem inconformidade. **[confirmado]** | Base oficial já permite conferência cidadã. |
| Brasil 2022 — PL/Instituto Voto Legal | "Auditoria" pediu anular votos de urnas pré-2020 só no 2º turno. | TSE rejeitou; multa de R$ 22,9 mi por litigância de má-fé; inquérito contra presidente do PL e engenheiro do IVL. Live de Cerimedo (urnas "anômalas") removida, contas suspensas. **[confirmado]** | Conclusão sem evidência por seção = punição. Nunca extrapolar de anomalia estatística para "fraude". |
| Brasil 2018/2022 — BUs falsos | Montagens de BU (ex.: Haddad 9.909 votos; "candidato com zero votos") circularam. **[confirmado]** | Exigir QR válido; mostrar foto original ao lado do dado. |

Apps de partidos para coleta de BU em 2022: **[não encontrei fonte específica]**. Checagens de imprensa com fotos de BU em 2022: **[não encontrei]**; houve cobertura do TCU checando 540 seções em tempo real.

### Lições consolidadas

1. **Fraude/envio falso**: validar QR do BU (assinatura digital do TSE) como prova primária; foto é só apoio. Regras de sanidade (votos ≤ aptos, soma confere). Dedup por seção; consenso de N envios independentes. Rate limit e identidade mínima do envio.
2. **Contestação organizada**: trilha imutável (hash da imagem + timestamp + log público); KE 2022 mostra que "provas" forjadas aparecem.
3. **Desinformação**: publicar divergência só como "pendente de verificação" com a imagem; datar e carimbar tudo; nunca usar linguagem de fraude.
4. **Cobertura**: declarar % de seções e viés (crowd cobre cidades mais). Se quiser estimativa, usar amostra estatística (estilo PVT), não total parcial.

## Legal BR

> Não sou advogado; validar com especialista em direito eleitoral antes de lançar. Resoluções do TSE mudam a cada eleição; para 2026 vale o pacote aprovado em mar/2026 (ex.: Res. 23.755/2026 alterou a 23.610). Não consegui abrir o texto compilado no site do TSE (403).

| Tema | Regra | Aplicação à contagem paralela |
|---|---|---|
| BU é público | Lei 9.504/97, art. 68: presidente da mesa é obrigado a entregar cópia do BU aos partidos que pedirem até 1h após emissão; negar é crime. BU é afixado na seção; TSE publica BUs online no dia. **[confirmado]** | Fotografar e republicar BU é usar documento público. **[inferência]** |
| Pesquisa eleitoral (art. 33) | Registro 5 dias antes; multa por divulgar sem registro. **[confirmado, valores podem estar desatualizados]** | Soma de BUs **não é pesquisa** (não entrevista eleitor). **[inferência]** Evitar qualquer projeção estatística que possa ser lida como "pesquisa" sem registro — **[incerto]**. |
| Boca de urna (art. 39 §5º) | Crime: arregimentar eleitor / propaganda no dia. Pesquisa de boca de urna só pode ser divulgada após fim da votação (presidente: após fechar no país todo). **[confirmado]** | BU só existe após 17h (Brasília), então não há divulgação antes do encerramento. Não fazer chamada partidária no dia. |
| Desinformação sobre o processo | Res. 23.714/2022 e Res. 23.610 (arts. 9-A e seguintes, atualizados pela 23.732/2024): veda divulgar fatos **sabidamente inverídicos ou gravemente descontextualizados** que atinjam a integridade da votação, apuração e totalização; remoção imediata de URL e multa (R$ 100–150 mil/hora para plataformas em 2022). **[confirmado em fontes secundárias; numeração exata do artigo vigente incerta]** | Divergência mal checada publicada como "fraude" cabe aqui. Divergência real e documentada, não. |
| Crime de fato inverídico | Código Eleitoral art. 323 (redação Lei 14.192/2021): divulgar fatos sabidamente inverídicos sobre partidos/candidatos capazes de influenciar o eleitorado; detenção de 2 meses a 1 ano ou multa; aumento se for pela internet/em tempo real. **[confirmado]** | Risco se o produto atribuir vantagem falsa a candidato. |
| IA (2026) | Pacote 2026 restringe conteúdo gerado/alterado por IA de 72h antes até 24h após a votação. **[incerto — redação exata não verificada]** | Não usar IA para gerar/“melhorar” imagens; OCR sem alterar a foto original está fora disso **[inferência]**. |
| Litigância de má-fé | Caso PL 2022: multa de R$ 22,9 mi. **[confirmado]** | Não levar "achados" ao TSE sem prova por seção. |

### LGPD (inferência a partir da Lei 13.709/2018; sem caso específico encontrado)

- **BU em si**: dados agregados por seção, sem dado pessoal de eleitor. Pode trazer nome/assinatura de mesários e fiscais → dado pessoal tornado público por obrigação legal (LGPD art. 7º, §§3º-4º), usar só para a finalidade de conferência. Considerar borrar assinaturas na imagem pública.
- **Foto**: metadados EXIF (GPS, modelo do aparelho) e rostos/pessoas ao fundo → remover EXIF no upload; recortar só o BU; não publicar imagem bruta se houver pessoas.
- **Envio "anônimo"**: IP, device ID, telefone são dados pessoais. Minimizar, prazo de retenção curto, aviso de privacidade.
- **Cadastro de auditores**: base legal = consentimento ou legítimo interesse; finalidade explícita; não cruzar com filiação partidária (opinião política é **dado sensível**, art. 5º II e art. 11 — exige consentimento específico). Não exibir nome de auditor junto a envio.
- Exceção jornalística (art. 4º II) pode cobrir parte da publicação se for veículo de imprensa **[incerto; depende de quem opera]**.

## Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Ser enquadrado como desinformação sobre a apuração | Linguagem: "conferência dos BUs publicados"; mostrar sempre % de cobertura; divergência = "pendente", com foto + QR + link para o BU oficial no TSE; canal para reportar ao TSE, não à mídia. |
| Envios falsos/flood (KawalPemilu 2019) | QR obrigatório e validado; dedup por seção + hash da imagem; regras de sanidade; rate limit; moderação com consenso. |
| BU montado viralizando com nossa marca | Toda imagem publicada com marca d'água + hash; página de verificação pública "este BU é autêntico?". |
| Contestação com provas forjadas (Quênia 2022) | Log append-only público (hash encadeado); export aberto dos dados. |
| Parecer concorrente do TSE / captura partidária | Governança neutra declarada (KawalPemilu); sem logos de partido; metodologia e código abertos; conselho com academia/imprensa. |
| Total parcial lido como "resultado" | Não exibir "vencedor"; exibir "X% dos BUs conferidos: Y batem, Z pendentes". Se projetar, só com amostra estatística e margem de erro (método PVT/NDI). |
| Reciclagem de conteúdo antigo (vídeo Você Fiscal) | Datar e versionar tudo; página "o que este projeto NÃO afirma". |
| LGPD | EXIF strip, borrar assinaturas/rostos, minimização, retenção curta, DPO/contato. |
| Remoção de conteúdo/multa | Revisão jurídica prévia; plano de resposta a notificação; não depender de uma só plataforma. |

## Fontes

Precedentes
- KawalPemilu 2014 (Open Data's Impact): https://odimpact.org/files/case-study-indonesia.pdf
- KawalPemilu 2014 (Binus): https://binus.ac.id/2014/09/inilah-pandawa-di-balik-kawal-pemilu/
- KawalPemilu 2019 (Jakarta Post): https://www.thejakartapost.com/news/2019/04/11/kawalpemilu-invites-campaign-teams-to-use-platform-to-safeguard-vote-count
- KawalPemilu 2019 relawan (Kontan): https://nasional.kontan.co.id/news/kawalpemilu-ajak-masyarakat-jadi-relawan-jaga-suara-di-pemilu-2019
- C1 falsos (Antara): https://www.antaranews.com/berita/838051/kawal-pemilu-keluhkan-banyak-data-c1-palsu
- Antara x KawalPemilu: https://m.antaranews.com/amp/berita/837515/antara-kirim-data-c1-plano-ke-kawalpemilu
- Tirto (contexto 2019): https://tirto.id/kawalpemilu-kawalpilpres-yang-hadir-di-tengah-delegitimasi-kpu-dmQ9
- Venezuela – MOE Colômbia: https://moe.org.co/wp-content/uploads/2024/08/20240803-Pasos-y-hallazgos-resultados-Venezuela-2024.pdf
- Venezuela – Xataka (verificação atas): https://www.xataka.com/magnet/hay-miles-actas-elecciones-venezuela-red-que-dan-otro-resultado-hay-forma-verificar-datos
- Venezuela – UE sobre painel ONU: https://www.eeas.europa.eu/eeas/venezuela-statement-high-representative-publication-interim-report-un-panel-experts-presidential_en
- Venezuela – Carter Center na OEA: https://www.elpais.com.co/mundo/centro-carter-presento-ante-la-oea-actas-que-demostrarian-la-victoria-de-edmundo-gonzalez-en-venezuela-0217.html
- Venezuela – HRW: https://www.hrw.org/report/2025/04/30/punished-seeking-change/killings-enforced-disappearances-and-arbitrary-detention
- NDI PVT/PRVT: https://www.ndi.org/pvt e https://ndi.org/publications/process-and-results-verification-transparency-prvt-guide
- Nigéria – Yiaga: https://wilanglobal.org/resource/yiaga-africa-post-election-statement-on-the-2023-presidential-election/
- Nigéria – atraso IReV: https://businessday.ng/nigeriadecidesliveupdates/article/despite-apologies-inec-yet-to-upload-half-of-results/
- Quênia – Uchaguzi (tese UiB): https://bora.uib.no/handle/1956/10904
- Quênia 2022 – erros 34A: https://www.nation.africa/kenya/news/politics/sample-of-forms-34a-reveals-errors-in-presidential-tally-3925620
- Quênia 2022 – Suprema Corte: https://theeastafrican.co.ke/tea/news/east-africa/kenya-poll-petition-verdict-the-highlights-3937484
- Quênia 2022 – mídia divergente: https://www.kenyans.co.ke/news/78252-why-media-houses-have-different-presidential-results
- México – PREP: https://politica.expansion.mx/elecciones/2024/05/12/el-ine-realiza-primera-simulacion-del-prep-para-las-elecciones-del-2-de-junio
- México – conteo rápido: https://vanguardia.com.mx/noticias/ine-reafirma-que-conteos-rapidos-seran-a-partir-de-las-10-de-la-noche-FC2756601
- Ucrânia – OPORA PVT: https://oporaua.org/en/vybory/pvt_en-17148 e https://www.kyivpost.com/ukraine-politics/opora-election-watchdog-confirms-exit-polls-calls-vote-competitive.html
- Rússia – Shpilkin (RFE/RL): https://www.rferl.org/a/russia-putin-election-statistical-model-shpilkin-s-razor/32868789.html
- Rússia – Golos: https://golosinfo.org/en/articles/146798

Brasil
- Você Fiscal (Exame): https://exame.com/tecnologia/app-de-apuracao-independente-recebe-dados-de-11-mil-urnas
- Você Fiscal (Tecnoblog): https://tecnoblog.net/166776/plataforma-voce-fiscal-verificar-seguranca-urna-eletronica/
- Aos Fatos sobre vídeo reciclado: https://www.aosfatos.org/noticias/video-vulnerabilidades-urnas-2014-cita-problemas-ja-corrigidos/
- TSE – BU e Boletim na Mão: https://www.tse.jus.br/comunicacao/noticias/2022/Outubro/voce-ja-ouviu-falar-do-boletim-de-urna-mas-sabe-o-que-ele-e-tire-suas-duvidas
- TSE – BUs online 2º turno: https://www.tse.jus.br/comunicacao/noticias/2022/Outubro/boletins-de-urna-do-2o-turno-ja-estao-disponiveis-na-internet
- TSE libera BUs no dia para apurações paralelas: https://www.gazetasp.com.br/brasil/tse-ira-fornecer-boletins-de-urnas-ja-no-dia-da-eleicao-para-apuracoes/1109295
- TCU – painel/auditoria BUs: https://portal.tcu.gov.br/imprensa/noticias/tcu-lanca-painel-eletronico-para-divulgar-informacoes-de-auditoria-feita-nos-boletins-de-urna.htm
- Defesa – relatório 2022: https://www.poder360.com.br/governo/defesa-nao-ve-fraude-em-eleicao-mas-sugere-melhorias-ao-tse/
- TSE – multa PL: https://www.tse.jus.br/comunicacao/noticias/2022/Dezembro/tse-confirma-multa-de-r-22-9-milhoes-ao-pl-por-litigancia-de-ma-fe
- Live Cerimedo (Folha PE): https://www.folhape.com.br/politica/pgr-aliados-de-bolsonaro-divulgaram-live-com-fake-news-sobre-urnas/392831/
- BU falso Haddad (Comprova/Poder360): https://www.poder360.com.br/eleicoes/comprova-boletim-de-urna-que-mostra-haddad-com-9-909-votos-e-montagem/

Legal
- Lei 9.504/97: https://www.planalto.gov.br/ccivil_03/leis/l9504.htm
- Art. 68 / BU para partidos (TSE temas): https://temasselecionados.tse.jus.br/temas-selecionados/temas-diversos/parte-v-urna-eletronica/boletim-de-urna
- Boca de urna (TSE temas): https://temasselecionados.tse.jus.br/temas-selecionados/propaganda-eleitoral/propaganda-no-dia-da-eleicao
- Res. 23.714/2022: https://www.tse.jus.br/legislacao/compilada/res/2022/resolucao-no-23-714-de-20-de-outubro-de-2022
- Res. 23.610/2019 (compilada): https://www.tse.jus.br/legislacao/compilada/res/2019/resolucao-no-23-610-de-18-de-dezembro-de-2019
- Repositório TSE de decisões sobre desinformação: https://temasselecionados.tse.jus.br/temas-selecionados/repositorio-decisoes-sobre-enfrentamento-desinformacao-eleitoral
- Resoluções 2026 (Poder360): https://www.poder360.com.br/poder-eleicoes/tse-aprova-pacote-de-14-resolucoes-para-as-eleicoes-de-2026/
- IA 2026 (MPMG): https://www.mpmg.mp.br/portal/menu/comunicacao/campanhas/ia-nas-eleicoes.shtml
- Art. 323 CE (Dizer o Direito): https://www.dizerodireito.com.br/2021/08/o-novo-delito-de-violencia-politica.html
- LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
