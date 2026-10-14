# Patrocínio: espaços, medidas e como ligar/desligar

## Como ligar e desligar
Os dois interruptores precisam estar ligados para um anúncio aparecer.

| Interruptor | Onde | Efeito | Quando usar |
|---|---|---|---|
| **Remoto** | `sponsors.json` no CDN: `"enabled": true/false` | Liga/desliga todos os espaços **na hora**, sem nova versão | Durante a revisão da Apple/Google (deixe `false`), em crise, fora do horário vendido |
| **Da versão** | `eas.json` → `EXPO_PUBLIC_SPONSORS`: `on`/`off` | A versão gerada com `off` nunca mostra patrocínio | Uma versão "limpa" para a loja, se preferir |

Recomendação: deixe `on` na versão e controle tudo pelo `"enabled"` remoto. Envie para revisão com `enabled: false` e ligue depois da aprovação.

Espaço sem patrocinador vendido não aparece (nada de "anuncie aqui").

## Os espaços

| Chave | Onde aparece | Audiência | Formato |
|---|---|---|---|
| `brasil` | Tela Brasil (inicial), abaixo dos resultados de Presidente e Governador | **A maior**: toda pessoa que abre o app, a noite inteira da apuração | Faixa 3:1 + nome + texto |
| `sent` | Logo após "✓ Boletim enviado. Obrigado!" | Só quem fiscalizou (o público mais engajado) | Faixa 3:1 + nome + texto |
| `welcome` | Último passo da animação de abertura ("Comparamos com o TSE") | Todo novo usuário, uma vez | Faixa 3:1 + nome + texto |
| `list` | Sobre → "Quem apoia" | Quem quer saber quem financia | Só o nome (botão com link) |

## Medidas da arte

O espaço tem a largura do cartão: cerca de **326 pt** num iPhone de 390 pt de largura (16 pt de margem + 16 pt de recuo de cada lado). A imagem ocupa a largura inteira com proporção **3:1** e cantos arredondados de 10 pt.

| Item | Especificação |
|---|---|
| Imagem | **1200 × 400 px** (3:1), PNG ou WebP, **até 150 KB** |
| Área segura | Texto e logo dentro dos **1080 × 320 px** centrais (60 px de margem lateral, 40 px em cima e embaixo): os cantos são cortados |
| Texto dentro da imagem | Mínimo de 40 px de altura de letra (fica legível em 326 pt) |
| `name` | Até **40 caracteres** (aparece em negrito abaixo da imagem) |
| `text` | Até **120 caracteres** (opcional) |
| `url` | Link `https://` do patrocinador (abre no navegador) |
| Fundo | Não use o verde-petróleo `#0F5257` nem o laranja `#F4A261` do app como cor dominante (a arte não pode parecer parte do app) |

Exemplo de `sponsors.json`:
```json
{
  "enabled": true,
  "slots": {
    "brasil": { "name": "Empresa X", "image": "sponsors/empresa-x-brasil.webp", "url": "https://empresax.com.br", "text": "Apoia a fiscalização cidadã." },
    "sent": { "name": "Empresa Y", "image": "sponsors/empresa-y.webp", "url": "https://empresay.com.br" }
  },
  "list": [{ "name": "Empresa X", "url": "https://empresax.com.br" }, { "name": "Empresa Y", "url": "https://empresay.com.br" }]
}
```
`image` pode ser um caminho no próprio CDN (`sponsors/...`) ou uma URL completa.

## Regras de venda (constam do contrato)
- Rótulo **PATROCÍNIO** sempre visível (já é automático).
- Mesmo anúncio para todos; sem segmentação, sem SDK de anúncios, sem rastreio.
- **Não aceitamos:** partidos, candidatos, campanhas, governos e órgãos públicos, fornecedores das urnas ou do TSE, casas de aposta, conteúdo político ou eleitoral.
- O patrocinador não tem nenhuma influência sobre conteúdo, resultados ou divergências.
- Nunca no leitor de QR, no veredito da seção, nas divergências, na página do candidato nem na animação "A apuração começou".
- Revisão jurídica antes da primeira venda (Lei 9.504, art. 57-C).

Logo do projeto para materiais de patrocínio (mídia kit, propostas): `brand/logo/` (veja o README de lá). O patrocinador nunca altera nem se funde ao nosso logo; a marca dele aparece sempre separada, no espaço do slot.
