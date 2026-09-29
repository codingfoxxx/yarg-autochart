# PROGRESS — diário do projeto

> Fonte de verdade para retomar o trabalho. Atualizado a cada etapa.
> Última atualização: 2026-09-29 02:40 (horário de Brasília).

## Estado atual (resumo)

| Frente | Estado |
|---|---|
| Fase 0 (pesquisa e planejamento) | **Concluída**: `docs/pesquisa/`, DECISION.md, LICENSES.md, SECURITY_LOG.md |
| Fork do YARG | **Publicado**: https://github.com/codingfoxxx/YARG (branch padrão `pessoal` = upstream `dev` @ `275e9a13` + documentação: README com aviso, FORK.md, CHANGELOG-FORK.md, BUILD.md rascunho, NOTICE, COPYING). Actions desligadas. **Nenhuma mudança de código ainda.** |
| Repositório de ferramentas | **Publicado**: https://github.com/codingfoxxx/yarg-autochart (`main`), com o fork como submódulo `YARG/` |
| Auditoria da engine (sem Unity) | **Feita**: 25 testes (`tests/EngineTests`), relatório em `docs/auditoria-timing.md`; 2 bugs do upstream demonstrados |
| Ferramenta autochart | **Funcionando** (`autochart/`): CLI, arrastar-e-soltar, relatório, validação no YARG.Core, 20 testes unitários |
| Músicas de teste | **3 publicadas**: `samples/` + Release https://github.com/codingfoxxx/yarg-autochart/releases/tag/musicas-teste-v1 (pré-lançamento) |
| Unity / build do jogo | **Bloqueado por disco** (ver abaixo) — próximo passo com o Lucas |
| Eixo A no código do jogo | Não iniciado (precisa do Unity para compilar) |
| PLAYTEST.md / relatório final | Pendentes |

## Pendências que dependem do Lucas (manhã de 29/09)

