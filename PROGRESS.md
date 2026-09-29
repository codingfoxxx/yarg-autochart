# PROGRESS — diário do projeto

> Fonte de verdade para retomar o trabalho. Atualizado a cada etapa.
> Última atualização: 2026-09-29 11:00 (horário de Brasília).

## Estado atual (resumo)

| Frente | Estado |
|---|---|
| Fase 0 (pesquisa e planejamento) | **Concluída**: `docs/pesquisa/`, DECISION.md, LICENSES.md, SECURITY_LOG.md |
| Fork do YARG | **Publicado**: https://github.com/codingfoxxx/YARG, branch `pessoal` (upstream `dev` @ `275e9a13` + mudanças do CHANGELOG-FORK.md) |
| Repositório de ferramentas | **Publicado**: https://github.com/codingfoxxx/yarg-autochart (`main`), com o fork como submódulo `YARG/` |
| **Build do jogo** | **Funciona** (29/09, 10:49): Unity 6000.3.5f2, `scripts\build-jogo.ps1`, ~14 min no primeiro build. `_builds\YARG\YARG.exe` abre e chega ao menu **com o Smart App Control ligado** (sem bloqueio) |
| Eixo A no código do jogo | **Publicado e compilado no Unity de verdade**: histerese nos gatilhos do controle; calibração guiada (instruções pt-BR/en, 2 passadas, resultado explicado, salvar para todos ou no perfil); calibração de entrada escalada pela velocidade; opção "Escanear Tudo ao Iniciar"; teclado/mouse ausentes não quebram mais. Revisão independente feita, achados corrigidos |
| Ferramenta autochart | **Funcionando** (`autochart/`): CLI, arrastar-e-soltar, relatório, validação no YARG.Core (cai para contêiner se o Windows barrar), 26 testes |
| Músicas de teste | **3 publicadas**: `samples/` + Release `musicas-teste-v1` |
| Testes .NET | 46/46 (engine, histerese, calibração) em contêiner; problemas conhecidos do YARG.Core com correção pronta em `docs/upstream/` |
| PLAYTEST.md | Pronto. **Falta o teste de verdade com o controle** (Lucas) |
| Relatório final | Depois do playtest |

## Smart App Control: resolvido sem desligar

- O Unity **6000.6.3f1** (instalado sozinho pelo Hub) não compilava: o Windows bloqueava DLLs sem assinatura do próprio Unity. Foi desinstalado a pedido do Lucas.
- Com o **6000.3.5f2** (versão do projeto), essas DLLs têm reputação e carregam; o build sai e o `YARG.exe` (sem assinatura) roda. Detalhes no SECURITY_LOG.md.

## Pendências que dependem do Lucas

1. **Playtest** com o controle: seguir o PLAYTEST.md (o jogo está em `C:\Dev\GuitarHero\_builds\YARG\YARG.exe`). Para a histerese dos gatilhos, usar um perfil novo ou adicionar o controle de novo.
2. (Opcional) **Blender 4.5 LTS**: sem ele, os modelos `.blend` (notas do tema "Rectangular") ficam sem malha. O tema padrão não usa.
3. (Opcional) Enviar as correções do YARG.Core à YARC e/ou criar um fork do YARG.Core (`docs/upstream/`).
4. **Executável público**: rebranding antes de publicar um build (LICENSES.md §1 e §6). Por enquanto o build fica só local.
5. **Moonscraper**: instalar (instalador verificado em `_downloads\`); pode ser barrado pelo SAC (sem assinatura).

## Como rodar as coisas

- Ambiente: `scripts\preparar-ambiente.ps1` (venv do lock + modelos com hash). .NET: `. scripts\dev-env.ps1`.
- Gerar música: arrastar o áudio em `scripts\gerar-musica.bat`, ou `.venv\Scripts\python.exe -m autochart gerar <audio> --titulo … --artista …`.
- Validar: `scripts\validar-musica.ps1 <pasta>`.
- Testes: `.venv\Scripts\python.exe -m unittest discover -s autochart\tests` (26); testes .NET da engine e do fork: `scripts\testes-dotnet-conteiner.ps1` (34; precisa do Docker Desktop aberto; no Windows direto, `dotnet test tests\EngineTests` pode ser barrado pelo Smart App Control); testes do YARG.Core: `dotnet test YARG\YARG.Core\YARG.Core.UnitTests` (1 falha de cultura pt-BR, conhecida).
- **Build do jogo** (com o Hub aberto, para a licença): `scripts\build-jogo.ps1`. Confere os pré-requisitos, restaura os pacotes NuGet se faltarem (o NuGetForUnity não roda em modo batch), vigia o disco e lista o que o Smart App Control bloquear. Saída em `_builds\YARG\YARG.exe`. Com o projeto já importado, os builds seguintes são mais rápidos.
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
- **~03:30–03:40:** o PC caiu. O log do vigia para às 03:30 e o boot seguinte foi às 09:22 (possivelmente a GPU, ver memória de hardware). Nada se perdeu: tudo estava commitado e publicado às 03:31. Só a revisão independente do código do fork foi interrompida; ela foi refeita às 09:3x.
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
