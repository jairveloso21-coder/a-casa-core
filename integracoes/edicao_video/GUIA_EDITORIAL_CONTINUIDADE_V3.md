# CASA Video Lab — Manual editorial de continuidade V3

**2026-11-16 · Perfil: gameplays curtos para TikTok/Reels/Shorts · Insumo exclusivo: gravação original.**

## Erro identificado na V2

A V2 confundiu **impacto isolado** com **história**. Os trechos foram reordenados:
- Tekken: sete fragmentos intercalaram fontes diferentes, omitindo transições naturais.
- Zelda: a abertura saiu do segundo 157,8 e saltou de volta ao 113,1, recomeçando acontecimentos sem aviso.
- Boss: começou no 5,25, recuou a 0,65 e pulou cenas que explicavam o combate.

Isso causa desorientação e torna impossível antecipar a consequência de um golpe. A V3 adota sequência causal e orçamento de cortes.

## Método de edição — seis etapas

1. **Ingestão do bruto:** guardar nome, duração, fps, hash SHA-256, áudio e proporções. Se o arquivo tiver origem `V1`, `V2`, `export`, `short` ou vídeo recortado, **não usar** como fonte de montagem. Não alterar nem apagar o original.
2. **Decupagem sem cortes:** assistir ao material e anotar *contexto → antecipação → ação → desfecho*. Anotar os segundos IN e OUT antes de renderizar. Não selecionar apenas frames de maior pico visual.
3. **Estrutura causal:** um vídeo curto deve explicar visualmente quem age, o que faz e qual foi o resultado. O primeiro plano deve gerar uma pergunta natural; a conclusão deve entregar um resultado verdadeiro. Sem promessas de payoff inexistente.
4. **Continuidade:** cortar por mudança de assunto/cena, intervalo morto real ou entre lutas independentes. Nunca remover o percurso necessário a entender como o personagem chegou ao momento. Dentro de uma ação contínua, **corte zero** como padrão. Não retroceder o tempo da mesma gravação, salvo flashback claramente rotulado e justificado.
5. **Acabamento:** manter som original sincronizado (sem substituir golpes por sons aleatórios), correção leve de contraste e cor, 720×1280/30 fps para entrega social, H.264/AAC. Para luta, manter ambos os combatentes visíveis; para ação centralizada, corte vertical pode preencher a tela. No caso de perda de contexto por recorte vertical, usar janela horizontal nítida sobre fundo neutro desfocado; não aumentar a quantidade de cortes para disfarçar enquadramento.
6. **QA:** conferir edital de origem com hashes, cronologia, orçamento de cortes, continuação visual de golpes, HUD/legendas legíveis, áudio e duração, decodificação completa, além de visualização manual em tamanho de celular. Métricas de retenção só após publicação consentida.

## Critérios editoriais acionáveis

| Critério | Regra V3 | Reprovar quando |
|---|---|---|
| Fonte | Somente arquivo original referenciado por hash | Fonte é V2 ou derivado |
| Tempo | Sequência sempre crescente por fonte | Trecho posterior antecede cena anterior sem explicação |
| Tomadas | Preferir ≥8 segundos de ação contínua neste piloto | Muitos trechos de 1–3 s sem narrativa |
| Cortes | Zelda 0; Boss 0; Tekken 1 entre duas lutas | Corte interno corta animação ou resultado |
| Enquadramento | Personagem/objetivo principal ficam legíveis | HUD ou lutadores essenciais fora da tela |
| Audio | Áudio do mesmo trecho original, preservado | Som da finalização vem de outra cena |
| Texto | Apenas contexto e uma pergunta final | Legendas cobrindo ação, afirmação não demonstrada |
| Publicação | Dados reais após postagem | Alegar retenção provada só por análise offline |

## Projetos V3 — EDL selecionada dos originais

- **Tekken**: `20261110_093952_00312013.mp4` 0,30–12,90 s (combo 1), seguido de `20261110_154545_00477552.webm` 0,30–14,05 s (combo 2). Uma transição editorial entre lutas independentes; sem reordenação interna.
- **Zelda**: `20261116_172215_00032424.webm` 111,00–148,00 s. Escada, saída, salto e queda numa tomada contínua.
- **Boss**: `20261115_115257_00612931.webm` 0,15–14,87 s. Aproximação, luta, conclusão e cena final numa tomada contínua. Os quadros escuros entre 10–12 s aparecem no próprio original.

## Pilha de ferramentas (não confundir pesquisa com homologação)

- **FFmpeg / ffprobe:** processamento e inspeção; **testado apenas no sandbox da conversa**. Guia: https://ffmpeg.org/ffmpeg-filters.html
- **Pillow:** fundos desfocados estáticos e títulos, testado no sandbox.
- **OpenCV:** inspeção visual em lotes; presente no sandbox. Nenhum algoritmo de visão computacional para garantir continuidade foi homologado.
- **Kdenlive:** referência de edição profissional não-linear, recorte, ripple e 3-point; **pesquisado, não instalado no FAMILIA**. https://docs.kdenlive.org/pt_BR/cutting_and_assembling/editing.html
- **OpenTimelineIO:** candidato a esquema de EDL interoperável, **pesquisado, não instalado**. https://github.com/AcademySoftwareFoundation/OpenTimelineIO
- **PySceneDetect:** candidato para identificar fronteiras de cenas; **pesquisado, não instalado**. Detector automático **não substitui** julgamento de continuidade. https://www.scenedetect.com/docs/latest/
- **auto-editor:** não liberar cortes automáticos por silêncio/movimento em gameplay sem revisão, pois pode remover golpes e pausas narrativas.

## Homologação separada por domínio

- `SOURCE`: código e política só depois de commit e leitura do conteúdo remoto.
- `SANDBOX`: produzir MP4, ffprobe, decodificação integral, SHA e relatório; os artefatos gerados neste chat não comprovam notebook.
- `HOST FAMILIA`: precisa de comando, logs, hash, ambiente e recibo real do executor autorizado.
- `DEVICE`: playback físico, medição e aplicativo/plataforma identificados; pendente.
- `RETENTION`: métrica de retenção real da postagem, jamais inferida do vídeo.

**Sem permissões elevadas, serviços residentes ou alterações em Steam, ROMs, segredos e dados de outros projetos.**