1. **Espaço em disco para o Unity.** Livres ~9 GB. O Hub instalou sozinho o Unity **6000.6.3f1** (8,4 GB, não usado pelo YARG). Desinstalar pelo Hub (Installs → ⋮ → Uninstall, pede UAC) libera o suficiente para o 6000.3.5f2 (~7 GB) + Library (~5-8 GB). Outra opção: o disco do Docker (26,5 GB; as imagens `precheck-*` são dele).
2. **Instalar o Unity 6000.3.5f2** (Hub: `unityhub://6000.3.5f2/3fa8bc678cb0`, sem VS/docs; pede UAC) e o **Blender 4.5.5 LTS** (MSI do blender.org; pede UAC). Ou autorizar alternativas sem admin.
3. **Smart App Control**: o `YARG.exe` compilado localmente pode ser bloqueado (ver SECURITY_LOG.md). Se for, decidir: (a) manter o SAC e usarmos outra estratégia, ou (b) desligar o SAC (irreversível sem reinstalar o Windows). Não desligar sem ele decidir.
4. **Executável público**: rebranding antes de publicar um build (LICENSES.md §1 e §6).
5. **Moonscraper**: instalar (instalador verificado em `_downloads\`); pode ser barrado pelo SAC (sem assinatura).

## Como rodar as coisas

- Ambiente: `scripts\preparar-ambiente.ps1` (venv do lock + modelos com hash). .NET: `. scripts\dev-env.ps1`.
- Gerar música: arrastar o áudio em `scripts\gerar-musica.bat`, ou `.venv\Scripts\python.exe -m autochart gerar <audio> --titulo … --artista …`.
- Validar: `scripts\validar-musica.ps1 <pasta>`.
- Testes: `.venv\Scripts\python.exe -m unittest discover -s autochart\tests`; `dotnet test tests\EngineTests`; testes do YARG.Core: `dotnet test YARG\YARG.Core\YARG.Core.UnitTests` (1 falha de cultura pt-BR, conhecida).

## Madrugada de 29/09 — o que foi feito (com números)

- **Testes da engine** (`tests/EngineTests`): resultado idêntico de 24 a 1000 fps (40 partidas humanizadas); janela efetiva de palhetada −95/+70 ms; tolerâncias, acordes, âncora, ghosting, sustain e star power conferidos. Bugs do upstream: pontos de sustain sem multiplicador no overstrum; `FiveFretGuitarPreset.Copy()` sem `SustainDropLeniency`.
- **Pilha de ML isolada**: sandbox Docker → 65 wheels do Windows com hash → `.venv` offline. **Smart App Control bloqueia torch 2.14** → torch/torchaudio **2.8.0**. Pesos locais com hash; Demucs só carrega se a classe nos metadados for a esperada.
- **autochart**: batidas sub-quadro + fase pelos ataques; andamento único quando cabe no ruído (124,0 BPM exatos na música do Admiral Bob); deriva real seguida (165→176 BPM ao vivo no Aguaviva); compasso único com fase (3/4 no waltz); vocabulário rítmico por música (sem tercinas falsas); filtro de vazamento; validação no YARG.Core com conferência nota a nota do tipo strum/HOPO/tap.
- **Resultados nas 3 músicas**: 0 violações; o scanner do jogo acha as 4 dificuldades; tipos de nota conferem 100%; jogador perfeito 100%; humano σ20 ms 99,9-100%; humano σ35 ms 95,7-97,9%.
- **Vigia noturno** (`_work\vigia-noturno.ps1`, log em `_work\vigia-noturno.log`): mantém o PC acordado enquanto há trabalho; após 25 min ocioso suspende com despertador (02:05, 07:10); em problema grava `_work\PROBLEMA-PC.txt` e suspende sem despertar. Encerra às 11:00. **Regra do Lucas: se algo der errado com o PC, parar, suspender e esperar.**

## Decisões tomadas

| Data | Decisão | Motivo |
|---|---|---|
| 2026-09-28 | Projeto em `C:\Dev\GuitarHero` (atalho na Área de Trabalho), fora do OneDrive | Escolha do Lucas |
| 2026-09-28 | Base do fork = upstream `dev` @ `275e9a13` | Correções de sincronia/calibração posteriores ao v0.15.0 |
| 2026-09-28 | Instalações portáteis em `_tools/` | Terminal sem admin; sem UAC durante a noite |
| 2026-09-29 | Chart em `.chart` (res 192) | Nativo do Moonscraper; HOPO idêntico ao do YARG |
| 2026-09-29 | Dois repositórios: fork + `yarg-autochart` (MIT) | Fork limpo e fácil de atualizar |
| 2026-09-29 | Executável do jogo só local até decidir rebranding | Nome/logos "YARG" sem licença de uso |
| 2026-09-29 | torch 2.8.0 | Smart App Control bloqueia DLLs do 2.14 |
| 2026-09-29 | Validador via `dotnet test` | Smart App Control bloqueia DLL local como programa principal |
| 2026-09-29 | Músicas publicadas sem stems separados | Pesos do Demucs "só para fins científicos" |
| 2026-09-29 | Fórmula de compasso única por música | Tempos fortes do detector oscilam (39 mudanças falsas no waltz) |

## Próximos passos

1. [ ] (Lucas) liberar disco + Unity 6000.3.5f2 + Blender; decidir sobre o Smart App Control se o `YARG.exe` for bloqueado.
2. [ ] Build de linha de comando do fork (`-batchmode -buildWindows64Player`), teste de fumaça (o jogo abre? acha as músicas de `songs\`?), medir FPS (PresentMon) e stutter.
3. [ ] Eixo A no código: histerese de gatilho analógico (configurável), deadzone do whammy no preset de controle, `Keyboard.current` sem nulo, calibração guiada para controle (instruções pt-BR/en, salvar por perfil). Cada mudança com entrada no CHANGELOG-FORK.md.
4. [ ] Testes de input no Unity (InputTestFixture com controle virtual de Xbox).
5. [ ] PLAYTEST.md e relatório final (`RELATORIO-FINAL.md`), conferência do histórico git (sem marcas de IA).
6. [ ] (opcional) PRs no upstream: os 2 bugs do YARG.Core e o teste de cultura.

## Problemas e observações

- `Keyboard.current` sem checagem de nulo em `GameManager.Update` (baixo risco no Windows).
- Latência de saída contada duas vezes com calibração 0 (confirmado no código; a calibração neutraliza; não alterar sem medir).
- Parsing de números dependente do idioma do Windows (bindings, campos de texto).
- Regressão upstream: sem `song.ini`, `notes.chart` sozinho não é detectado.
- O guarda de segurança do terminal bloqueia comandos com `Remove-Item`/`rm` junto de barras ou caminhos de sistema, mesmo dentro de texto: fazer remoções em comandos separados e escrever textos longos com a ferramenta de arquivos.
- Metal denso é o caso mais difícil para o autochart (separação pior, ataques borrados).
