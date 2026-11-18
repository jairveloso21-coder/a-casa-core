# CASA Core — integração das sete capacidades do Hermes ao ChatGPT (L1)

## Contrato operacional

A CASA Core permanece **a única autoridade** para política, journal, locks, idempotência, CI e recibos. Esta integração reutiliza capacidades do Hermes Agent, não instala um novo runtime Hermes e não exige modelos Hermes 3/4. O Qwen Code continua sendo o orquestrador local pretendido; Forge/Lya é responsável pelo planejamento/subagentes.

O **ChatGPT** atua como L1 e usa apenas conectores autorizados nesta sessão. Não há plugin nativo CASA automaticamente instalado no ChatGPT, nem acesso PowerShell direto, nem memória da conta alterada apenas por commit. A memória persistente da conta pode guardar preferências, mas **o checkpoint operacional canônico** continua no GitHub e nos recibos da CASA.

## Ordem de BOOT/RESUME do ChatGPT

1. Recuperar o projeto/objetivo e os estados físicos preservados; ler `INICIAR_SESSAO_IA.txt`, `SESSION_BOOTSTRAP_V12.md`, `CANONICAL_SYSTEM_STATE.json`, último recibo e regras atualizadas de `Projetos-Arquivo`.
2. Ler `core/CASA_HERMES_NUCLEUS_V1.json`. `core/casa_hermes_nucleus.py` audita a presença de fontes em checkouts locais com `--core-root` e `--state-root`, mas **NUNCA** declara CI, HOST, DEVICE ou instalação do ChatGPT.
3. Memória: usar Skill existente `casa-memoria-evolutiva` e ledger; recuperar registros por projeto, sem duplicar memórias ou misturar dados.
4. Autoaperfeiçoamento: melhorias comprovadas viram atualizações versionadas às Skills existentes; sem promoção automática a partir de texto de modelo ou recibo não verificado.
5. MCP: reutilizar `casa-global-tools` e `casa-core-gateway` já documentados. Invocar ferramentas reais somente se conectadas, com schemas e permissões atuais.
6. Execução: usar contratos tipados do Strict Executor/Bridge. Para FAMILIA, o Git V1 suporta consulta somente leitura `device.status`, e o Gmail Bridge preservado suporta envelope cifrado quando o cliente original e as chaves efêmeras estiverem disponíveis. GitHub access não equivale a shell.
7. Subagentes: delegar via Forge/Lya apenas após escopo e lock por projeto; nenhum subagente concede novo privilégio.
8. Agendamento: reutilizar CASA Unified Supervisor/Agendador e automações habilitadas; não criar segundo daemon, cron concorrente ou repetição de missão com efeito incerto.
9. Multiplataforma: FAMILIA Windows/WSL e Garnet/Termux possuem identidades, assinaturas e permissões próprias. Fire TV e PS5 exigem gates específicos.
10. Encerrar por CANDIDATO -> SOURCE -> CI Gitea -> HOST FAMILIA -> DEVICE -> EDITORIAL, só nos gates aplicáveis; validar SSHSIG independentemente e registrar o primeiro gate ainda aberto.

## Continuidade da execução local recuperada em 18/11/2026

- **Ponte comprovada historicamente:** `casa-sovereign-bridge-v1/bridge.py` e V2, `missions/inbox/<PROJETO>/` / `missions/outbox/<PROJETO>/`, Gmail `CASA-CMD-V1` / `CASA-RESULT-V1`, `CASA_Gmail_Bridge_v1_1.zip` preservado na Library.
- **Não tratar como rota perdida** por ausência de ferramenta PowerShell nesta conversa. O canal e as permissões precisam ser verificados por operação e recibo atual, sem reinstalação.
- **Canário somente leitura** Git V1: job `6d637bd7-ff0e-41d5-a14f-112285b994b7`, `target=familia`, `operation=device.status`, nonce `7c7d30d4-a07a-4e75-926c-567ffa30122b`, commit `a70fe47eda5e21e9c81e5313f254cd062a62dbc6`, tarefa em `casa-sovereign-bridge-v1/tasks/`. Estado ao despacho: `QUEUED_GIT`, recibo ainda não verificado.
- Conferir primeiro `casa-sovereign-bridge-v1/results/<job>/familia.json` e atestação V2 correspondente. Sem resultado não duplicar o job. Um recibo Git correlacionado não é assinatura SSHSIG por si só.
- A verificação do Gitea CI é independente: endpoint oficial `127.0.0.1:3002` no FAMILIA, e não uma chamada à rede local a partir do ambiente ChatGPT.

## Gate de desenvolvimento

`python -m unittest discover -s tests -p 'test_casa_hermes_nucleus.py' -v` valida manifesto, rotas, paths, isolamento e cadeia de recibos. O teste offline **não** instala esta funcionalidade no FAMILIA. Não promover PR ou artefato como homologação CI/HOST sem recibos próprios.
