# CASA Video Lab — Motor de Entendimento Visual (proposta V1)

Data: 2026-11-16. **Situação reconciliada em 2026-11-17:** o **modelo opcional Qwen3-VL** de inferência visual automática continua sem homologação HOST; isso **NÃO bloqueia** a esteira de edição já comprovada no FAMILIA por recibos reais de REA Video, MakeMyClip e FFmpeg.

## Gate operacional corrigido: VLM opcional, edição disponível

**Não utilizar `QWEN3_VL_NOT_HOMOLOGATED` como motivo para impedir inspeção, decupagem humana/assistida, roteiro, dublagem e renderização.** A seleção de editor é independente da existência do modelo de entendimento visual. A sequência segura é: original íntegro com hash → REA Video decompose existente → observações visuais fundamentadas em quadros reais (ou REVISÃO NECESSÁRIA se inacessíveis) → timeline privada → editor MakeMyClip 0.5.2/FFmpeg conforme capacidade efetivamente disponível → QA de MP4 com prova física → aprovação editorial. Não gerar descrições falsas quando os quadros não foram inspecionados.

Evidências já existentes (não repetir nem renomear missões):
- FAMILIA / REA Video decompose real: `Projetos-Arquivo/missions/outbox/CANAL_DARK/M_20261116_CANAL_DARK_CP35_REA_DECOMPOSE_REAL_MEDIA_V1_receipt.json` — `REAL_REA_DECOMPOSE_PASS`, exit 0.
- FAMILIA / MakeMyClip 0.5.2: `Projetos-Arquivo/missions/outbox/GLOBAL_HOMOLOGATION/M_20261116_VIDEO_STUDIO_AI_CPD_MAKEMYCLIP_052_PARALLEL_AB_V1_receipt.json` — `TECHNICAL_RENDER_PASS`, MP4 sintético 4,79625 s, full decode, SHA-256 `60458314320da075f6ab7187232174b6203c250da5142e7543ec757356f6d974`.
- FAMILIA / MCP local de editor: `Projetos-Arquivo/missions/outbox/GLOBAL_HOMOLOGATION/M_20261116_VIDEO_STUDIO_AI_CPE_MCP_052_READONLY_HOST_V1_receipt.json` — `LOCAL_MCP_READONLY_PASS`, oito ferramentas.
- CANAL DARK / CP33: `Projetos-Arquivo/missions/outbox/CANAL_DARK/M_20261116_CANAL_DARK_CP33_PROFESSIONAL_EVIDENCE_CASE_V1_receipt.json` — `CASE_TECHNICAL_PASS`, não prova dublagem comercial concluída.
- Semântica V6 / `render_original.py` e `qa_video_lote.py`: SOURCE e testes SANDBOX documentados em `biblioteca_semantica/README.md`; **o próprio módulo V6 ainda não tem prova de execução HOST**. NÃO emprestar a ele a homologação de outro editor.
- Qwen3-VL: candidato opcional, **HOST_INFERENCE_NOT_VERIFIED**. Uso real da ferramenta MCP pelo modelo Qwen também não comprovado; descoberta MCP não equivale a chamada.

**Fechamento de dependência:** `VISUAL_MODEL_NOT_HOMOLOGATED` deixa de bloquear a produção. Isso fecha somente o bloqueio de roteamento/documentação, não dispensa QA e renderização de cada vídeo nem permite declarar o vídeo do usuário pronto.

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

## Reconciliação de escopo — 17/11/2026
REA Video CP34/CP35 já operou no FAMILIA; CP35 processou clipe técnico de 7 s **sem VLM/OCR/ASR**. Isso prova `probe/decompose`, não Qwen3-VL interpretando o original Stellar Blade. A decupagem V5 do bruto é observação assistida de sandbox, não inferência local homologada. O MP4 R26.1 já existe e foi baixado do Drive; SHA bate com FAMILIA, mas QA de HDR PQ/BT.2020 e loudness -25,28 LUFS **reprovou** e houve rejeição editorial do proprietário. Ver [registro reconciliado](./HOMOLOGACAO_RECONCILIADA_20261117.md). Não gerar novamente voz nem reiniciar o worker R4.
