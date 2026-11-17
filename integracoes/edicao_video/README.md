<!-- CASA_EXECUTABLE_QA_V6 -->
## QA reutilizável de lote V6

A [biblioteca semântica](./biblioteca_semantica/README.md) agora inclui [qa_video_lote.py](./biblioteca_semantica/qa_video_lote.py), um validador reutilizável de vídeo, áudio, hashes e continuidade dos Shorts, executado em um piloto real no sandbox. O [manual V6](./biblioteca_semantica/QA_EXECUTAVEL_V6.md) e o [manifesto](./biblioteca_semantica/manifest.json) distinguem SOURCE/SANDBOX de CI/HOST/DEVICE. Nenhuma homologação física do FAMILIA foi alegada.

<!-- CASA_VIDEO_EXPORT_V5 -->
## Correção de exportação V5

A [biblioteca semântica / guia de exportação V5](./biblioteca_semantica/GUIA_EXPORTACAO_SOCIAL_V5.md) acrescenta regras de reenquadramento vertical, controle de notificações, continuidade de finalizações, conversão HDR→SDR com metadados BT.709 e arquivo MP4 H.264/AAC otimizado para download. Evidência: 6 exports localmente decodificados no sandbox; HOST/DEVICE não testados.

<!-- CASA_SEMANTIC_VIDEO_LIBRARY_V1 -->
## Biblioteca global de decupagem semântica v1.0

A nova [biblioteca_semantica](./biblioteca_semantica/README.md) padroniza anotações **textuais internas** de ações e resultados da gravação ORIGINAL, valida continuidade/causalidade e gera uma EDL proposta sem sobrepor o texto na imagem. Contém [código Python](./biblioteca_semantica/semantic_timeline.py), [contrato JSON](./biblioteca_semantica/schema.json), [testes de regressão](./biblioteca_semantica/tests/test_semantic_timeline.py), [skill-fonte](./biblioteca_semantica/SKILL.md) e [registro de estado](./biblioteca_semantica/manifest.json).

**Gates:** SOURCE publicado e relido; testes do código, CI, instalação no FAMILIA e integração a um modelo visual real ainda NÃO comprovados. A biblioteca não integra automaticamente Qwen3-VL ou FFmpeg e não é uma skill instalada no host.

<!-- MOTOR_SEMANTICO_INTERNO_V1 -->
## Motor de compreensão semântica — proposta V1

**Regra:** a leitura da gravação original gera uma linha do tempo **interna, textual e privada** de eventos com timestamps e níveis de confiança antes da escolha dos cortes. Ela nunca é exibida como legenda ou sobreposição no render.

Consulte [MOTOR_ENTENDIMENTO_VISUAL_V1.md](./MOTOR_ENTENDIMENTO_VISUAL_V1.md) para contrato, ferramentas candidatas e gates de validação. O documento existe no SOURCE; Qwen3-VL e whisper.cpp **não foram instalados nem homologados no HOST FAMILIA**. Exemplo com dados reais de gameplay mantido apenas no ambiente privado da conversa, fora do repositório público.

<!-- CASA_VIDEO_V3_CONTINUIDADE -->
## Regra prioritária desde V3 (16/11/2026)

**Editar sempre o arquivo bruto ORIGINAL**, identificado por nome e SHA-256. Não utilizar renders de versões anteriores como matéria-prima, não inverter a cronologia de uma sequência, não cortar dentro de um golpe ou salto e não confundir velocidade de montagem com qualidade editorial.

- [Manual de narrativa, decupagem e continuidade V3](./GUIA_EDITORIAL_CONTINUIDADE_V3.md)
- [Catálogo e estado de verificação V3](./CATALOGO_VIDEO_CONTINUIDADE_V3.json)

**Evidência V3:** três MP4s produzidos dos arquivos originais e 33/33 verificações automáticas no sandbox. **Pendente:** HOST FAMILIA, dispositivos e retenção após publicação. As regras V3 têm precedência editorial sobre a montagem V2; preservar os arquivos V2 para auditoria histórica.

---

# CASA Video Lab V2 — biblioteca de edição de gameplay

**Edição:** 2026-11-16 · **Alvo:** cortes verticais para Reels, TikTok e Shorts.

## Estado real da homologação

