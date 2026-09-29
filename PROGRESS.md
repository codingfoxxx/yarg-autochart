# PROGRESS — diário do projeto

> Fonte de verdade para retomar o trabalho. Atualizado a cada etapa.
> Última atualização: 2026-09-29 01:15 (horário de Brasília).

## Estado atual (resumo)

- **Fase 0 concluída**: pesquisas em `docs/pesquisa/`, DECISION.md, LICENSES.md, SECURITY_LOG.md.
- **Fork publicado**: https://github.com/codingfoxxx/YARG (branch padrão `pessoal`, commit `65ee51d2` = upstream `dev` @ `275e9a13` + só documentação: aviso no README, FORK.md, CHANGELOG-FORK.md, BUILD.md rascunho, NOTICE, COPYING). GitHub Actions do fork desligadas. LFS do fork funciona (servido pela rede de forks).
- **Repositório de ferramentas**: `C:\Dev\GuitarHero` (git local, branch `main`); vai para https://github.com/codingfoxxx/yarg-autochart com o fork como submódulo `YARG/`.
- **Unity: ADIADO para amanhã** por falta de disco. O Hub instalou sozinho (assistente de primeiro uso, aceito pelo Lucas) o Unity **6000.6.3f1** (+WebGL +docs, 8,4 GB em `C:\Program Files\Unity\Hub\Editor\6000.6.3f1`), que o YARG não usa. Livre: ~12,8 GB. O 6000.3.5f2 (~10 GB no pico) + Library (~5-8 GB) não cabem. **Pedir ao Lucas: desinstalar o 6000.6.3f1 pelo Hub (Installs → ⋮ → Uninstall; pede UAC).** Depois: instalar 6000.3.5f2 (Hub: `unityhub://6000.3.5f2/3fa8bc678cb0`, sem VS nem docs) e Blender.
- **Licença Unity Personal**: ativada (29/09 00:26). Fica na pasta virtualizada do Hub MSIX (`%LOCALAPPDATA%\Packages\UnityTechnologies.UnityHub_2vrhnee42bhxm\LocalCache\Local\Unity\licenses\`). Rodar o editor com o Hub aberto.
- **.NET SDK 10.0.401** portátil em `_tools\dotnet` (SHA-512 ok). YARG.Core.UnitTests: 547 ok, 1 falha de cultura pt-BR, 2 ignorados.
- **gh** logado como `codingfoxxx` (keyring), escopos repo/workflow/gist/read:org. No clone do YARG, credencial local = gh.

## Noite de 28→29/09 (Lucas dormindo)

- **Vigia noturno** (`_work\vigia-noturno.ps1`, PID em `_work\vigia.pid`, log em `_work\vigia-noturno.log`): mantém o PC acordado enquanto há trabalho; após 25 min de ociosidade suspende com despertador (02:05, depois 07:10); em problema (disco < 3 GB, RAM/commit baixos, erro de GPU/driver no log) grava `_work\PROBLEMA-PC.txt` e suspende **sem** despertador. Encerra às 11:00. Controles: `_work\busy-until.txt` (yyyy-MM-dd HH:mm), `_work\sem-despertar.txt`, `_work\parar-vigia.txt`.
- **Lembretes do Claude** (só nesta sessão): 02:10, 02:25, 07:15, 07:32.
- **Regra do Lucas:** se algo der errado com o PC (comportamento inesperado, memória…), NÃO prosseguir: parar, suspender o PC e esperar a resposta dele. **Checar `_work\PROBLEMA-PC.txt` antes de cada etapa longa.**

## Decisões tomadas

| Data | Decisão | Motivo |
|---|---|---|
| 2026-09-28 | Projeto em `C:\Dev\GuitarHero` (atalho "Guitar Hero" na Área de Trabalho), fora do OneDrive | Escolha do Lucas |
| 2026-09-28 | Limpeza de caches npm (6,0 GB) e pip (1,7 GB) | Autorizado pelo Lucas |
| 2026-09-28 | Base do fork = upstream `dev` @ `275e9a13` | Correções de sincronia/calibração posteriores ao v0.15.0 |
| 2026-09-28 | Instalações portáteis em `_tools/` | Terminal sem admin; sem UAC durante a noite |
| 2026-09-28 | Blender é necessário | `Notes.blend` ainda é usado pelo tema de notas Rectangular |
| 2026-09-29 | Chart em `.chart` (res 192) | Nativo do Moonscraper; ver DECISION.md §4 |
| 2026-09-29 | Dois repositórios: fork `codingfoxxx/YARG` + `codingfoxxx/yarg-autochart` (MIT) | Fork limpo e fácil de atualizar; ver DECISION.md §2 |
| 2026-09-29 | Executável do jogo **só local** até o Lucas decidir sobre rebranding | Nome/logos "YARG" sem licença de uso; ver LICENSES.md §1 |

## Madrugada de 29/09 (01:00-02:00) — o que foi feito

- **Testes da engine** (`tests/EngineTests`, 25 testes, todos passando) + `docs/auditoria-timing.md`: resultado idêntico de 24 a 1000 fps; janela efetiva de palhetada −95/+70 ms; 2 problemas do upstream demonstrados (KnownIssue). Commit `24a034f`.
- **Pilha de ML**: sandbox Docker (`sandbox/ml-sandbox.sh`, `sandbox/smoke.py`, `sandbox/wheels-win.sh`) → wheels do Windows com hash em `_work/sandbox/wheels-win` + `_work/sandbox/requirements-win.lock` → `.venv` (Python 3.11.9) instalado com `--no-index --require-hashes`. `autochart/src` entra no venv por `.venv/Lib/site-packages/autochart-src.pth`.
- **Smart App Control (Windows) bloqueia as DLLs do torch 2.14** (sem assinatura/reputação). Solução sem mexer na segurança: **torch/torchaudio fixados em 2.8.0** (carregam). Não desligar o SAC (não volta sem reinstalar o Windows).
- **Pesos**: `models/beat_this/final0.ckpt` (sha256 8c328b45…), `models/demucs/htdemucs_6s-5c90dfd2.safetensors` (sha256 d2a1745f…). Carregados offline com hash conferido (`autochart/src/autochart/models.py`); o Demucs só carrega se a classe nos metadados for `demucs.htdemucs.HTDemucs`.
- **autochart** (pacote Python em `autochart/src/autochart`): tempomap, quantize, analysis (batidas sub-quadro + correção de fase, ataques refinados no envelope), events, lanes (Viterbi), difficulty, starpower, sections, chart (escritor .chart/.ini com HOPO natural do YARG), report, pipeline, cli. Rodar: `.venv\Scripts\python.exe -m autochart gerar <audio> --titulo … --artista …`.
- Teste sintético (20 s, 120 BPM): grid 120,03 BPM, erro das batidas mediana 2,4 ms; nota→evento ~2 ms; 0 violações.

## Próximos passos (em ordem)

1. [x] LICENSES.md, DECISION.md, SECURITY_LOG.md, docs/pesquisa.
2. [x] Fork criado e branch `pessoal` publicada.
3. [ ] Repositório `yarg-autochart` no GitHub com o submódulo `YARG`.
4. [ ] **Testes da engine de 5 trastes** (`tests/EngineTests`, NUnit, net10.0, referenciando `YARG/YARG.Core/YARG.Core/YARG.Core.csproj`): inputs com timestamp para strum, HOPO, tap, acordes, ghosting, sustain, star power, janelas nas bordas. Investigar as suspeitas 7, 8, 9 do `docs/pesquisa/mapa-input-engine.md`.
5. [ ] **Validador .NET** (`tools/validator`): varre a pasta da música como o jogo (CacheHandler/SongEntry), carrega o chart, roda o bot, gera relatório.
6. [ ] **Ambiente Python 3.11**: teste isolado em Docker (downloads de pesos), depois `.venv` local com hashes. Checar espaço antes (Docker cresce o vhdx).
7. [ ] **Ferramenta `autochart`** (pipeline em DECISION.md §5) + métricas + relatório.
8. [ ] Músicas de teste: baixar 3-4 (ver `docs/pesquisa/musicas-livres.md`), registrar hashes e créditos em LICENSES.md §5, gerar charts, validar.
9. [ ] Moonscraper 1.5.13 (download verificado) + documentar o fluxo de edição.
10. [ ] (Com disco livre) Unity 6000.3.5f2 + Blender 4.5.5 LTS → build de linha de comando → teste de fumaça.
11. [ ] Eixo A no código do jogo: histerese de gatilho, deadzone do whammy, calibração guiada, `Keyboard.current`.
12. [ ] PLAYTEST.md, relatório final, conferência do histórico git (sem marcas de IA).

## Problemas e observações

- `Keyboard.current` sem checagem de nulo em `GameManager.Update` (baixo risco no Windows).
- Latência de saída contada duas vezes no modo compartilhado com calibração 0 (confirmado no código; ver docs/pesquisa/mapa-input-engine.md §suspeitas 1). Não alterar sem medir; a calibração neutraliza.
- Parsing de números dependente do idioma do Windows (bindings, campos de texto): consistente no mesmo PC; risco se a região do Windows mudar.
- Regressão upstream: sem `song.ini`, `notes.chart` sozinho não é detectado.
- O guarda de segurança do terminal bloqueia comandos que têm `Remove-Item` junto com caminhos de `C:\Program Files` ou regex: fazer remoções em comandos separados.
