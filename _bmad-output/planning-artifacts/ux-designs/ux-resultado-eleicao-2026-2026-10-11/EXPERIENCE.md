---
status: final
updated: 2026-10-11
sources:
  - ../../../specs/spec-conferencia-bu/SPEC.md
design: DESIGN.md
---

# Experiência: Confere BU

## Foundation

- **Formato:** PWA mobile first, aberta por link (sem instalar), mais páginas públicas responsivas por seção.
- **Prazo:** o 2º turno é em 25/10/2026; o piloto do 1º turno usa a mesma tela, com N cards.
- **Sem sistema de UI externo.** A identidade visual está em [DESIGN.md](DESIGN.md).
- **Princípio:** a estrutura é familiar (resultados do TSE e do Google); a pergunta é nova (porta × TSE).

## Information Architecture

| Superfície | Entrada | Jornada |
|---|---|---|
| **Seção** (minha seção) | aba 1 · link `/s/<uf>/<mun>/<zona>/<secao>` | Cida 2, 7, 9 · Marcos 3–6 |
| **Escanear** (câmera + folha) | botão central | Cida 5–6 · Marcos 1 |
| **Boletim lido** (revisão antes de enviar) | fim do escaneamento | Cida 6 |
| **Cobertura** (Brasil e UF) | aba 2 | — (convite: "minha cidade precisa de boletins") |
| **Divergências** (lista pública, filtro por UF) | aba 4 · alerta | Marcos 8 |
| **Provas** (fotos, assinatura, registro, arquivo TSE) | botão na Seção | Marcos 5 |
| **Verificar sem o app** (código + dados brutos) | botão em Provas | Marcos 6 |
| **Sobre / Como funciona** | aba 5 | Cida 1 |
| **Card de compartilhamento** (story 9:16) | "Compartilhar a prova" | Cida 10 · Marcos 7 |

## Voice and Tone

O app fala com a Dona Cida: frases curtas, sem jargão ("boletim", não "BU"; "assinatura da urna", não "EdDSA").

| Situação | Texto |
|---|---|
| Votação aberta | "Votação em andamento. A urna fecha às 17h. Depois, fotografe o boletim na porta da seção." |
| Enviado | "Boletim da porta registrado · assinatura da urna válida" |
| Idêntico | "Idêntico ao TSE" + "Boletim da porta (17:06) = publicado pelo TSE (18:47)" |
| Diverge | "Diferente do TSE" + "Precisa de explicação; não é acusação." |
| Offline | "Sem internet. Tudo fica salvo no celular e é enviado quando a conexão voltar." |
| Explicada | "Divergência explicada" + documento |

Palavras proibidas: "fraude", "vencedor", "ganhou", "projeção", "BATEU".

## Component Patterns

- **Seletor de local:** é lembrado no dispositivo. Ao ler um QR, o local vem do próprio boletim; não se digita nada.
- **Turno 1º/2º:** padrão 2º no dia 25. O 1º alimenta o piloto.
- **Ordem dos candidatos:** quem tem mais votos na seção vem primeiro. Sem votos ainda, a ordem é pelo número.
- **Card de candidato:** na coluna TSE, "…" enquanto pendente. O status por candidato (✓ confere / ✕ diverge (−N)) só aparece depois que o TSE publica.
- **Compartilhar:** gera um story 9:16 com veredito, local e link verificável. Uma divergência sai como "Divergência em análise". Um print sem link não vale.

## State Patterns

Estados da seção, nesta ordem no dia:

1. **Votação em andamento** (8h–17h): sem números. Ações: "Me lembrar às 17h" e "Fotografar a zerésima (manhã)", que é opcional.
2. **Sem boletim** (após 17h): convite para escanear e "N pessoas da sua cidade já enviaram".
3. **Boletim registrado, aguardando o TSE:** números da porta e TSE "…". Ação: "Avise-me quando o TSE publicar".
4. **Idêntico ao TSE:** veredito positivo e provas.
5. **Diferente do TSE:** destaca o campo e mostra causas possíveis (urna de contingência, recuperação de dados, erro de leitura) **antes** das provas.
6. **Divergência explicada:** documento anexado (ata ou nota do TSE). A divergência nunca some; ela muda de estado.

