<!-- CASA_ORIGINAL_RENDERER_V6 -->
## Renderizador reutilizável a partir do original (V6)

O módulo [render_original.py](./render_original.py) recebe JSON com `schema_version="casa.video.render/1.0"`, `sources` e `jobs`, exige SHA-256 dos arquivos originais e produz MP4 H.264/AAC com loudnorm. O crop vertical é uma escolha explícita por cena, e o módulo não desenha nenhum texto semântico na imagem.

Uso: `python render_original.py config.json --sources-root /originais --exports-root /WIP --manifest /WIP/manifest_qa.json`

Para um Short, o job informa `source_id`, `file`, `in_seconds`, `out_seconds`, `format="short"` e `crop={"x":0,"y":0,"w":608,"h":1080}` ajustado à gravação real. Para YouTube, `format="youtube_horizontal"`. O source informa `id`, `file`, `sha256`, `origin="raw_capture"`.

**Não usar os números de exemplo como configurações do usuário.** Requer inspecionar o conteúdo e escolher enquadramento que preserve a ação. O renderer recusa HDR sem transformação explícita, não altera nem sobrescreve originais e não monta automaticamente uma história por IA. Sempre executar [qa_video_lote.py](./qa_video_lote.py) depois da renderização.

**Evidência:** 11 testes unitários passaram no sandbox; um MP4 de 2 segundos foi produzido e aprovado no QA integral. O processo de renderização dessa prova excedeu o tempo limite antes de escrever o manifesto; a validação do MP4 foi refeita separadamente. CI, HOST FAMILIA e DEVICE não testados.

<!-- CASA_EXECUTABLE_QA_V6 -->
## Biblioteca V6 executável — auditoria de lote

[qa_video_lote.py](./qa_video_lote.py) é a biblioteca de **QA executável e somente leitura**: confere hashes dos originais, hashes das saídas, codec, BT.709, duração, loudness integrado/true peak, sobreposição dos dois Shorts e decodificação integral. [Oito testes de regressão](./tests/test_qa_video_lote.py) passaram no sandbox; [3/3 mídias reais V6](./QA_EXECUTAVEL_V6.md) passaram na auditoria. O módulo não edita, não infere eventos e não adiciona textos à imagem. Qwen3-VL e integração automática com editores continuam não homologados.

<!-- CASA_AUDIO_QA_V6 -->
## Gate de áudio e duração narrativa (V6)

[QA_AUDIO_SOCIAL_V6.md](./QA_AUDIO_SOCIAL_V6.md) — acrescenta medição EBU R128, true peak e comparação de loudness entre todos os vídeos de um mesmo lote, evitando shorts com áudio muito mais baixo. Também impede repetir os mesmos segundos entre Shorts quando isso não acrescenta narrativa. A correção-piloto de três vídeos foi testada no sandbox a partir do **original**, não no host FAMILIA.

<!-- CASA_VIDEO_EXPORT_V5 -->
## Exportação social e revisão visual V5

O [guia reutilizável V5](./GUIA_EXPORTACAO_SOCIAL_V5.md) documenta perfil HDR→SDR, validação de BT.709, MP4 compatível e revisão visual dos Shorts com a imagem de gameplay ocupando área suficiente. As anotações semânticas são **privadas** e não aparecem no vídeo.

Piloto: **6/6 MP4s passaram nos testes de decodificação do sandbox**, com originais preservados e hashes reconferidos. **Não testado no host FAMILIA nem reproduzido fisicamente no dispositivo do usuário.**

# CASA — Biblioteca Semântica de Vídeo v1.0

**Módulo global e reutilizável** para projetos de edição que usam gravações originais. Caminho: `integracoes/edicao_video/biblioteca_semantica/`.

## Finalidade e regras que não podem ser removidas

1. Converter observações feitas **sobre a gravação original** em eventos textuais privados: o que aparece, quando, quem age, consequência observada, evidência temporal e confiança.
2. Antes de montar, preservar **preparação → ação → consequência** e impedir reordenação dos trechos dentro da fonte.
3. Manter os textos **somente no índice interno**. A biblioteca **não desenha**, **não embute** nem **transmite** anotações ao vídeo exportado.
4. Não realizar cortes automáticos por silêncio/movimento nem afirmar desfechos inexistentes.
5. Não alterar, substituir, excluir ou divulgar os originais. Cada projeto mantém seus próprios hashes, eventos, EDLs e recibos.

## Arquitetura de camadas

- `schema.json`: contrato `casa.semantic-video/1.0`, compartilhável entre editores e pipelines.
- `semantic_timeline.py`: biblioteca Python 3.10+ sem dependências externas. Valida anotações, cronologia, presença dos eventos causais, flags de privacidade e cria **EDL proposta** em JSON; `--source-root` verifica SHA-256 de arquivos originais fisicamente acessíveis.
- `examples/example_timeline.json`: caso sintético (não contém imagens nem nomes de gravações do usuário).
- `tests/test_semantic_timeline.py`: testes negativos de regressão para saltos, fonte derivada, texto visível e causalidade quebrada.
- `SKILL.md`: contrato operacional de decupagem para o Qwen/editores CASA.

## Comandos de uso (não são instalação no FAMILIA)

```bash
python semantic_timeline.py validate examples/example_timeline.json
python semantic_timeline.py edl examples/example_timeline.json
python semantic_timeline.py validate caminho/indice.json --source-root caminho/gravacoes_originais
python -m unittest discover -s tests -v
```

Sem `--source-root`, a ferramenta apenas valida **declarações** de proveniência. Com a opção, confere hashes reais, mas não tem meios de provar sozinho que um arquivo foi capturado originalmente: isso requer manifesto confiável do projeto.

## Integrações previstas, ainda não instaladas/homologadas

**FFmpeg/ffprobe** para metadados, **PySceneDetect** para cortes visuais, **Qwen3-VL** para produção assistida de descrições de eventos, **whisper.cpp** apenas para diálogos, **OpenTimelineIO** para intercâmbio de EDL. O módulo atual **não invoca nem integra automaticamente** esses produtos. Textos sem observação visual ficam com baixa confiança e exigem revisão.

## Política de homologação

- **SOURCE:** confirmar commit, caminho e leitura de retorno do GitHub.
- **TESTES LOCAIS:** executar `unittest` em ambiente isolado e registrar versões/logs — só marcar aprovado quando houver saída real.
- **HOST FAMILIA:** requer execução autenticada e recibo local (host, código, versão, hash, stderr/stdout, consumo); **pendente**.
- **DEVICE/PLATAFORMA:** playback físico e dados de retenção, não comprovados.
- Não classificar SOURCE como HOST/DEVICE.

Veja também [guia de continuidade V3](../GUIA_EDITORIAL_CONTINUIDADE_V3.md) e [especificação de entendimento visual](../MOTOR_ENTENDIMENTO_VISUAL_V1.md).
