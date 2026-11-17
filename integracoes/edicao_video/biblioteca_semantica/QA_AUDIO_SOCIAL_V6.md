# CASA Video Lab — Gate de áudio e comparação entre exports (V6)

**Data de incorporação:** 2026-11-16. **Escopo:** biblioteca global de edição; dados de cada projeto permanecem isolados.

## Defeito reproduzido

Seis vídeos sociais renderizados e aprovados por testes de codec/decodificação tinham **volumes de áudio muito diferentes**. Os vídeos de gameplay do Mickey apresentaram medição de loudness integrado EBU R128 entre **−36,2 e −35,0 LUFS**; os de Stellar Blade, entre **−20,3 e −18,3 LUFS**. A diferença entre grupos era de cerca de 16–18 LU, embora todos os arquivos tivessem AAC válido.

**Conclusão:** o QA de vídeo deve verificar **loudness integrado, true peak e uniformidade entre posts**, não apenas integridade/codec.

## Procedimento reutilizável (realizar no original)

1. Manifestar hash SHA-256, áudio original, duração e IN/OUT. Nunca extrair o áudio de um export V5 para criar uma V6.
2. Obter loudness integrado e true peak com FFmpeg EBU R128: `ffmpeg -hide_banner -i original.mp4 -vn -af ebur128=peak=true -f null -`.
3. Escolher meta de loudness de trabalho (no piloto: aproximadamente **−18 LUFS**, com teto de true peak em **−1,5 dBTP**). Isso é **meta editorial local**, não uma regra única oficial de TikTok/Instagram/YouTube.
4. Fazer normalização do **áudio do trecho original** usando a medição real. Exemplo de filtro de primeiro teste: `loudnorm=I=-18:TP=-1.5:LRA=11`. Quando necessário, usar medição de duas passagens para reprodução mais previsível.
5. Não amplificar ruído/silêncio indevidamente. Avaliar som do jogo e fala antes de liberar ganho; ouvir início, ação principal, pico e final.
6. Após render, medir novamente LUFS e true peak de **cada saída**, verificar sincronização, codec, canais e duração.
7. **Gate de coerência do lote:** destacar diferença de loudness integrado acima de 3 LU entre vídeos do mesmo pacote para revisão humana. Isso é um gatilho de QA, não uma garantia automática de qualidade percebida.
8. Processar vídeos sempre da mídia bruta, nunca da versão V5; manter texto de entendimento semântico apenas nos JSONs privados.
9. Registrar separadamente SOURCE, SANDBOX, CI, HOST_FAMILIA, DEVICE e métricas reais das plataformas. Não considerar renderização local equivalente a instalação no FAMILIA.

## Regra editorial para vídeos repetitivos

Ao extrair dois Shorts de um original muito curto, medir sobreposição temporal e distinguir os objetivos narrativos. No piloto do Mickey (original de ~15 s), V5 usava intervalos **0–8,5 s** e **5,4–14,9 s**, repetindo **3,1 segundos**. A V6 propôs **0–6,8 s** e **6,8–14,9 s**, sem sobreposição e preservando ordem. **Ausência de desfecho no bruto não pode ser disfarçada**: nunca inventar vitória ou etapa concluída.

## Evidência do piloto V6

Correções reais executadas apenas no SANDBOX da conversa a partir do original preservado:

| Exportação | Duração | Loudness integrado | True peak | QA |
|---|---:|---:|---:|---|
| Mickey Short 1 V6 | 6,8 s | −18,1 LUFS | −3,4 dBFS | decodificação integral PASS |
| Mickey Short 2 V6 | 8,1 s | −18,7 LUFS | −3,4 dBFS | decodificação integral PASS |
| Mickey YouTube V6 | 14,97 s | −17,1 LUFS | −1,6 dBFS | decodificação integral PASS |

Os três arquivos foram gerados diretamente do original de Mickey, sem usar exports V5 como insumo e sem inserir descrições textuais no vídeo. A notificação do troféu ainda está presente na versão horizontal pois existe no original.

**Status:** SOURCE = guia publicado/relido após commit; SANDBOX = três renders e QA PASS; CI, HOST FAMILIA, DEVICE e publicação/retention = NÃO TESTADOS. O motor semântico visual automatizado Qwen3-VL continua não homologado.

Veja também [GUIA_EXPORTACAO_SOCIAL_V5.md](./GUIA_EXPORTACAO_SOCIAL_V5.md) e [MOTOR_ENTENDIMENTO_VISUAL_V1.md](../MOTOR_ENTENDIMENTO_VISUAL_V1.md).
