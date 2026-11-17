# CASA Video Lab — Narração de personagem e mixagem V1

**Edição:** 2026-11-17. **Escopo:** biblioteca global reutilizável, não instalação no FAMILIA.

## Objetivo
Criar dublagem ou comentário em primeira pessoa **sobre uma gravação original**. O texto de análise visual continua privado; só as frases de narração aprovadas entram na **faixa de áudio**, nunca automaticamente como legendas no vídeo.

## Contrato editorial
- Ler a captura bruta e confirmar hash SHA-256 e duração antes de escolher o trecho.
- Decupar cenas em preparação, ação, consequência e reação final, guardando timecodes dos acontecimentos observados. Sem editar a partir de exportações anteriores.
- Escrever falas próprias que acompanhem os acontecimentos visíveis. Nunca atribuir ao roteiro de um jogo falas que são uma criação de fã.
- Para voz nova, usar uma voz original ou autorizada. Não presumir permissão para clonar voz de atriz ou personagem a partir de jogo comercial.
- Gerar cada fala em áudio separado com timestamp, texto, direção vocal e SHA-256. A voz não deve ser inserida antes de existir arquivo gerado verificável.
- **Mixar** a trilha original da gravação com a dublagem através de ganho e ducking, evitando esconder golpes, alertas e efeitos essenciais. Checar cada início/fim de fala e evitar sobreposição indesejada.
- Exportar em MP4 H.264/AAC com `+faststart`, conversão HDR→SDR por tone-mapping real quando necessário, metadados corretos BT.709 e áudio integrado auditado.
- QA físico: decodificação integral, codecs, cor, duração, volume/true peak, cinco checkpoints visuais no mínimo e hashes de fonte/destino. Distribuição/retention apenas após testes reais.

## Arquitetura reutilizável

1. `semantic_events.json` (privado) — descrição do que acontece, causa e consequência.
2. `voice_script.json` (privado) — at, text, tone, voice_id autorizado, idioma e contexto; **não vai para vídeo**.
3. `voice_stems/*.wav` — sínteses independentes, sem cópia dos sons do jogo.
4. `voiceover_mix.wav` — linhas posicionadas nos segundos corretos; trilha original mixada posteriormente.
5. `social_output.mp4` — vídeo final sem sobreposição da descrição semântica.
6. `audio_qa.json` — provenance, SHA-256, codecs, loudness, true peak, pass/fail.

## ElevenLabs — integração

O serviço dispõe de Text-to-Speech com vozes geradas, selecionadas ou autorizadas e de MCP hospedado com OAuth em `https://api.elevenlabs.io/v1/mcp`. O MCP local antigo foi arquivado em agosto de 2026; priorizar a versão hospedada e autenticação por OAuth. **Nesta sessão não havia ElevenLabs conectado; não marcar a geração real no Labs como concluída.**

- https://elevenlabs.io/docs/overview/capabilities/text-to-speech
- https://elevenlabs.io/docs/eleven-api/resources/mcp-server

Voice Design é preferível a clonagem não autorizada quando o pedido for uma voz original de personagem com atitude parecida.

## Piloto SANDBOX, sem inferir sucesso do HOST

No piloto Stellar Blade, foi preparada uma narração experimental de 5 falas em 55,4 s a partir de trecho contínuo de captura original. A voz foi sintetizada localmente por eSpeak pt-br feminina, **não** pelo ElevenLabs e **não** como voz autêntica de Eve. O MP4 entregue teve H.264 1280×720 30 fps BT.709, AAC 48 kHz, decode completo PASS, aproximadamente −15,3 LUFS e true peak −2,7 dBFS. O original foi preservado.

- **SOURCE:** guia criado e relido no GitHub.
- **SANDBOX:** síntese local provisória, montagem, render e QA PASS.
- **ELEVENLABS:** não conectado, sem produção.
- **CI / HOST FAMILIA / DEVICE / PUBLICAÇÃO:** não testados.

A melhoria real esperada do ElevenLabs depende de acesso conectado e de voz autorizada. Não substituir o status de testes por promessas.
