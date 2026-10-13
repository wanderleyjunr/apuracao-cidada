# Pesquisa 04: arquitetura e segurança da contagem cidadã de BUs

Data: 2026-10-11. Legenda: **[confirmado]** fonte citada · **[incerto]** fonte secundária ou não verificada · **[estimativa]** conta minha.

## TL;DR

- **O QR do BU é assinado.** Ele é a verdade-raiz, e a foto e o OCR passam a ser evidência e plano B. Pelo manual de 2024, os dados se dividem em vários QRs, cada um com um `HASH` SHA-512 acumulado, e o último traz `ASSI`, uma assinatura Ed25519 sobre o último hash. A chave pública é publicada pelo TSE. **[confirmado, manual 2024]**
- **Ponto aberto para 2026:** trechos do manual de 2026 falam em "EdDSA **ou ECDSA**" e num **certificado da urna** dentro do QR. **[incerto]** O PDF de 2026 devolveu 403 para mim. É preciso baixá-lo à mão e confirmar antes de escrever código.
- **Validação offline é viável:** basta embutir no app as chaves públicas ou os certificados da AC, conferidos contra a lista de hashes SHA-512 publicada pelo TSE. Só a checagem de revogação de certificado precisa de rede. **[confirmado para chaves e hashes; revogação segundo o projeto urna_aberta]**
- **Consequência:** se o QR é assinado, a revisão por 3 a 5 auditores só faz falta no caminho sem QR (QR ilegível ou BU danificado). Isso derruba o custo humano de cerca de 2,3 milhões de revisões para algo como 5 a 15% disso. **[estimativa]**
- **Leitura de QR:** `zxing-cpp` (Apache-2.0) compilado para WASM roda no navegador e em app nativo.
- **Fallback de OCR/visão não chinês:** Gemma 3 (12B ou 27B) ou Pixtral 12B self-hosted, e docTR (Apache-2.0) para OCR puro.
- **Infraestrutura:** Cloudflare (Workers, Queues, R2) mais Postgres append-only mais log Merkle (Tessera), com resultado em arquivos estáticos. Custo de nuvem na casa de **centenas de dólares** no dia. **[estimativa]**

---

## 1. Leitura do BU (QR code)

**O que se sabe:**
- O BU impresso tem QR(s) com o conteúdo completo. A leitura não exige internet. O TSE publica o manual "QR Code no Boletim de Urna: manual para criação de aplicativos de leitura", edições 2016, 2018, 2020/22, 2024 e 2026. **[confirmado]**
- **Vários QRs por BU:** a quantidade depende do número de candidatos. Cada QR traz um cabeçalho `QRBU:<índice>:<total>`, versão e identificação da urna e da seção. **[confirmado no parser do repositório lucas-daniel-sm e no TabNews]**
- **Integridade:** `HASH` é o SHA-512 hexadecimal acumulado de todos os QRs anteriores, o que permite verificar a sequência. `ASSI` é a assinatura Ed25519 do último hash, só no último QR. **[confirmado, manual 2024]**
- **Chaves:** segundo o TRE-SP, o TSE gera um par de chaves por UF e publica as chaves públicas. A urna assina com libsodium. **[incerto: veio de snippet de busca; a página deu 403]**
- **2026:** os snippets do manual citam "EdDSA ou ECDSA" mais o certificado da urna no QR. Se for assim, a validação passa a ser uma cadeia de certificados até a AC da urna, com as ACs fixadas no app. **[incerto]**
- **Ressalva:** o projeto urna_aberta diz que urnas modelo 2020 e 2022 assinam os arquivos `.vsc` da mídia com **Ed521**. Isso se refere aos arquivos de resultado, não necessariamente ao QR. **[incerto, fonte de terceiros]**

**Bibliotecas de leitura (todas open source):**

| Lib | Licença | Onde roda | Nota |
|---|---|---|---|
| **zxing-cpp** | Apache-2.0 | C++, WASM (`zxing-wasm`, ~1,3 MB), Android, iOS, Python | Recomendada. Benchmark (de fornecedor concorrente): mediana de 74 ms por imagem, recall de 67% em fotos difíceis **[incerto]**. Restringir a QR e ligar `tryHarder` ajuda. |
| ZXing (Java) | Apache-2.0 | Android, JVM | Original. Em modo de manutenção. |
| zbar | LGPL-2.1 | C, Python | Ok no servidor. A LGPL complica o app. |
| `BarcodeDetector` (Web API) | nativo | Chrome Android | Grátis, mas não existe no Safari/iOS. Usar como atalho, com o zxing-wasm de fallback. |
| ML Kit / Apple Vision | proprietário, grátis | app nativo | Robusto em foto ruim. Não é open source. |

