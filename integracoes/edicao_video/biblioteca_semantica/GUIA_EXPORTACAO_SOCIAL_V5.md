# CASA Video Lab — Biblioteca de exportação social e correção V5

Data do piloto: 2026-11-16. Uso global e por projeto; dados de mídias e trabalhos continuam isolados no respectivo projeto.

## Auditoria que originou a regra

No piloto com originais de gameplay, a V4 gerava um vídeo YouTube WebM HDR/VP9 de quase 388 MB, Shorts com janela de gameplay de apenas 510/1280 px, metadados de cor inconsistentes, finalização interrompida antes do desfecho e uma sobreposição de notificação do console. A V5 corrigiu a exportação e a composição a partir dos **arquivos originais**.

A nova versão de YouTube foi entregue em MP4 H.264/AAC SDR BT.709 com `+faststart`, ~94,7 MB e 173,3 segundos. O Short de finalização passou a incluir a reação da personagem. Os quatro Shorts tiveram a imagem de gameplay ampliada e o trecho do Mickey foi recortado para omitir uma notificação sem reordenar o movimento.

**Evidência deste piloto:** seis MP4 gerados, decodificados integralmente, ffprobe executado, SHA-256 dos dois originais reconferido. Estes testes ocorreram apenas no SANDBOX da conversa, não no FAMILIA.

## Regras reutilizáveis de edição

1. **Fonte:** exclusivamente gravação original, com manifesto de identificação e SHA-256; nunca reusar um V2/V3/V4 exportado como matéria-prima editorial.
2. **Compreensão:** gerar índice **interno** de eventos e evidências por timestamp. Os textos de interpretação são apenas metadados, jamais legendas ou overlays.
3. **Narrativa:** manter preparação, ação e consequência observável. Nunca cortar antes do resultado ou inventar um resultado que o original não contém. Sem reversão de cronologia.
4. **Vertical:** definir enquadramento a partir da trajetória do personagem e objetivos relevantes, conferindo início/meio/fim. Reprovar o uso de uma faixa central minúscula cercada de fundos desfocados. Não esconder adversários importantes.
5. **HUD/notificações:** localizar notificações temporárias do sistema; avaliar recorte seguro que preserve personagem, HUD necessário e consequência. Não inserir emendas internas para ocultá-las.
6. **HDR:** distinguir PQ/BT.2020 10-bit de SDR/BT.709. Para exportação social SDR, aplicar **tone-mapping** real antes de H.264 8-bit; não apenas etiquetar HDR como SDR.
7. **Colorimetria:** depois da composição, usar `setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709` quando apropriado e flags `-color_primaries bt709 -color_trc bt709 -colorspace bt709` no encoder. Conferir o resultado com ffprobe; não assumir que a flag resolve por si.
8. **Download/reprodução:** priorizar MP4 H.264/AAC, `yuv420p`, `+faststart`; medir peso final, não só bitrate nominal. Não declarar que o usuário conseguiu baixar antes de teste real.
9. **Áudio:** preservar áudio sincronizado do trecho correspondente ao original; não substituir sons do jogo para disfarçar cortes e manter picos sob controle.
10. **Formato YouTube:** preservar orientação horizontal e a duração realmente existente; nunca duplicar um vídeo curto para fingir duração longa.

## Exemplo de HDR → SDR (validar no material real)

```bash
ffmpeg -i original_hdr.webm -vf "crop=1920:1080:0:4,zscale=w=1280:h=720:t=linear:npl=100,format=gbrpf32le,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:p=bt709:m=bt709:r=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709,fps=30" -c:v libx264 -crf 24 -preset veryfast -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 160k -movflags +faststart saida_sdr.mp4
```

O exemplo depende da resolução, flags originais e codecs disponíveis. **Não executar mecanicamente em outra gravação sem detectar perfil HDR e validar a imagem.**

## Qualidade e homologação

- Testar `ffprobe`: codec, FPS, resolução, duração, start time, faixa de cor, primárias e transferência.
- Fazer **decodificação integral** com `ffmpeg -v error -xerror -i arquivo.mp4 -f null -`.
- Revisar quadros e áudio no início, meio, clímax e desfecho; validar enquadramento de cada ação.
- Verificar hashes dos originais antes e depois; nunca apagar os originais.
- Armazenar relatório de cada exportação com `source_sha256`, IN/OUT, `output_sha256`, duração, tamanho, decisões de enquadramento, avisos e resultado dos testes.
- Separar estados `SOURCE`, `SANDBOX`, `CI`, `HOST_FAMILIA`, `DEVICE`, `PUBLICATION` e `RETENTION`. Não inferir um estado a partir de outro.
- Não executar tarefas residentes de vídeo ou instalar ferramentas no FAMILIA sem teste de hardware e controle de permissões.

## Evidências e limites conhecidos

- Piloto V5: **6/6** exports passaram em QA local de codec/decodificação.
- A auditoria visual usa revisão de quadros amostrados; não comprova percepção de todos os frames.
- Não houve teste real de download no navegador/dispositivo do usuário, publicação ou dados de retenção.
- Qwen3-VL segue como candidato para gerar automaticamente eventos; **nenhum modelo de compreensão de vídeo foi homologado no FAMILIA**.

Ver [motor semântico](../MOTOR_ENTENDIMENTO_VISUAL_V1.md), [regra de continuidade](../GUIA_EDITORIAL_CONTINUIDADE_V3.md) e [biblioteca_semantica](./README.md).
