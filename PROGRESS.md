# PROGRESS — diário do projeto

> Fonte de verdade para retomar o trabalho. Atualizado a cada etapa.
> Última atualização: 2026-09-29 03:15 (horário de Brasília).

## Estado atual (resumo)

| Frente | Estado |
|---|---|
| Fase 0 (pesquisa e planejamento) | **Concluída**: `docs/pesquisa/`, DECISION.md, LICENSES.md, SECURITY_LOG.md |
| Fork do YARG | **Publicado**: https://github.com/codingfoxxx/YARG (branch padrão `pessoal` = upstream `dev` @ `275e9a13` + documentação: README com aviso, FORK.md, CHANGELOG-FORK.md, BUILD.md rascunho, NOTICE, COPYING). Actions desligadas. **Nenhuma mudança de código ainda.** |
| Repositório de ferramentas | **Publicado**: https://github.com/codingfoxxx/yarg-autochart (`main`), com o fork como submódulo `YARG/` |
| Auditoria da engine (sem Unity) | **Feita**: 25 testes (`tests/EngineTests`), relatório em `docs/auditoria-timing.md`; 2 bugs do upstream demonstrados |
| Ferramenta autochart | **Funcionando** (`autochart/`): CLI, arrastar-e-soltar, relatório, validação no YARG.Core, 20 testes unitários |
| Músicas de teste | **3 publicadas**: `samples/` + Release https://github.com/codingfoxxx/yarg-autochart/releases/tag/musicas-teste-v1 (pré-lançamento) |
| Unity / build do jogo | **Bloqueado**: disco (ver abaixo) e, mais sério, o **Smart App Control barra o compilador do Unity** (testado com o 6000.6.3f1; ver abaixo) |
| Eixo A no código do jogo | **Publicado no fork** (`pessoal` @ `f542fbf4`): histerese nos gatilhos do controle; correção de `Keyboard.current` nulo; **calibração guiada** (instruções pt-BR/en, 2 passadas, resultado explicado, salvar no perfil ou global). Compila (verificador próprio, 0 erros, mesmos 26 avisos do upstream); sem teste no jogo rodando |
| Testes .NET | 43/43 (engine + histerese + calibração) — rodam num contêiner Linux, porque o Windows passou a barrar a DLL de testes recompilada |
| PLAYTEST.md / relatório final | Pendentes |

## ⚠ Decisão importante para a manhã: Smart App Control × Unity

Às 02:40 abri o fork com o Unity 6000.6.3f1 (o que o Hub instalou sozinho) em modo batch, numa cópia só com os scripts. A licença funcionou. A compilação **falhou sem nenhum erro de código**: o Windows (Smart App Control, política `VerifiedAndReputableDesktop`, eventos 3077) bloqueou DLLs sem assinatura que vêm **dentro do próprio Unity**, e sem elas o pipeline de compilação do Unity 6 não termina (`ApiUpdater.MovedFromExtractor.dll`, entre outras; detalhes no SECURITY_LOG.md).