Outros estados:
- **Envios concordantes:** "Mais 2 pessoas enviaram. Os três são idênticos."
- **Envios conflitantes** (assinaturas diferentes para a mesma seção): alerta de prioridade, que não vira veredito.
- **Offline / fila:** contador de boletins pendentes de envio.
- **Escaneamento incompleto:** "Lido 2 de 4", com os que faltam indicados.
- **QR ilegível:** pedir uma foto mais próxima. Sem QR → "enviar foto para auditores" (CAP-10).
- **Assinatura inválida:** "Este boletim não passou na verificação" e não é publicado como prova.

## Interaction Primitives

- **Botão central (âmbar):** abre a câmera direto em leitura contínua, com vibração curta a cada QR lido.
- **Notificações:** às 17h ("hora de fotografar"), quando o TSE publica a seção e quando há divergência na seção acompanhada.
- **Envio automático** quando a conexão volta, sem a pessoa precisar voltar ao app.
- **Área segura inferior** (ver DESIGN.md): nada passa por trás do botão central.

## Accessibility Floor

- O status nunca é transmitido só por cor: sempre ícone e texto.
- Alvos de toque ≥ 44px, inclusive as abas de cargo e o turno.
- A câmera tem alternativa: enviar foto da galeria.
- Leitores de tela anunciam o veredito e a diferença por extenso ("Vinte e dois: porta noventa e oito, TSE noventa e cinco").
- Texto ampliável sem cortar os nomes dos candidatos (quebra em duas linhas, como "FLÁVIO / BOLSONARO").
- Funciona em Android de entrada e em rede 3G.

## Key Flows

**Jornada 1: Dona Cida, 58 anos, Senador Cortes/MG, seção 37.**
1. Qui 22/10: recebe o vídeo no grupo da família e abre o link no navegador, sem instalar.
2. Escolhe Senador Cortes · seção 37. O app memoriza.
3. Dom 9h: vota e vê a zerésima na porta (foto opcional).
4. Toca em "Me lembrar às 17h".
5. 17h05: chega o alerta, ela volta à porta e toca em escanear.
6. Lê de 1 a 4 de 4. Sem sinal, vê "salvo, envia quando voltar a internet".
7. Em casa, no Wi-Fi: o envio acontece sozinho, e aparece "Boletim registrado · aguardando o TSE".
8. 18h50: notificação "O TSE publicou a sua seção".
9. **⭐ Clímax:** "Idêntico ao TSE", com a foto que ela mesma tirou como prova: *"meu voto chegou inteiro"*.
10. Compartilha o story no grupo, trazendo mais gente.

**Jornada 2: Marcos, 34 anos, Campinas/SP, seção 88.**
1. 17h10: escaneia, vê "assinatura válida" e envia pelo 4G.
2. 17h40: "Mais 2 pessoas enviaram. Os três são idênticos."
3. 19h20: o TSE publica, e a tela mostra "Diferente do TSE · 22: porta 98 · TSE 95 (−3)".
4. Antes das provas, lê "fato a ser explicado, não prova de fraude" e as causas possíveis.
5. Abre as provas: 3 fotos, assinatura, registro de 17h10 e arquivo do TSE.
6. **⭐ Clímax:** "Verificar sem o app" abre o código e os dados brutos; qualquer pessoa refaz a conta.
7. Compartilha "Divergência em análise" com o link.
8. A seção entra em Divergências, e os observadores (OAB, imprensa e as campanhas dos dois lados) recebem um alerta automático.
9. Dias depois: a seção muda para "Divergência explicada", com o documento anexado.

## Inspiration & Anti-patterns

- **Inspiração:** a estrutura dos resultados do TSE (local, turno, abas, cards com foto) e a lista limpa do Google (`imports/`).
- **Anti-padrões:**
  - placar nacional;
  - destaque para quem "está ganhando" no país;
  - linguagem alarmista;
  - exigir conta ou instalação;
  - pedir localização.

## Open Questions

- **Quem marca uma divergência como "explicada"?** [ASSUMPTION] É o conselho de neutralidade, com aprovação de membros de lados diferentes e um documento público.
- **Nome definitivo do app** (o placeholder "Confere BU" está nos mocks).
- **A fonte do sistema basta,** ou haverá uma fonte de marca?
- **Dark mode:** não foi decidido. A paleta T4 "Noite elétrica" ficou só como referência.