- SOURCE: pipeline e catálogo disponíveis para revisão; publicação no GitHub indicada separadamente.
- SANDBOX: FFmpeg 7.1.5, OpenCV 4.13.0 e Pillow 12.3.0 verificados; 3 vídeos renderizados do original, decodificados integralmente e auditados por quadros.
- HOST FAMILIA / WSL / GPU MX250: **não testados**; nenhuma instalação ou serviço adicionado ao host.
- GARNED / FIRESTICK / redes sociais: **não testados**; nenhuma publicação nem playback físico.
- PySceneDetect v0.7.3: pesquisado, porém a instalação pelo índice local falhou; não está homologado.
- Auto-Editor, hEditor, Reframe, OpenTimelineIO: candidatos pesquisados, não instalados nem homologados.

## O que mudou

1. Seleção editorial sobre gravação bruta, não recompilação dos vídeos antigos.
2. Tecnicamente, os planos de luta passam por uma janela mais ampla com foco nos lutadores; Zelda alterna campo amplo e recorte vertical, com correção manual do eixo do personagem.
3. Enquadramento com preenchimento de fundo derivado das imagens, eliminando barras totalmente pretas geradas pela composição anterior.
4. Texto de abertura em 1–2 segundos e convite para comentar só ao final.
5. Audio-fades de milissegundos nas emendas, compressor e normalização de loudness.
6. Capas verticais, legendas para postagem e manifesto por sequência com SHA-256.

## Pipeline e dependências

Requer `python3`, `Pillow`, `ffmpeg`, `ffprobe`, uma fonte TTF instalada. Em Linux/WSL, teste a disponibilidade com `python3 -c 'from PIL import Image'` e `ffmpeg -version`.

Uso em ambiente isolado:
```bash
export CASA_VIDEO_SOURCE_DIR="/caminho/para/as/gravações"
export CASA_VIDEO_OUTPUT_DIR="/caminho/para/WIP/casa_video_v2"
python3 casa_video_lab_v2.py all
```

O código carrega os nomes de fonte indicados no dicionário `SOURCES` e as decisões editoriais em `STORIES`. Para outras gravações, altere a matriz de fontes e as seções antes de executar. Nunca reescreva os originais; a saída vai somente a `CASA_VIDEO_OUTPUT_DIR`, que deve ser diferente da pasta de originais.

**Preservação:** não mover/apagar material original, ROMs, Steam, segredos ou conteúdo de outros projetos. Use saída em WIP; publicação e limpeza só após recibo e retenção segura. Não habilitar UAC/ACL bypass ou serviços residentes.

## Checklist de homologação FAMILIA (a executar pelo executor autenticado)

- Resolver o caminho WSL e verificar hashes dos arquivos originais antes do primeiro processamento.
- Verificar executáveis, versão, font e filtros `drawtext`, `loudnorm`, `boxblur`.
- Executar a edição local, confrontar `source_segments`, codec, fps, duração, áudio, decodificação integral e SHA-256.
- Medir consumo de CPU/RAM/disk durante a execução, inclusive custo na MX250 se a codificação NVENC for aprovada em rodada posterior.
- Produzir recibo do host com comando, exit-code, sha256, logs e assinatura real; diferenciar SOURCE, CI, HOST e DEVICE.
- Fazer revisão visual de quadros, engajamento em teste A/B depois da postagem, apenas com autorização. Não declarar retenção comprovada sem dados.

## Limites conhecidos

- Não há algoritmo de seleção de cenas treinado/homologado. As cenas deste piloto foram escolhidas após inspeção visual.
- Não se instalou PySceneDetect no sandbox: índice de pacotes não forneceu a versão pesquisada.
- Não há avaliação real de retenção; roteiros são hipóteses editoriais.
- A edição foi exportada a 720 × 1280 / 30 fps (H.264/AAC); 1080 × 1920 seria uma etapa adicional, não presumida.
- Áudio musical externo não foi adicionado.

## Arquivos de entrega

`TEKKEN8_V2_DOIS_COMBOS.mp4`, `ZELDA_V2_SALTO_SEM_FIM.mp4`, `BOSS_V2_REPLAY_FINAL.mp4`, `*_CAPA.png`, `LEGENDAS_POSTAGEM.md`, `RELATORIO_QA_V2.json`, `CATALOGO_FERRAMENTAS_VIDEO_V2.json`, `casa_video_lab_v2.py`.

## Pesquisa open source de referência

- [FFmpeg](https://github.com/FFmpeg/FFmpeg)
- [OpenCV](https://github.com/opencv/opencv)
- [Pillow](https://github.com/python-pillow/Pillow)
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect)
- [auto-editor](https://github.com/WyattBlue/auto-editor)
- [hEditor](https://github.com/pycodebr/heditor)
- [Reframe](https://github.com/Prekzursil/Reframe)
- [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO)

**Status explícito:** estar catalogado não significa estar instalado nem homologado no FAMILIA.