# PROTOCOLO PERC v5.2 — WORKBENCH "A CASA"
1. **ALVO MOBILE (`AFTKM`):** Arquitetura estrita `armeabi-v7a` (Android 11).
   - Para binarios nativos em **Go** (sem NDK instalado): Compilar estaticamente com `set GOOS=linux&& set GOARCH=arm&& set GOARM=7&& set CGO_ENABLED=0&& go build -ldflags="-s -w"`.
   - Para APKs ou C/C++ com NDK: Executar via `wsl`.
2. **C/C++ E REVERSA:** Executar via `wsl` (Windows host nao possui GCC/Clang).
3. **FFMPEG:** Usar obrigatoriamente `-threads 8` e priorizar GPU (`-hwaccel auto` / `-c:v h264_nvenc`).
4. **ANTI-PREGUICA:** Proibido `TODO`, `FIXME`, `...` ou codigo identico ao anterior (SHA-256 deve mudar).
5. **FORMATO DE SAIDA QWEN:** Responder apenas JSON com `id_os`, `alvo`, `arquivo_destino`, `binario_gerado`, `melhorias_tecnicas`, `comando_build`, `comando_validacao`, `codigo_completo`.