**Avaliação:** com o QR assinado e válido, os votos não precisam de OCR nem de humanos, porque a assinatura já prova a origem: o conteúdo saiu de uma urna com chave oficial. Ela **não** prova que aquele papel estava afixado naquela seção. Para isso servem a foto (com o QR visível), a metadata e o cruzamento com o BU que o TSE publica depois. Dois BUs com assinatura válida e conteúdo diferente para a mesma seção são um **alarme de alta prioridade** (por exemplo, urna de contingência), não uma fraude do app.

**Recomendação:** ler os QRs no próprio celular (WASM ou nativo), validar a assinatura localmente com libsodium.js ou tweetnacl, e enviar `payload dos QRs + foto comprimida`. O servidor revalida a assinatura e nunca confia no cliente.

## 2. Fallback de visão/OCR (só quando o QR falha)

| Modelo | Licença | Origem | Tabela/documento | Custo/velocidade | Veredito |
|---|---|---|---|---|---|
| **Gemma 3 (4B/12B/27B)** | Gemma Terms of Use (não é OSI, permite uso comercial, tem política de uso) | Google (EUA) | Bom em OCR e documento **[incerto, sem benchmark próprio]** | 12B cabe numa GPU de 24 GB. Dá para self-host. | **Recomendado #1** |
| **Pixtral 12B** | Apache-2.0 | Mistral (França) | Bom em documento | Uma GPU. **Sem manutenção** (substituído pela Mistral). | Recomendado #2, se a licença Apache pesar |
| Mistral OCR (API) | proprietário | França | Forte em tabelas | ~US$ 2 a 4 por 1.000 páginas **[incerto, varia por versão]** | Opção paga sem GPU |
| Llama 3.2 Vision 11B/90B | Llama Community License, com **restrição UE** nos modelos multimodais | Meta (EUA) | Ok | Uma GPU (11B) | Possível. A licença é chata. |
| Florence-2 (0,23B/0,77B) | MIT | Microsoft | OCR simples. Fraco em extração estruturada. | Muito leve | Útil para pré-recorte e detecção de região |
| docTR | Apache-2.0 | Mindee (França) | OCR de linha. A estrutura fica por sua conta. | CPU ou GPU, rápido | **Recomendado para OCR puro** e validação cruzada |
| Tesseract | Apache-2.0 | — | Fraco em foto torta ou impressão térmica | CPU, grátis | Último recurso |
| LLaVA | Apache-2.0 ou Llama, conforme a variante | acadêmico | Fraco em tabela densa | — | Não |
| Qwen-VL, PaddleOCR | Apache-2.0 | China | Fortes em documento | — | Excluídos por preferência do usuário |

**Uso:** o modelo de visão gera um **rascunho** dos números, e humanos (k-de-n) confirmam. Nunca entra resultado sem confirmação humana. A soma dos votos tem de bater com "comparecimento", "brancos" e "nulos" impressos no BU, o que já dá uma checagem automática.

## 3. Anti-fraude e anti-Sybil com anonimato

| Camada | Como | Anonimato | Comentário |
|---|---|---|---|
| **Assinatura do QR** | Verdade-raiz. Envio sem assinatura válida cai no caminho lento. | total | Elimina a fraude de conteúdo no caminho principal. |
| Proof-of-work no cliente | **ALTCHA** (MIT) ou **Cap** (Apache-2.0), self-hosted | total | Encarece spam em massa. Não barra atacante com botnet. |
| Cloudflare Turnstile | grátis. Usa Private Access Tokens em dispositivos Apple. | parcial (a CF vê IP e headers) | Bom complemento. Não é Privacy Pass puro **[incerto]**. |
| Attestation | Play Integrity (cota padrão de **10 mil/dia**, aumento exige pedido de até 1 semana) e App Attest (anônimo, chave por instalação) | bom | **Pedir aumento de cota com antecedência.** Não serve para a versão web. |
| Rate limit | por IP, ASN e /24, por token de PoW e por seção (máx. N envios por seção) | bom | Cloudflare WAF rate limiting. |
| Hash perceptual da foto | pHash/dHash (lib `imagehash`) mais SHA-256 exato | total | Detecta a mesma foto reenviada para seções diferentes. |
| Manipulação de foto | Checar se o QR decodificado da foto bate com o payload enviado. EXIF é opcional e falsificável. | total | Com assinatura válida, manipular a foto não muda os números. |
| **Auditores: atribuição aleatória** | O servidor sorteia a tarefa. O auditor não escolhe UF nem seção. | pseudônimo | Impede a concentração de um grupo em seções-alvo. |
| Consenso k-de-n | 3 de 5 concordando. Divergência leva a mais revisores e depois a moderador. | — | Só no caminho sem QR. |
| Reputação | Peso por acerto em **tarefas-isca** (BUs com QR já validado, usados como gabarito oculto) | pseudônimo | Ouro: a verdade-raiz calibra os humanos. |
| Cruzamento com o TSE | Comparar com os BUs publicados pelo TSE (dados abertos ou BU na Web) | — | A divergência é o produto: é o que interessa publicar. |

