<!-- CASA_ORIGINAL_RENDERER_V6 -->
## Integração de renderização original-only e QA V6

1. Verificar SHA-256 físico de gravações originais; rejeitar qualquer arquivo V1/V2/V5 exportado como fonte.
2. Produzir descrições de cenas em JSON interno com timestamps; jamais queimar essas descrições no vídeo.
3. Selecionar sequências completas, causa/ação/consequência e enquadramento que preserve protagonista e objetivo.
4. Executar `render_original.py` com manifesto de fonte, intervalos e crop explícito; salvar só em WIP separado.
5. Usar `qa_video_lote.py` para verificar hashes, H.264/AAC, BT.709, duração, loudness/true peak, sobreposição dos Shorts e decodificação integral.
6. Tratar HDR como situação especial que exige pipeline explícito e validado; não fingir SDR mudando apenas etiquetas.
7. Entregar recibos SOURCE/SANDBOX/CI/HOST/DEVICE separadamente. Publicação/retention exige evidência real.

# Skill: CASA Semantic Video Decoupage v1.0

**Estado por capacidade (reconciliado 2026-11-17):** a Skill `semantic_timeline.py` específica permanece SOURCE (instalação independente no FAMILIA não demonstrada); **a edição de vídeo da CASA não está bloqueada**: REA Video teve decomposição real no FAMILIA (CP35), MakeMyClip 0.5.2 teve renderização técnica com decodificação integral (CPD) e seu MCP local de leitura foi testado (CPE). Estes recibos não comprovam instalação física desta Skill nem uso do Qwen3-VL.

**Regra de despacho anti-bloqueio:** não exigir Qwen3-VL para continuar uma edição. Se a inferência visual automática não estiver instalada, usar REA Video para decomposição, inspeção de quadros acessíveis e marcação conservadora de eventos observados; produzir montagem via editor/FFmpeg operacional já comprovado, finalizar com QA real. Se não houver acesso aos quadros, manter o produto como `NEEDS_VISUAL_REVIEW` em vez de inventar a cena, e buscar uma rota autorizada de acesso à mídia. Não reiniciar downloads, não duplicar bibliotecas ou exigir contratação externa.

**Evidência:** `../MOTOR_ENTENDIMENTO_VISUAL_V1.md` e recibos `Projetos-Arquivo/missions/outbox/CANAL_DARK/M_20261116_CANAL_DARK_CP35_REA_DECOMPOSE_REAL_MEDIA_V1_receipt.json`, `Projetos-Arquivo/missions/outbox/GLOBAL_HOMOLOGATION/M_20261116_VIDEO_STUDIO_AI_CPD_MAKEMYCLIP_052_PARALLEL_AB_V1_receipt.json` e `M_20261116_VIDEO_STUDIO_AI_CPE_MCP_052_READONLY_HOST_V1_receipt.json`. **Rota de edição habilitada; homologação do modelo visual opcional e da própria Skill não presumida.**

## When to use
Every CASA project producing short videos from raw recordings, when the user wants smooth, engaging editing without jump cuts or false narratives.

## Invariants
- Only original recording(s) backed by source manifest and SHA-256.
- No re-edit of previous exports, no deletion/alteration of the original.
- Build private text events with precise time ranges and confidence **before** choosing shots.
- Sequence event chain: setup → action → observed consequence. If the payoff is absent, state absent; never invent one.
- One story continuity first; cuts only at meaningful boundaries. Separate fights/scenes explicitly.
- Event descriptions and analysis text **MUST NOT** be burned into the video or exported as subtitles.
- Models provide suggestions, not definitive observation; uncertain descriptions require human/visual review.

## Standard workflow
1. Inventory originals: unique source IDs, path, SHA-256 and duration (actual file verification required).
2. Watch and describe **what can be seen**; create `events` with observed evidence timestamps.
3. Mark low-information sequences, occlusion, black frames, loading and pauses as candidates for review, not automatic removal.
4. Build `shots` while preserving event order and all dependencies.
5. Validate with `semantic_timeline.py validate` including `--source-root` when original bytes available.
6. Generate an EDL suggestion with `semantic_timeline.py edl`; editorial review before independent renderer.
7. QA actual exported MP4 for continuity, framing, synchronized original audio and no injected event descriptions.
8. Report SOURCE/CI/HOST/DEVICE evidence separately; do not claim increased retention without platform metrics.

## Data contract
Refer to [schema.json](./schema.json) and [README.md](./README.md). Text fields are **for internal planning only**. The EDL exporter deliberately omits `description_pt`.

## Failure handling
Reject: derivative source, SHA mismatch, missing causal predecessor, reverse chronological cut in same recording, truncated action, `render_as_overlay=true`, unknown event, source change without reason, out-of-range timestamps. No background continuous agent/process required.
