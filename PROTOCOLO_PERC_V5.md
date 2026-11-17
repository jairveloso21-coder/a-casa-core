# PROTOCOLO PERC v8.2 — WORKBENCH "A CASA"

## 1. DISPOSITIVOS DO WORKBENCH (PROIBIDO CONFUNDIR)
- **NOTEBOOK (`WIN_HOST` / `WSL_LINUX`):** Windows 11 64-bit | Intel i5-10210U (8 Threads) | NVIDIA MX250 | WSL 2.
- **CELULAR PRINCIPAL (`CELULAR_GARNED`):** Dispositivo mobile oficial (`garned`). Use sempre `adb -s <serial_garned>` para deploy/testes mobile.
- **FIRE TV STICK (`FIRESTICK_AFTKM`):** Dispositivo de TV (`AFTKM`, Android 11, `armeabi-v7a`). Nunca envie builds de celular para o AFTKM sem ordem explicita.

## 2. REGRAS DE COMPILACAO E FERRAMENTAS
1. **Go Estatico para Android/ARM:**
   - Para `armeabi-v7a` (32-bit): `set GOOS=linux&& set GOARCH=arm&& set GOARM=7&& set CGO_ENABLED=0&& go build -ldflags="-s -w"`
   - Para `arm64-v8a` (64-bit): `set GOOS=linux&& set GOARCH=arm64&& set CGO_ENABLED=0&& go build -ldflags="-s -w"`
2. **C / C++ / Radare2 / Apktool:** Executar via `wsl`.
3. **FFmpeg (Video):** Usar `-threads 8` e priorizar GPU (`-hwaccel auto` / `-c:v h264_nvenc`).
4. **Anti-Preguica e Anti-Clone:** Proibido `TODO`, `FIXME`, `...` ou devolver codigo com hash SHA-256 identico ao anterior.

## 3. CONTRATO JSON DE SAIDA DA QWEN
Responder apenas JSON com: `id_os`, `alvo` (`WIN_HOST | WSL_LINUX | CELULAR_GARNED | FIRESTICK_AFTKM`), `arquivo_destino`, `binario_gerado`, `melhorias_tecnicas`, `comando_build`, `comando_validacao`, `codigo_completo`.

## 4. GATE AUDIOVISUAL GLOBAL (17/11/2026)
1. **Plataforma antes do export:** video curto e `9:16` nao identificam destino. Confirmar plataforma de publicacao (YouTube Shorts, Reels, TikTok, YouTube horizontal etc.), formato, specs oficiais e aprovacao do responsavel. Sem plataforma, produzir somente preview no formato original e marcar `PLATFORM_NOT_SELECTED`; nunca `POST_READY`.
2. **Voz humana homologada:** vincular WAV de referencia e SHA-256. Reusar descricao de voz ou argumento `language=Portuguese` nao prova timbre nem sotaque pt-BR. Antes da composicao, exigir A/B auditiva com referencia, sotaque brasileiro, naturalidade, pronuncia e provas de preservacao; falha `VOICE_IDENTITY_AB_NOT_APPROVED` ou `ACCENT_PT_BR_NOT_APPROVED` reprova render editorial.
3. **Narracao ao longo das cenas:** texto por timecode e evento observado; inicio, meio e fim quando o escopo exige comentario ao longo do combate. Proibido posicionar voz por `duracao_total - duracao_da_fala - 3` ou gerar bloco unico no encerramento. Falha `NARRATION_ALL_AT_END` ou `NARRATION_NOT_DISTRIBUTED` bloqueia aceite.
4. **Distinguir gates:** `SOURCE / CI / HOST / DEVICE / EDITORIAL / PUBLICACAO`. Um MP4 H.264/AAC decodificado integralmente e hash validado nao comprova naturalidade, coerencia narrativa nem postagem. Conservar candidato reprovado para auditoria, nao publicar e nao reiniciar sintese de efeito incerto.
5. **Pré-voo obrigatório de execução (V2.1):** após definir a plataforma e revisar cada WAV, executar `casa_video_release_gate_v2.py --phase pre_render --evidence <job.json>` com as falas distribuídas por timecodes de cenas. `PREFLIGHT_BLOCKED` ou exit 2 proíbe render FINAL e postagem. Após export, executar `--phase release` com codec, hash, full decode, audio sync, revisao PT-BR, direitos e aceite editorial. O FAMILIA passou 18/18 testes; a R4 foi rejeitada pelo próprio validador. O teste de lógica não substitui teste do vídeo novo.
6. **Implementacao vinculada:** `jairveloso21-coder/Projetos-Arquivo/chatgpt-ops/skills/casa-video-studio-ai/SKILL.md` e `chatgpt-ops/operational/tools/casa-video-studio-ai/casa_video_release_gate_v2.py`. Este gate e transversal e nao substitui o executor tipado local nem autoriza ferramentas pagas.

## V2.2 — Escolha de plataforma por VÍDEO (não por canal)

- Manter **todos os destinos e formatos** no catálogo da CASA; nenhuma plataforma é padrão global do Canal Dark, da CASA ou de qualquer projeto. A cada **novo vídeo**, recuperar o destino explicitamente escolhido pelo proprietário *para aquele arquivo*; perguntar somente quando ausente. Se o usuário já escolheu na conversa para o vídeo atual, registrar e **não perguntar novamente**.
- A decisão operacional carrega `platform`, `selection_scope=per_video`, `selection_media_sha256`, `selection_evidence`, `profile_id`, `official_spec_url`, `official_spec_checked_on`, `output_aspect`, `resolution` e `fps`. Proibido copiar `target_platform` para uma preferência global ou herdar o formato de outro arquivo: o validador exige hash do original e falha com `PLATFORM_DECISION_NOT_VIDEO_SCOPED`.
- YouTube **vídeo tradicional** e YouTube **Shorts** são destinos independentes mesmo dentro do YouTube. A decisão atual para **Eve contra Gigas / Stellar Blade** é **YouTube tradicional, 16:9 horizontal, MP4 1920×1080, H.264/AAC-LC 48 kHz, ~59,94 fps de origem**, preservando sequência e efeitos. O original `20261116_182602_00670977.webm` possui 1920×1088; reenquadramento técnico para 1920×1080 requer crop vertical de apenas 8 pixels, validando HUD e safe areas. **Esta é uma decisão exclusiva do vídeo atual, não uma configuração persistente global.**
- Especificações oficiais consultadas em 17/11/2026: `https://support.google.com/youtube/answer/1722171?hl=pt-BR` e `https://support.google.com/youtube/answer/6375112?hl=en`. Não definir uma duração máxima inventada para vídeo tradicional; Youtube classifica vídeos verticais/quadrados até três minutos como Shorts sob regras vigentes, por isso 16:9 é necessário para o vídeo tradicional atual.
- A dublagem da Eve R26.1 exige clonar/condicionar ao WAV real (SHA-256 `d7126b72315fc832970d3249537f63ea43524291d67bc4c680a043da8320d34a`) **somente em motor que realmente consuma `ref_audio`**, como Qwen3-TTS Base `generate_voice_clone` após verificar instalação/licença; o VoiceDesign antigo não consome `ref_audio`. Audição piloto A/B PT-BR obrigatória antes de sintetizar tudo. Falas por timecode em início, meio e fim do combate; não inferir vitória sem quadro do desfecho.
- Registrar a plataforma no projeto específico e QA SOURCE/HOST/EDITORIAL; se não houve nova geração e render comprovados, manter `EDITORIAL_REJECTED_NOT_POST_READY` para a R4. Nenhum upload/publicação automática.