**Anonimato:** o envio de foto não pede conta. A PoW, o Turnstile ou o attestation geram um token efêmero. Remover o EXIF (GPS) no cliente antes do upload. O IP fica só no log da borda, com retenção curta. **[decisão de design]**

## 4. Segurança e disponibilidade

- **Leitura (público):** resultado em **arquivos JSON estáticos** (por seção, município, UF e Brasil) no R2 atrás do CDN da Cloudflare. Regerar a cada 1 a 5 minutos. Um DDoS na leitura bate no cache, não na origem.
- **Escrita:** Worker valida token e assinatura, coloca na **fila** (Cloudflare Queues), e um consumidor grava em lote. A origem (Postgres) nunca recebe tráfego público direto.
- **Banco append-only:** tabela `eventos` só com INSERT (sem permissão de UPDATE/DELETE para a role da aplicação). Resultados derivados por view ou job.
- **Log transparente:** cada BU aceito vira uma folha num **log Merkle tile-based** (Trillian Tessera, Go; padrão C2SP, o mesmo do Static CT). As tiles são arquivos estáticos no R2, e qualquer um baixa e verifica provas de inclusão e consistência. Publicar os checkpoints assinados em vários lugares (GitHub, Mastodon, jornal) para impedir a reescrita do histórico.
- **Fotos:** R2 (sem custo de egress). Chave = SHA-256 da foto (dedup natural).
- **Pico [estimativa]:** 470 mil seções × ~3 envios = ~1,4 milhão de uploads em 4 h. Média de ~100/s, pico de ~1.000/s na primeira hora. Workers e Queues aguentam.

**Custo estimado [estimativa, preços oficiais do R2]:**

| Item | Conta | US$ |
|---|---|---|
| R2 armazenamento | 1,4 milhão de fotos × 400 KB ≈ 560 GB × US$ 0,015/GB-mês | ~9 por mês |
| R2 escritas (Classe A) | 1,4 milhão × US$ 4,50/milhão | ~6 |
| R2 leituras (Classe B) e egress | egress grátis. ~100 milhões de leituras × US$ 0,36/milhão | ~36 |
| Workers e Queues | plano pago, alguns milhões de requisições | ~5 a 50 **[incerto]** |
| Visão (fallback, ~10% = 47 mil BUs) | Mistral OCR ~US$ 2 a 4/1.000, ou GPU alugada por 1 dia | ~100 a 300 |
| Postgres gerenciado | 1 instância média, 1 mês | ~50 a 100 |
| **Total do evento** | | **~US$ 200 a 500** |

Plano Cloudflare Business ou Enterprise (proteção DDoS com SLA) **não incluído**: o plano grátis tem mitigação de DDoS, mas sem SLA.

## 5. Arquitetura mínima recomendada

```
 [Celular: PWA ou app]
  câmera -> zxing-wasm/nativo -> junta QRs -> valida Ed25519 local (libsodium.js)
  remove EXIF, comprime foto, resolve PoW (ALTCHA) / Turnstile / attestation
            |
            v  HTTPS
 [Cloudflare edge: WAF + rate limit]
            |
 [Worker /submit] --revalida assinatura--> ok?
            |                                  \--não/sem QR--> fila "revisao"
            v
 [Queue "ingest"] ----> [Consumer]
                           |-> R2: fotos/<sha256>.jpg
                           |-> Postgres (append-only: eventos)
                           |-> Tessera: folha no log Merkle -> tiles no R2
                           |-> confere com BU do TSE (quando publicado)
 [Fila "revisao"] -> Gemma 3 / docTR (rascunho) -> sorteio p/ 5 auditores
                       -> consenso 3/5 -> eventos
 [Job a cada 1-5 min] -> agrega -> JSON estáticos no R2
            |
            v
 [CDN público] resultados/*.json + log/tiles + checkpoints assinados
            ^
   público, imprensa, verificadores independentes
```

**Stack simples:**
- Frontend: PWA (TypeScript), `zxing-wasm`, `libsodium-wrappers`. App nativo depois, se for preciso usar attestation.
- Borda: Cloudflare Workers, Queues, R2, Turnstile.
- Backend: um serviço Go (Tessera é Go) ou TypeScript no Worker mais um consumidor Go. Postgres.
- Visão: Gemma 3 12B via vLLM ou Ollama numa GPU alugada só no dia, com docTR como segunda opinião.

## Recomendação

