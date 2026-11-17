# CASA Video Lab — Reconciliação de homologações (17/11/2026)

**Tipo de alteração:** correção de governança e roteamento de evidências, não execução física ou homologação de novos modelos. Prova precisa ser específica de artefato, versão, host, operação e projeto. Não copiar dados ou WAVs de Stellar Blade para esta biblioteca global.

## Estados positivos que NÃO devem ser descartados

- **REA Video CP34:** probe real de mídia técnica no FAMILIA, usando fonte pinada; recibo: `Projetos-Arquivo/missions/outbox/CANAL_DARK/M_20261116_CANAL_DARK_CP34_REA_PINNED_READONLY_PROBE_V1_receipt.json`.
- **REA Video CP35:** decomposição real da mídia técnica `CP30_QWEN_EDGE_CADU_NARRATED_TECH_ONLY.mp4`, 7 s, com `--no-vlm --no-ocr`, sem ASR; recibo: `Projetos-Arquivo/missions/outbox/CANAL_DARK/M_20261116_CANAL_DARK_CP35_REA_DECOMPOSE_REAL_MEDIA_V1_receipt.json`. **Não é reconhecimento semântico de Stellar Blade.**
- **FFmpeg:** versão 9.0.2 reportada em execução no FAMILIA no recibo de inventário Video Studio CPA. Isso comprova a ferramenta naquela operação, não um render do original com R26.1.
- **REA, biblioteca editorial e editor MakeMyClip:** testes isolados já registrados no `CANONICAL_SYSTEM_STATE.json#video_studio_ai_global_checkpoint`. Nenhum desses resultados constitui evento Qwen MCP `tool_use` ou vídeo de Stellar Blade final.
- **Stellar Blade V5:** já existe decupagem de observação assistida no sandbox (`DECUPAGEM_INTERNA_V5.json`, `AUDITORIA_EDITORIAL_V5.md`). Fonte `20261116_182602_00670977.webm`, SHA-256 `5678a1b033a815a90b97c615e5d87fba3afe6e74275146310bbfb426df5fb5b5`; marcos ~6, 23, 60, 120, 154, 168 e 175 segundos. **Não descartar/reinventar essas marcações.**
- **Voz Eve R26.1:** biblioteca de cinco WAVs aprovada artisticamente no Drive e preservada, ZIP SHA-256 `ceb3df3383276149bb8663df3a5f50566bd596fbae61557e9f25b556c8eeb34a`; registro `Projetos-Arquivo/chatgpt-ops/operational/voice-library/CANAL_DARK_R26_1_LOCK.json`. SSHSIG do arquivo de biblioteca ainda pendente no registro; não regenerar a voz.
- **Renderizador e QA V6:** `biblioteca_semantica/render_original.py` e `qa_video_lote.py` executaram provas no sandbox; seus estados **HOST FAMILIA** e **CI** permanecem pendentes na versão atual.

## Falsos positivos proibidos

1. `HOMOLOGATED_AND_LOCKED` do baseline global não é `ALL_PROJECTS_COMPLETE`. Conferir o registro de reconciliação por projeto antes de mostrar “homologado”.
2. CP35 `REAL_REA_DECOMPOSE_PASS` não implica VLM, leitura real de eventos, ASR ou análise do vídeo original.
3. O motor `MOTOR_ENTENDIMENTO_VISUAL_V1.md` continua uma especificação de inferência; instalar, benchmarkar e observar em vídeo real antes de promover o gate HOST.
4. R26.1 `AUDIO_APPROVED` não implica narração sincronizada ou MP4 pronto. A prévia com vozes-guia eSpeak também não é a biblioteca final.
5. Um MP4 de demonstração ou uma gravação derivada não é automaticamente o WebM original, mesmo tendo checksum válido.
6. `SOURCE` + recibo textual `SUCCESS` não comprovam assinatura SSHSIG, CI, execução no FAMILIA, playback ou aceitação editorial.

## Rota já existente e aceite do vídeo original

`20261116_182602_00670977.webm` **bruto** + SHA-256 real → decupagem V5 como referência privada + inspeção de quadros reais no FAMILIA → roteiro causal por timecode sem inventar ações → WAV `eve-original-R26-REFINADA.wav` do arquivo R26.1 intacto → mixagem/dinamização do áudio original e narração com FFmpeg → `render_original.py` ou renderizador do Video Studio versionado → `qa_video_lote.py` + QA editorial → MP4 final com hash + recibo SSHSIG válido. O renderizador V6 atual **não** recebe a R26.1 como faixa adicional; sua integração precisa ser implementada e testada, sem afirmar funcionalidade inexistente.

**Antes de operar:** localizar fisicamente bruto e WAV, comparar hashes, ler o checkpoint exato da missão/worker para evitar replay, verificar disco e chave de assinatura. Se já existe render em curso, consultar o resultado, não iniciar outra síntese ou transcoding. Proteger original, APKs e dados de outros projetos; saída somente em `Meu Drive/CASA_BANCADA_WIP/CANAL_DARK/`.

**Fechamento completo:** demonstrar separadamente SOURCE commit, CI run real, HOST logs/artefatos/versionamento/SHA/SSHSIG independente, QA audiovisual e, quando exigido, teste de reprodução em DEVICE. Se algum gate falhar, mantê-lo explicitamente ABERTO e recuperar a rota existente antes de criar serviço novo.

## Fontes canônicas

- `Projetos-Arquivo/CANONICAL_SYSTEM_STATE.json#homologation_scope_reconciliation_20261117`.
- `Projetos-Arquivo/chatgpt-ops/operational/homologation/CASA_HOMOLOGATION_RECONCILIATION_20261117.json`.
- `Projetos-Arquivo/chatgpt-ops/operational/tools/casa-evidence-gate-v1/casa_homologation_reconcile.py`.
- `a-casa-core/integracoes/edicao_video/biblioteca_semantica/manifest.json#homologation_reconciliation_20261117`.

**Estado em 17/11:** correção do registro em SOURCE; o vídeo final de Stellar Blade ainda NÃO está atestado, e essa publicação não é prova de execução no FAMILIA.
