# CASA Video Lab — QA de exportações V6

Ferramenta reutilizável de **auditoria**, sem necessidade de instalar Qwen3-VL ou abrir editor de vídeo.

## Escopo do módulo
- Verifica SHA-256 **real** de originais e exportações, sempre por caminhos relativos a raízes configuráveis.
- Identifica Shorts com sobreposição indevida na mesma gravação original.
- Confere H.264/AAC, orientação, duração e as três tags de cor BT.709.
- Mede o loudness integrado e o true peak pelo FFmpeg, além de comparar diferença de loudness entre os vídeos do mesmo lote.
- Decodifica integralmente cada arquivo para procurar falhas de reprodução.
- Impõe que descrições semânticas sejam privadas no manifesto; **não verifica visualmente se um texto foi queimado no vídeo**.
- Nunca modifica os arquivos originais nem cria legendas. Requer Python 3.10+, FFmpeg e ffprobe disponíveis no PATH.

## Como usar

```bash
python qa_video_lote.py manifesto_exportacoes.json \
  --exports-root /caminho/de/exports \
  --sources-root /caminho/dos/originais \
  --report /caminho/para/relatorio.json
python -m unittest discover -s tests -p 'test_qa_video_lote.py' -v
```

### Manifesto

```json
{
  "schema_version": "casa.video.export-qa/1.0",
  "annotations_private": true,
  "render_semantic_text": false,
  "sources": [{
    "id": "captura_01",
    "file": "gravacao_original.webm",
    "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "origin": "raw_capture",
    "duration_seconds": 100.0
  }],
  "exports": [{
    "source_id": "captura_01",
    "file": "short_01.mp4",
    "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "in_seconds": 10.0,
    "out_seconds": 22.0,
    "format": "short"
  }]
}
```

Os hashes são ilustrativos: a verificação exige o hash real dos bytes no disco. `format` é `short` ou `youtube_horizontal`. O manifesto demonstra uma decisão editorial, mas sua declaração `origin=raw_capture` **não constitui prova independente** da origem — essa classificação exige registro confiável da captura no projeto.

## QA da amostra recebida (16/11/2026)

- ZIP recebido: três MP4s V6 do Mickey com SHA-256 consistente com o manifesto.
- Arquivo original presente no sandbox: SHA-256 conferido com o manifesto.
- **8/8** testes unitários do novo módulo passaram, no sandbox.
- **3/3** exports do pacote passaram na execução completa de `qa_video_lote.py` no sandbox.
- Loudness medido novamente: **−18,25; −18,67; −17,07 LUFS**. Todos dentro da tolerância editorial configurada para o piloto (−18 ±3 LU).
- Sem sobreposição entre os Shorts 0,0–6,8 s e 6,8–14,9 s.
- A execução não confirma qualidade narrativa percebida, retenção, hospedagem/publicação nem testes no host FAMILIA.

## Status separados

- `SOURCE`: módulo e testes publicados e relidos no GitHub.
- `SANDBOX`: **8/8 testes unitários** e **3/3 vídeos V6** aprovados pelo módulo.
- `CI`: não executado.
- `HOST_FAMILIA`: não executado nem instalado por esta sessão.
- `DEVICE`: não testado.
- `RETENTION`: não medida.

A biblioteca pertence ao projeto global de ferramentas compartilhadas, mas cada projeto mantém suas **gravações, manifestos, logs e outputs isolados**. Sem serviços residentes ou alteração em pastas de outros projetos.