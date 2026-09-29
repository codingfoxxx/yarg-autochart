# PROGRESS — diário do projeto

> Fonte de verdade para retomar o trabalho. Atualizado a cada etapa.
> Última atualização: 2026-09-29 00:25 (horário de Brasília).

## Estado atual (resumo)

- **Fase 0 (pesquisa e planejamento): quase concluída.** Quatro de cinco pesquisas prontas (formato de música, mapa de input/engine, estado da arte do auto-charting, músicas livres). Falta o inventário de licenças (sub-agente ainda rodando em 00:25).
- **Documentos da Fase 0:** PROGRESS.md (este), .gitignore. Faltam: LICENSES.md, BUILD.md, DECISION.md, SECURITY_LOG.md, docs/pesquisa/.
- **Ações do Lucas pedidas em 00:20** (antes de dormir): (1) login no Unity Hub + licença Personal; (2) `gh auth login` com o gh portátil. Conferir com `gh auth status` e com a existência da licença antes de usar.
- **Alarmes** (só nesta sessão): 02:05 e 07:10 do dia 29/09, para retomar se a cota acabar. PC mantido acordado até 11:00 por um processo PowerShell oculto (SetThreadExecutionState).

## Decisões tomadas

| Data | Decisão | Motivo |
|---|---|---|
| 2026-09-28 | Projeto em `C:\Dev\GuitarHero` (atalho na Área de Trabalho), fora do OneDrive | Escolha do Lucas: OneDrive sincroniza a Área de Trabalho; caminho com acento/espaço quebra ferramentas |
| 2026-09-28 | Limpeza de caches npm (6,0 GB) e pip (1,7 GB) | Autorizado pelo Lucas; disco tinha 22 GB livres |
| 2026-09-28 | Base do fork = upstream `dev` @ `275e9a13` (26/09/2026), YARG.Core @ `e2d44e8d` | `dev` tem correções de sincronia de áudio/calibração posteriores ao v0.15.0 (#1558, #1589, calibração, offset por música) |
| 2026-09-28 | Instalações portáteis em `_tools/` (gh, .NET, Blender, Unity Editor) | Terminal sem admin; evita janelas de UAC durante a noite e mantém tudo na pasta do projeto |
| 2026-09-28 | Blender é necessário | `Assets/Art/Meshes/Obsolete/Notes.blend` ainda é usado pelo tema de notas Rectangular (notas abertas/HOPO) e pelo preview de notas |
| 2026-09-29 | Chart gerado em `.chart` (resolução 192), não `.mid` | Formato nativo do Moonscraper (edição fiel ao jogo); limiar natural de HOPO igual no YARG e no Moonscraper (65 ticks); o gerador calcula as inversões `N 5` e o validador confere com o parser do YARG |

## Ambiente (fatos verificados)

- Windows 11 Home, Ryzen 7 7700, 32 GB RAM, RTX 4070 SUPER (instável: TDR em 28/09, preferir CPU).
- Disco C: ~27 GB livres em 29/09 00:10 (só existe o C:). Vigiar antes de instalar o Unity (~7 GB) e gerar a Library (~5-8 GB).
- git 2.53 + git-lfs 3.7.1; identidade `Lucas Raposo <lucasraposobastos25@gmail.com>`; GitHub `codingfoxxx` no Git Credential Manager.
- Python 3.11.9 (`py -3.11`) e 3.14.3 (padrão). ffmpeg 9.0.1 (gyan.dev) já instalado. Node 24.
- Docker Desktop instalado (WSL2), daemon parado; `docker_data.vhdx` = 24,6 GB (do Lucas, não podar).
- Unity Hub 3.21.3 instalado (MSIX, por usuário). gh 2.101.0 portátil em `_tools\gh\bin\gh.exe`.
- Terminal NÃO é admin.

## Onde as coisas estão

- `C:\Dev\GuitarHero\` → repositório principal (ferramentas + docs), ainda sem `git init`.
- Clone do YARG (upstream, `dev` @ 275e9a13, LFS NÃO baixado) ainda em
  `C:\Users\lucas\OneDrive\Área de Trabalho\Guitar Hero\YARG` → **mover para `C:\Dev\GuitarHero\YARG`** quando o sub-agente de licenças terminar (ele lê de lá). Depois apagar a pasta vazia "Guitar Hero" da Área de Trabalho e criar o atalho.
- Instaladores baixados: `_downloads\` (gh zip, Unity Hub msix) com SHA-256 conferidos.
- Pesquisas brutas (relatórios dos sub-agentes): serão salvas em `docs/pesquisa/`.

## Próximos passos (em ordem)

1. [ ] Receber o relatório de licenças → escrever LICENSES.md.
2. [ ] Salvar relatórios em `docs/pesquisa/` (sem dados pessoais da máquina).
3. [ ] Escrever BUILD.md, DECISION.md, SECURITY_LOG.md. `git init` do repositório principal e primeiro commit (sem marca de IA!).
4. [ ] Mover o clone do YARG para `C:\Dev\GuitarHero\YARG`; atalho na Área de Trabalho.
5. [ ] Conferir `gh auth status` e a licença Unity. Se ok: criar forks `codingfoxxx/YARG` (todas as branches) e `codingfoxxx/YARG.Core` só se for mexer no core; criar branch `pessoal` a partir de `dev`@275e9a13; configurar remotes (`origin` = fork, `upstream` = oficial).
6. [ ] Instalar (portátil, com hash + Defender): .NET SDK 10 (`dotnet-install.ps1` em `_tools\dotnet`), Blender 4.5.5 LTS zip em `_tools\blender` + `blender --register` (associação .blend por usuário), Unity Editor 6000.3.5f2 via Hub CLI em `_tools\Unity` (só Windows Mono, sem VS, sem docs).
7. [ ] `git lfs pull` no YARG; build de linha de comando (`-batchmode -buildWindows64Player`), logs em `_builds\`.
8. [ ] Rodar `dotnet test` do YARG.Core.UnitTests; criar projeto de testes da engine (5 trastes, inputs com timestamp) no repositório principal.
9. [ ] Ambiente Python 3.11 (`.venv`), primeiro em container Docker (isolamento) para registrar downloads de pesos; pinos com hash.
10. [ ] Ferramenta `autochart` (ver DECISION.md) + validador .NET com YARG.Core.
11. [ ] Músicas de teste (candidatas em docs/pesquisa/musicas-livres.md): Burn The World Waltz (Kevin MacLeod, 3/4, 177 BPM), Attack of the Aguaviva (Blue_Wave_Theory, 170, FLAC), The Beach is No Place... (Admiral Bob, 124), The Vagabond (Josh Woodward, 128, pede e-mail).
12. [ ] Eixo A: auditoria de timing (suspeitas em docs/pesquisa/mapa-input-engine.md), histerese nos gatilhos analógicos, deadzone do whammy, calibração guiada para controle.

## Problemas e observações

- `Keyboard.current` usado sem checar nulo em `GameManager.Update` (baixo risco no Windows).
- Suspeita confirmada no código: com calibração 0 e "Account for hardware latency" ligado, a latência do endpoint (~35 ms no modo compartilhado) é descontada duas vezes. Pode compensar latências não modeladas; só medição real resolve. A calibração neutraliza. Não alterar sem medir.
- Regressão upstream (não nos afeta): sem `song.ini`, um `notes.chart` sozinho não é detectado (`CacheHandler.cs:808-810`).
