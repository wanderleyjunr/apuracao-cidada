# Fluxos

## Captura → prova → comparação
```
Eleitor (PWA / WhatsApp)
  └─ lê QRBU 1..N + QRCE (offline) [+ foto]
       └─ fila local → envio
            └─ Ingestão (anti-abuso: PoW/Turnstile, rate limit, dedupe)
                 ├─ CAP-2 valida: sequência → cadeia SHA-512 → ASSI com o certificado QRCE
                 ├─ CAP-6 confere IDUE→certificado contra capturas anteriores
                 └─ CAP-3 grava no registro append-only (hash + carimbo de tempo)
                      └─ CAP-4 compara com o espelho TSE (bu.dat da seção)
                           ├─ ✅ igual
                           ├─ 🚨 divergente → página "Divergências"
                           └─ ⏳ pendente (TSE ainda não publicou)
                                └─ CAP-5 páginas estáticas por seção + cobertura %
```

## Âncora de confiança do certificado (enquanto o TSE não informa a AC raiz)
```
capturas independentes da mesma urna → mesmo certificado? → "urna X = chave Y" registrado
depois: certificado/assinaturas do TSE (vota.vsc) para o IDUE X → iguais? senão 🚨
```

## Dia inteiro (CAP-9)
```
~7h  zerésima: IDUE + hora (foto)
17h  BU: IDUE + HRAB + votos (QR assinado)
após TSE: bu.dat + log.jez da seção
→ IDUE e horários têm que bater; diferença = "troca de urna, conferir ata"
```
