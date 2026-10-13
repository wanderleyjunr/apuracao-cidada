---
name: Confere BU (nome provisório)
description: Conferência cidadã do Boletim de Urna. Estrutura familiar de app de resultados, identidade própria, neutra e "printável".
status: final
updated: 2026-10-11
sources:
  - ../../../specs/spec-conferencia-bu/SPEC.md
colors:
  primary: '#0F5257'
  secondary: '#3BB3A6'
  accent: '#F4A261'
  ink: '#0D2224'
  surface-base: '#F2F7F6'
  surface-raised: '#FFFFFF'
  border-hairline: '#DCE7E5'
  ink-secondary: '#5B6470'
  coverage-high: '#0F5257'
  coverage-mid: '#3BB3A6'
  coverage-low: '#8FD3CB'
  status-ok: '#12A150'
  status-diverge: '#D62828'
  status-pending: '#5C6B7A'
  status-diverge-surface: '#FDEEEE'
  offline-surface: '#FFF3E6'
  offline-ink: '#7A4A12'
typography:
  family:
    note: 'Fonte do sistema: -apple-system, Roboto, "Segoe UI", sans-serif. [ASSUMPTION] usada nos mocks e não escolhida explicitamente'
  verdict:
    size: 19px
    weight: 900
  number-big:
    size: 26px
    weight: 900
  vote-count:
    size: 17px
    weight: 900
  candidate-name:
    size: 12px
    weight: 900
    case: upper
  body:
    size: 12px
    weight: 400
  meta:
    size: 10.5px
    weight: 600
  nav-label:
    size: 9.5px
    weight: 700
rounded:
  sm: 9px
  md: 12px
  lg: 14px
  sheet: 20px
  pill: 20px
  full: 50%
spacing:
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 16px
  '5': 24px
components:
  verdict-sticker:
    rotate: -1.5deg
    shadow: '0 4px 0 rgba(0,0,0,.13)'
  candidate-photo:
    size: 50px
    border: 3px
  fab-scan:
    size: 54px
  bottom-nav:
    height: 52px
---

## Brand & Style

A estrutura é a que o eleitor já conhece dos resultados do TSE e do Google: local, turno, abas de cargo e um card por candidato. A pergunta, porém, é outra: **"o boletim da porta bate com o do TSE?"** A identidade é própria e **nunca imita o TSE** (sem logo, sem o amarelo e o verde oficiais), para não parecer órgão público.

O tom é tropical profissional: verde-mata e petróleo com âmbar quente. O app é sério na prova e caloroso no convite. O elemento de assinatura visual é o **adesivo do veredito**, herdado da direção "Cartaz": um bloco levemente inclinado, feito para print e story.

Neutralidade é regra visual. Os dois candidatos recebem exatamente o mesmo tratamento, e nenhuma cor de marca remete a partido.

## Colors

- **Verde-mata `{colors.primary}`:** cabeçalho, botão principal, aba ativa e o veredito "idêntico".
- **Turquesa `{colors.secondary}`:** borda dos cards de candidato e progresso de leitura dos QR Codes.
- **Âmbar `{colors.accent}`:** botão central de escanear, o adesivo "Votação em andamento" e o CTA de compartilhar.
- **Status:**
  - `{colors.status-ok}` para idêntico/confere.
  - `{colors.status-diverge}` para diverge.
  - `{colors.status-pending}` para aguardando.
  - Sempre acompanhados de ícone e texto, nunca só a cor.
- **Cobertura:** escala de três tons, `{colors.coverage-high}`, `{colors.coverage-mid}` e `{colors.coverage-low}`. O exterior (ZZ) usa `{colors.accent}`.

Evitar: vermelho como cor de marca (associado ao PT); verde-amarelo e azul como cor de marca (associados ao PL e à campanha de Flávio); rosa e magenta (reprovados pelo Alino); qualquer cor ligada a um candidato.

## Typography

Fonte do sistema. A hierarquia vem do peso:
- Veredito e números em 900.
- Nomes de candidatos em caixa alta, 900.
- Corpo em 400.
- Votos usam `{typography.vote-count}`, grandes e tabulares, porque o número é o protagonista.

## Layout & Spacing

- **Mobile first.** Coluna única, margens de 12px e escala de 4/8/12/16/24.
- **Cabeçalho** `{colors.primary}` com cantos inferiores arredondados, sobre o qual o adesivo avança ~10px.
- **2º turno:** dois cards lado a lado.
- **1º turno:** grade de 2 colunas.
- **Área segura inferior:** todo conteúdo rolável reserva `{components.bottom-nav.height}` mais a saliência do `{components.fab-scan}` (~28px). Nada passa por trás do botão central.

## Elevation & Depth

Profundidade só no adesivo do veredito (sombra sólida deslocada, como um adesivo colado) e no botão central, que tem anel na cor de fundo. Os cards são planos, com borda.

## Shapes

- `{rounded.lg}` para cards.
- `{rounded.md}` para botões (uma linha, 44px).
- `{rounded.sheet}` para cabeçalho e folha inferior.
- `{rounded.pill}` para etiquetas de status.
- Fotos de candidatos em círculo completo.

## Components

- **Cabeçalho de seção:** nome do app, alternância de turno 1º/2º e o seletor de local (município, zona e seção).
- **Adesivo do veredito:** etiqueta de status no canto superior, título e uma linha de evidência. Tem quatro variantes:
  - âmbar, "Votação em andamento";
  - turquesa, "Boletim da porta registrado";
  - verde-mata, "Idêntico ao TSE";
  - vermelho, "Diferente do TSE".
- **Card de candidato:**
  - Foto oficial do TSE em círculo `{components.candidate-photo.size}`, partido e número, e nome.
  - Duas colunas, PORTA e TSE, e a linha de status.
  - Quando diverge, usa a borda `{colors.status-diverge}` e o fundo `{colors.status-diverge-surface}`.
- **Linha de prova:** ícone e texto (foto, assinatura, registro público, arquivo do TSE).
- **Folha de escaneamento:** quadrados numerados por QR Code (lidos em `{colors.secondary}`, pendentes tracejados), mais o chip "certificado".
- **Aviso offline:** fundo `{colors.offline-surface}`.
- **Mapa de cobertura:** mapa do Brasil com o formato real de cada UF, colorido **só pela % de cobertura**. Nunca por candidato, ao contrário dos mapas de imprensa que pintam pelo vencedor. O exterior (ZZ) aparece numa linha à parte, e tocar num estado lista as cidades.
- **Botão:** sempre uma linha, altura 44px. Texto curto; nunca quebra em duas linhas.
- **Navegação inferior:** Seção · Cobertura · [Escanear] · Divergências · Sobre.

Mockups (os documentos de design prevalecem em caso de conflito): [telas-chave](mockups/telas-chave.html) · [estados do dia](mockups/estados-do-dia.html) (paleta P3) · [estrutura familiar](mockups/estrutura-familiar.html) (só a estrutura; a paleta ali é provisória).

## Do's and Don'ts

- ✅ Mesmo tamanho, foto, borda e peso para os dois candidatos.
- ✅ Veredito só depois que o TSE publica.
- ❌ Nunca "vencedor", percentual de vitória ou soma nacional de votos por candidato.
- ❌ Nunca a palavra "fraude"; usar "divergência" e "a ser explicada".
- ❌ Nunca imitar a identidade visual do TSE.