1. **Antes de tudo:** baixar à mão o manual do QR de 2026 e a lista de hashes das chaves públicas no portal do TSE (deram 403 para robô). Confirmar algoritmo (Ed25519 ou ECDSA), se há certificado no QR e se as chaves são por UF. Escrever um verificador de referência com teste usando um BU real de 2024.
2. Produto em torno do **QR assinado**. A foto é evidência, e os humanos ficam só para o caminho sem QR e para as tarefas-isca.
3. Anonimato de verdade: sem conta para quem envia. ALTCHA, Turnstile e rate limit. Attestation só no app.
4. Tudo público e verificável: JSON estático, log Merkle (Tessera), código open source, chaves do TSE fixadas no app.
5. A divergência é a saída principal: publicar "BU assinado ≠ BU publicado pelo TSE" com prova (QR, foto e prova de inclusão).
6. Teste de carga simulando 1.000 envios/s e um ensaio com BUs de 2024 antes de outubro.

## Fontes

- TSE, manual do QR no BU 2026 (403 para robô): https://www.tse.jus.br/eleicoes/eleicoes-2026-content/arquivos/manual-do-qr-code-no-boletim-de-urna/@@display-file/file/manual-do-qr-code-no-boletim-de-urna.pdf
- TSE, manual 2024: https://www.tse.jus.br/eleicoes/eleicoes-2024-content/arquivos/qr-code-no-boletim-de-urna
- TSE, página do manual 2018 (download das chaves e hashes): https://www.tse.jus.br/eleicoes/eleicoes-2018/qr-code-no-boletim-de-urna-manual-para-criacao-de-aplicativos-de-leitura
- TSE, documentação técnica 2022 (ASN.1 do BU e assinaturas): https://www.tse.jus.br/eleicoes/eleicoes-2022/documentacao-tecnica-do-software-da-urna-eletronica
- TRE-SP, QR no BU: https://www.tre-sp.jus.br/eleicoes/eleicoes-dos-conselhos-tutelares/arquivos/qr-code-no-boletim-de-urna
- TSE, apresentação TPS 2021 (EdDSA no QR): https://www.justicaeleitoral.jus.br/tps/arquivos/2021/apresentacao-4-tps-2021-sevin-ecossistema-urna.pdf
- TSE, notícia sobre o BU impresso: https://www.tse.jus.br/imprensa/noticias-tse/2021/Junho/boletim-de-urna-traz-o-resultado-impresso-da-secao-de-votacao
- TSE, dados abertos do BU 2024: https://dadosabertos.tse.jus.br/dataset/resultados-2024-boletim-de-urna
- urna_aberta (verificador independente, Ed521 e ACs da urna): https://github.com/kterto/urna_aberta
- verificador_boletim_urna (parser QRBU): https://github.com/lucas-daniel-sm/verificador_boletim_urna
- TabNews, QRs múltiplos por BU: https://www.tabnews.com.br/ThalissonM/0a065507-73fc-4986-ac49-d62f00c42b69
- zxing-cpp: https://github.com/zxing-cpp/zxing-cpp
- Benchmark zxing-wasm (Dynamsoft, viés de fornecedor): https://www.dynamsoft.com/codepool/benchmark-barcode-reading-javascript-zxing-wasm-dynamsoft-barcode-reader.html
- Gemma Terms of Use: https://ai.google.dev/gemma/terms
- Llama, FAQ (restrição UE multimodal): https://www.llama.com/faq/
- Pixtral 12B, Apache-2.0: https://techcrunch.com/2024/09/11/mistral-releases-pixtral-its-first-multimodal-model
- Pixtral (sem manutenção): https://mistral.ai/fr/news/pixtral-12b
- Florence-2: https://inference-models.roboflow.com/models/florence2/
- Mistral OCR 3, preço: https://news.bensbites.com/posts/53853-mistral-launches-mistral-ocr-3-featuring-improvements-in-processing-forms-scanned-documents-complex-tables-and-handwriting-priced-at-2-per-1000-pages
- Mistral OCR 4, preço (secundária): https://tech-insider.org/mistral-ocr-4-launch-2026/
- ALTCHA: https://altcha.org/open-source-captcha/
- Cap: https://trycap.dev/guide/open-source-captcha
- Turnstile e Private Access Tokens: https://blog.cloudflare.com/turnstile-private-captcha-alternative/
- Privacy Pass (Cloudflare): https://developers.cloudflare.com/privacy-pass/index.md
- Play Integrity, cotas: https://developer.android.com/google/play/integrity/setup
- App Attest (WWDC21): https://developer.apple.com/videos/play/wwdc2021/10244/
- Trillian Tessera: https://blog.transparency.dev/introducing-trillian-tessera
- Logs tile-based: https://transparency.dev/articles/tile-based-logs/
- R2, preços: https://developers.cloudflare.com/r2/pricing
