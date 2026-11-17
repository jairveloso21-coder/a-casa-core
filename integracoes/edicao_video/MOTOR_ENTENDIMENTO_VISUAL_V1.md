# CASA Video Lab — Motor de Entendimento Visual (proposta V1)

Data: 2026-11-16. **Estado: ESPECIFICAÇÃO PUBLICADA / INFERÊNCIA AUTOMÁTICA NÃO HOMOLOGADA.**

## Motivo
A montagem V2/V3 usava heurísticas de duração e aparência de quadros, sem representar semanticamente o que acontece. Cortes podem ficar tecnicamente contínuos, mas narrativamente incompletos. O motor transforma a **gravação original** em um **índice temporal privado de eventos em texto**; não cria legendas e não insere esse texto no vídeo.

## Contrato de entrada
- Aceitar apenas mídias brutas identificadas por caminho, SHA-256, duração, codec, fps e áudio.
- Recusar V1/V2/V3 exports como fonte editorial.
- Nunca alterar/remover o bruto ou transferir frames/dados privados para serviços externos sem autorização.
- Cada mídia/projeto terá indexação própria, separada dos demais projetos CASA.

## Esteira proposta
1. **Leitura estrutural:** ffprobe, FFmpeg e extração amostral de frames. Detectar longos intervalos escuros, logos, telas de loading e dinâmica luminosa. Descartar automaticamente apenas candidatos, nunca cenas narrativas.
2. **Segmentação sugestiva:** PySceneDetect AdaptiveDetector/ThresholdDetector apontam mudanças visuais, não o significado da cena. Não usar detecção de movimento isolada como decisão de corte.
3. **Compreensão multimodal:** testar Qwen3-VL-2B-Instruct com frames amostrados e clipes breves, prompt em português para ação/participantes/ordem/causa/consequência. Não inferir eventos entre frames quando não há prova.
4. **Áudio opcional:** whisper.cpp apenas para fala narrada ou diálogos. Sons de jogo, músicas e efeitos não são descrição visual nem justificam corte automático.
5. **Consolidação:** unir observações por janela temporal e preservar evidência e incerteza. Produzir `semantic_events.json` por mídia.
6. **Decupagem editorial:** identificar preparação → ação → consequência → desfecho, continuidade espacial/temporal, duração de planos e janelas de baixa informação. Avisar quando o bruto não contém o desfecho esperado.
7. **Linha do tempo:** permitir escolhas justificadas para o editor, mantendo IN/OUT relativos ao bruto, sem saltos internos que destruam causalidade. Solicitar avaliação editorial antes do render.
8. **QA:** conferir hashes, monotonicidade, alinhamento áudio/vídeo, presença de setup e payoff, ausência de falsos acontecimentos; medir retenção apenas depois de publicar, por dados reais.

## Registro mínimo de evento
```json
{
  "source_sha256": "<hash do bruto>",
  "start_seconds": 12.0,
  "end_seconds": 16.0,
  "description_pt": "O jogador inicia uma aproximação e executa uma ação identificável",
  "participants": ["jogador", "adversário"],
  "event_type": "action",
  "causal_predecessor": "evento_anterior",
  "observed_result": "não conclusivo na amostra",
  "visual_visibility": "adequada",
  "confidence": "medio",
  "source_evidence": ["frame_time=12.0", "frame_time=14.0", "frame_time=16.0"],
  "editorial_decision": "rever contexto antes de cortar",
  "render_as_overlay": false
}
```

O registro é **metadado privado**, jamais texto exportado no vídeo.

## Hardware FAMILIA e instalação
Notebook Windows 11 + WSL2, i5-10210U, ~19,83 GB RAM, GPU MX250. Não assumir que a MX250 comporte inferência de vídeo inteira em VRAM. Começar com poucos quadros por janela, resolução moderada, quantização e execução isolada com limites medidos de RAM/CPU, somente depois de revisar licenças e compatibilidade. Cache dos frames com descarte controlado. Usar ferramentas globais já homologadas, se compatíveis, sem duplicar serviços.

## Fontes técnicas pesquisadas
- Qwen3-VL: https://github.com/QwenLM/Qwen3-VL (interpretação de vídeo; candidato, **não instalado/testado**).
- Qwen3-VL-2B: https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct (pesos e model card; candidato, **não testado**).
- PySceneDetect: https://www.scenedetect.com/docs/latest/ (detecção de transição visual, não de narrativa).
- whisper.cpp: https://github.com/ggml-org/whisper.cpp (fala; não é video captioning).
- OpenTimelineIO: https://github.com/AcademySoftwareFoundation/OpenTimelineIO (linha do tempo, não analisa significado).

## Gatilhos de homologação
- SOURCE: especificação revisada no GitHub = **verificado após readback**.
- SANDBOX: inspeção humana/IA assistida de frames e índice textual = **prova de conceito, não inferência de modelo**.
- HOST FAMILIA: instalação e benchmark de Qwen3-VL/scene detector = **pendente**.
- DEVICE e retenção real: **pendentes**.

Não registrar SUCCESS de visão automática enquanto não existir arquivo gerado pelo modelo local, logs, hash, versão, medições e revisão das descrições contra vídeo bruto.
