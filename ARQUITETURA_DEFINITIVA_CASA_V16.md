# ARQUITETURA DEFINITIVA — ECOSSISTEMA A CASA (V16.0 | CLOSED-LOOP)

## 1. TOPOLOGIA OPERACIONAL E FRONTEIRAS DE CONFIANÇA
O ecossistema opera sob o modelo **Zero-Trust & Fail-Closed**, dividido em 4 planos isolados:

1. **Plano de Decisão (L1 — Arquiteto ChatGPT):**
   - Interpreta o pedido do Proprietário (`jairveloso21-coder`), consulta o estado real no GitHub/Drive e emite planos fechados.
   - **Proibição Absoluta:** Nunca pede caminhos canônicos, nunca usa rotas aposentadas (`Forgejo`, `Desktop Commander`) e nunca invalida o sistema globalmente por falha pontual de um gate.
2. **Plano de Síntese (L2 — Qwen Code 0.27.3 + Ollama `127.0.0.1:11434`):**
   - Gera código completo e emite estritamente o contrato `OS_PERC` (v8.2), sem acesso a shell irrestrito.
3. **Plano de Governança & Roteamento (L3 — CASA Core & MCP Gateway):**
   - `casa-global-tools` (`stdio`, read-only): consulta o catálogo de 97 integrações.
   - `casa-core-gateway` (`stdio`, mutação tipada): valida `policy.json`, converte `OS_PERC` -> `CASA_MISSION_V2.1`, adquire lock exclusivo por projeto, grava no `journal.jsonl` com `idempotency_key` e despacha para `missions/inbox/<PROJETO>/`.
4. **Plano de Execução & Evidência (L4 — Host `FAMILIA`, Gitea `:3002` & Devices):**
   - **Strict Executor V2** executa a missão no alvo autorizado, roda o build/teste no **Gitea CI (`127.0.0.1:3002`)** e emite recibo JSON assinado com **SSHSIG + SHA-256** em `missions/outbox/<PROJETO>/`.

---

## 2. MATRIZ DE CAMINHOS, PORTAS E HARDWARE (IMUTÁVEL)

| Entidade | Identificador / Endereço Canônico | Restrição Física / Política |
| :--- | :--- | :--- |
| **Host Principal** | `FAMILIA` (`C:\CASA_HUB\02_REPOSITORIES`) | Win11 `x86_64` \| Meta SSD livre `>= 130 GiB` |
| **Repositório Regras** | `jairveloso21-coder/a-casa-core` | Contém `policy.json`, `PROTOCOLO_PERC_V5.md` (v8.2) |
| **Repositório Estado** | `jairveloso21-coder/Projetos-Arquivo` | Contém `CANONICAL_SYSTEM_STATE.json`, `missions/inbox` & `outbox` |
| **Camada 2 (WIP)** | Google Drive `/CASA_BANCADA_WIP` | Folder ID: `1sxbfhKTp1e3yDMLavtDXvIMMHAdJVjn3` |
| **Camada 3 (Acervo)** | Telegram `CASA_Mensageiro` | Exige QA aprovado + SHA-256 + Restore Test |
| **Inferência Local** | `http://127.0.0` | `Qwen2.5-Coder 7B` (primário) \| `0.5B` (fallback) |
| **Servidor CI Oficial** | `http://127.0.0.1:3002` (Gitea WSL) | Único CI válido. `Forgejo` e `Desktop Commander` = `410 GONE` |
| **Celular Garnet** | ADB Serial `b3a67583` (Android 16) | ABI exclusiva: `arm64-v8a` |
| **Fire TV Stick** | ADB TCP `192.168.1.108:5555` (Android 11) | ABI exclusiva: `armeabi-v7a` \| Exige `idle preflight` |
| **Console PS5 Slim** | Orbis OS (LAN) | Payloads `ELF` / GameFinder \| Proibido `.apk` |

---

## 3. ESCADA OFICIAL DE COMPROVAÇÃO (6 GATES SEQUENCIAIS)
Nenhuma entrega pode pular etapas nem herdar aprovação de nível inferior:

1. **`CANDIDATO`:** Item catalogado nos 97 IDs (apenas inventário).
2. **`SOURCE`:** Código/SKILL/YAML commitado no GitHub com SHA verificado.
3. **`CI`:** Pipeline executado no Gitea (`:3002`) no SHA exato com `CI_RUN_ID` registrado.
4. **`HOST`:** Executado/compilado no `FAMILIA` com `exit_code == 0` + recibo `SSHSIG` + `SHA-256`.
5. **`DEVICE`:** Instalado e validado em hardware real (`pidof`, playback, estabilidade) no serial pinado.
6. **`EDITORIAL`:** Mídia/produto validado tecnicamente (`SDR/BT.709`, `-14 LUFS`, QoE) e arquivado com teste de restauração.

---

## 4. RAMIFICAÇÃO ISOLADA DOS 18 PROJETOS
Cada projeto possui namespace, branch, fila (`inbox`/`outbox`) e segredos estritamente separados:
1. `CASA_Core` (`a-casa-core` \| `main`)
2. `CASA_LAB` (`Projetos-Arquivo` \| `main`)
3. `Motor-Forge-Lya` (`main`)
4. `Autonomy-Control` (`main`)
5. `RetroCloud` (`RetroCloud_` \| `main`)
6. `RCRE` (`main`)
7. `Buscar_Inter` (`buscar-inter-browser` \| `main`)
8. `IPFLIX` (`fix/ipflix-v9-2-qa-contract-20261115`)
9. `Achadinhos_Promos` (`main`)
10. `ConsoleNativeLab` (`main`)
11. `Minha_Vida` (`private/cursor-isolated` — isolamento total de dados pessoais)
12. `Ap_801_Reserva_Blumenau` (`main`)
13. `Canal-Dark-CASA-LAB` (`main`)
14. `Casa-Remote-Next` (`main`)
15. `CASA_Webhook_Gateway` (`main`)
16. `Origin_Intelligence` (`main`)
17. `RetroCloud_V1` (`main`)
18. `MINHAS_FINANCAS` (`feat/minhas-financas-blueprint-20261102`)
