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