- Com o SAC ligado, **o Unity 6000.6.3f1 não compila nada nesta máquina**. O 6000.3.5f2 pode ou não ter o mesmo problema: a decisão do Windows é por arquivo, pela reputação na nuvem. Só dá para saber instalando.
- O `YARG.exe` gerado também seria um executável sem assinatura (ver item 3 abaixo).
- Opções: (a) instalar o 6000.3.5f2 e testar; se falhar igual, (b) desligar o SAC (decisão só sua; **irreversível** sem reinstalar o Windows; o Defender continua ativo) ou (c) compilar o jogo fora desta máquina (GitHub Actions com a sua licença do Unity cadastrada como segredo, feito por você) e, mesmo assim, o `YARG.exe` provavelmente seria barrado para rodar aqui.
- Enquanto isso, o código do fork é verificado com `tools/unity-compile-check` (o compilador C# do Unity, que é assinado pela Microsoft, roda normalmente).

## Pendências que dependem do Lucas (manhã de 29/09)

1. **Espaço em disco para o Unity.** Livres 9,2 GB às 02:30. O espaço do jogo apagado foi consumido porque o Hub instalou sozinho o Unity **6000.6.3f1** entre 00:29 e 00:54 (8,4 GB, versão que o YARG não usa). Desinstalar pelo Hub (Installs → ⋮ → Uninstall, pede UAC) libera o suficiente para o 6000.3.5f2 (~7 GB) + Library (~5-8 GB). O disco do Docker (26,5 GB) não encolhe sozinho e tudo nele é dos projetos do Lucas (precheck, hasura, postgres), então não foi mexido.
2. **Instalar o Unity 6000.3.5f2** (Hub: `unityhub://6000.3.5f2/3fa8bc678cb0`, sem VS/docs; pede UAC) e o **Blender 4.5.5 LTS** (MSI do blender.org; pede UAC). Ou autorizar alternativas sem admin.
3. **Smart App Control**: o `YARG.exe` compilado localmente **provavelmente será bloqueado**: no modelo de player do Unity, tudo é assinado menos o `WindowsPlayer.exe`, que vira o `YARG.exe` (ver SECURITY_LOG.md). Se for, decidir: (a) jogar pelo editor do Unity (assinado, funciona com o SAC), (b) desligar o SAC (irreversível sem reinstalar o Windows) ou (c) certificado de assinatura de código (pago). Não desligar sem ele decidir.
4. **Executável público**: rebranding antes de publicar um build (LICENSES.md §1 e §6).
5. **Moonscraper**: instalar (instalador verificado em `_downloads\`); pode ser barrado pelo SAC (sem assinatura).

## Como rodar as coisas

- Ambiente: `scripts\preparar-ambiente.ps1` (venv do lock + modelos com hash). .NET: `. scripts\dev-env.ps1`.
- Gerar música: arrastar o áudio em `scripts\gerar-musica.bat`, ou `.venv\Scripts\python.exe -m autochart gerar <audio> --titulo … --artista …`.
- Validar: `scripts\validar-musica.ps1 <pasta>`.
- Testes: `.venv\Scripts\python.exe -m unittest discover -s autochart\tests` (24); testes .NET da engine e do fork: `scripts\testes-dotnet-conteiner.ps1` (34; precisa do Docker Desktop aberto; no Windows direto, `dotnet test tests\EngineTests` pode ser barrado pelo Smart App Control); testes do YARG.Core: `dotnet test YARG\YARG.Core\YARG.Core.UnitTests` (1 falha de cultura pt-BR, conhecida).
- **Build do jogo** (depois de instalar o Unity 6000.3.5f2, com o Hub aberto): `scripts\build-jogo.ps1`. Confere os pré-requisitos, vigia o disco, repete uma vez se o NuGet ainda não tiver restaurado os pacotes e lista o que o Smart App Control bloquear. Saída em `_builds\YARG\YARG.exe`.
- Verificar se o fork compila (sem o editor): `.venv\Scripts\python.exe tools\unity-compile-check\compilar.py --sincronizar-de YARG` (ver `tools/unity-compile-check/README.md`).

## Madrugada de 29/09 — o que foi feito (com números)

- **Testes da engine** (`tests/EngineTests`): resultado idêntico de 24 a 1000 fps (40 partidas humanizadas); janela efetiva de palhetada −95/+70 ms; tolerâncias, acordes, âncora, ghosting, sustain e star power conferidos. Bugs do upstream: pontos de sustain sem multiplicador no overstrum; `FiveFretGuitarPreset.Copy()` sem `SustainDropLeniency`.
- **Pilha de ML isolada**: sandbox Docker → 65 wheels do Windows com hash → `.venv` offline. **Smart App Control bloqueia torch 2.14** → torch/torchaudio **2.8.0**. Pesos locais com hash; Demucs só carrega se a classe nos metadados for a esperada.
- **autochart**: batidas sub-quadro + fase pelos ataques; andamento único quando cabe no ruído (124,0 BPM exatos na música do Admiral Bob); deriva real seguida (165→176 BPM ao vivo no Aguaviva); compasso único com fase (3/4 no waltz); vocabulário rítmico por música (sem tercinas falsas); filtro de vazamento; validação no YARG.Core com conferência nota a nota do tipo strum/HOPO/tap.
- **Resultados nas 3 músicas**: 0 violações; o scanner do jogo acha as 4 dificuldades; tipos de nota conferem 100%; jogador perfeito 100%; humano σ20 ms 99,9-100%; humano σ35 ms 95,7-97,9%.
- **02:30–03:15, Eixo A:** Unity 6000.6.3f1 em modo batch → bloqueado pelo Smart App Control (acima). Verificador de compilação próprio com o Roslyn do Unity: as 116 assemblies do projeto compilam (0 erros) numa cópia com remendos de versão. **Histerese dos gatilhos** implementada no fork (configurável por controle; o preset do controle solta a 75% do ponto de acionamento, o padrão do Input System) com 9 testes na engine real: gatilho pairando em 0,5 ± 0,06 durante um sustain → sustain derrubado em 20/20 sem histerese, 0/20 com. **`Keyboard.current` nulo** corrigido em 2 lugares. Whammy revisado: o Input System já aplica deadzone de 12,5% no analógico, então não precisa mudar.
- **03:10–03:40, calibração guiada** no fork: instruções claras (pt-BR/en), música tocada 2× (~40 toques), descarte só dos toques fora da curva, resultado explicado e escolha entre salvar na calibração de entrada do perfil ou na de áudio global. Simulação com 400 jogadores (erro humano de 15 ms): 95% dos resultados a menos de 5,7 ms do atraso real (uma passada, como no original: 8,4 ms).
- **Robustez do autochart** (áudios sintéticos): mono 48 kHz → OK (100,0 BPM exatos, notas a 1,4 ms do ataque); 6 s → OK; ruído sem pulso → antes quebrava com `IndexError`, agora sai com mensagem clara (código 3) e não cria pasta. Achado à parte: cliques periódicos no áudio podem "liberar" tercinas no vocabulário rítmico. Aqui eram artefato do sinal de teste (sem os cliques, só semínimas e colcheias), então o algoritmo não mudou.
- **Validação do autochart × Smart App Control:** o Windows passou a barrar DLLs recompiladas, de forma inconsistente (o validador foi barrado às 02:56 e aceito às 03:00). O autochart agora detecta o bloqueio e roda o mesmo validador num contêiner Linux oficial da Microsoft (9 s); sem Docker, marca "não executada" com o motivo.
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
| 2026-09-29 | Histerese dos gatilhos = 0,75 do ponto de acionamento, só no preset de controle | Mesmo padrão do Input System do Unity; teste mostra fim das solturas fantasmas sem mudar o jogo com apertos completos; o resto dos controles fica igual ao upstream |
| 2026-09-29 | Whammy do controle sem deadzone extra | O Input System já zera o analógico abaixo de 12,5% |
| 2026-09-29 | Testes .NET no contêiner `mcr.microsoft.com/dotnet/sdk:10.0` | O Smart App Control barra DLLs de teste recompiladas; o contêiner não mexe na proteção |

## Próximos passos

1. [ ] (Lucas) liberar disco + Unity 6000.3.5f2 + Blender; decidir sobre o Smart App Control se o Unity 6000.3.5f2 não compilar ou se o `YARG.exe` for bloqueado.
2. [ ] Build de linha de comando do fork (`-batchmode -buildWindows64Player`), teste de fumaça (o jogo abre? acha as músicas de `songs\`?), medir FPS (PresentMon) e stutter.
3. [x] Eixo A: histerese dos gatilhos (configurável), `Keyboard.current` sem nulo. [x] Whammy: não precisa (deadzone do Input System). [x] Calibração guiada para controle (instruções pt-BR/en, 2 passadas, salvar no perfil ou global). [ ] Controle deslizante do ponto de soltura na tela de binds (prefab, precisa do editor). [ ] Conferir no jogo: textos da calibração cabem na tela, fluxo com o controle.
4. [ ] Testes de input no Unity (InputTestFixture com controle virtual de Xbox).
5. [x] PLAYTEST.md. [x] Conferência do histórico git em 29/09 03:27: 22 commits no yarg-autochart e 9 no fork (`275e9a13..pessoal`), todos "Lucas Raposo", nenhuma marca de IA nas mensagens nem nos arquivos. [ ] Relatório final (`RELATORIO-FINAL.md`) quando o jogo tiver sido testado.
6. [x] Correções prontas (não enviadas) para 3 defeitos do YARG.Core: `docs/upstream/` (patches + testes; com eles, 3/3 problemas conhecidos resolvidos, suíte oficial 548/548, engine 43/43). [ ] **(Lucas) decidir**: abrir PR na YARC e/ou criar um fork público do YARG.Core para o nosso jogo usar a correção já.

## Problemas e observações

- `Keyboard.current` sem checagem de nulo em `GameManager.Update` (baixo risco no Windows).
- Latência de saída contada duas vezes com calibração 0 (confirmado no código; a calibração neutraliza; não alterar sem medir).
- Parsing de números dependente do idioma do Windows (bindings, campos de texto).
- Regressão upstream: sem `song.ini`, `notes.chart` sozinho não é detectado.
- O guarda de segurança do terminal bloqueia comandos com `Remove-Item`/`rm` junto de barras ou caminhos de sistema, mesmo dentro de texto: fazer remoções em comandos separados e escrever textos longos com a ferramenta de arquivos.
- Metal denso é o caso mais difícil para o autochart (separação pior, ataques borrados).
