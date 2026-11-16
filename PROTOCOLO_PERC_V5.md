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
