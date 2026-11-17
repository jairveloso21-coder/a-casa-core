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
