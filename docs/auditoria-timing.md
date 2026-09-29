# Auditoria de timing — engine de 5 trastes

Estado em 2026-09-29. Base: YARG `dev` @ `275e9a13`, YARG.Core @ `e2d44e8d`, preset de engine **Default**.
Testes em [`tests/EngineTests`](../tests/EngineTests) (`dotnet test tests/EngineTests`).

## Como foi testado

- Charts de teste escritos em `.chart` e carregados com o **parser real** do YARG.Core (`SongChart.FromDotChart`).
- Engine montada como o jogo monta: `EnginePreset.Default.FiveFretGuitar.Create(...)` + `YargFiveFretGuitarEngine` + `SetSpeed(1.0)`.
- **Laço de frames igual ao do jogo:** a cada frame, os inputs cujo timestamp já passou são enfileirados (`QueueInput`) e a engine é atualizada com o tempo do frame (`Update`). Taxas de 24 a 1000 fps, com e sem variação aleatória de ±10% entre frames.
- Jogador simulado ("humano"): aperta os trastes 15 ms antes de palhetar, faz HOPO/tap só com os trastes, segura sustains, com erro de tempo gaussiano por nota.

Não testado aqui (precisa do Unity ou de hardware): como os eventos do controle recebem o timestamp no Input System, o polling do XInput, a latência de áudio e vídeo reais. Ver a seção "Lado do jogo".

## Resultados (25 testes aprovados)

| Aspecto | Resultado |
|---|---|
| **Independência de FPS** | 40 partidas humanizadas (σ = 35 ms) × 7 taxas de quadro × com/sem jitter: **resultado idêntico** (acertos, overstrums, ghosts, combo, pontuação, star power) em todas. O julgamento usa o timestamp de cada input, não o frame. |
| Jogo perfeito | 27/27 notas, combo cheio, zero overstrum, em 30/60/144/240 fps |
| **Janela efetiva da palhetada** | **−95 ms a +70 ms**, contínua. Nominal ±70 ms; os 25 ms extras antes vêm da "tolerância curta" de palhetada (uma palhetada logo antes da janela ainda vale quando a nota entra nela). É intencional no desenho da engine, não um bug |
| Traste depois da palhetada | Vale até **50 ms** depois (tolerância de palhetada); com 60 ms, overstrum |
| Acorde palhetado | Exige exatamente os trastes do acorde (nem a mais, nem a menos) |
| Nota simples | Aceita trastes mais baixos segurados (âncora); não aceita traste mais alto |
| HOPO | Vale só com o traste se houver combo; depois de um erro, exige palhetada; uma palhetada até 80 ms depois de um HOPO é absorvida (sem overstrum) |
| Ghosting | Encostar num traste errado acima bloqueia o HOPO seguinte (anti-ghosting padrão) |
| Sustain | Soltar e reapertar em até 25 ms mantém o sustain; 35 ms ou mais derruba; soltar cedo não conta como erro de nota |
| Star power | Duas frases completas = 50%, ativação funciona; errar uma nota da frase = nenhum ganho |
| Overstrum | Palhetada no vazio zera o combo |
| Input entregue atrasado | Um evento que chega à engine depois de ela já ter passado do timestamp dele é julgado no tempo em que chegou (documentado; no jogo só ocorre se o evento do dispositivo atrasar mais de um frame) |

## Problemas encontrados

| # | Problema | Severidade | Evidência | Ação |
|---|---|---|---|---|
| 1 | **Overstrum durante um sustain** soma os pontos já segurados **sem multiplicador** e não os registra em `SustainScore` (`GuitarEngine.Overstrum`), enquanto soltar o traste no mesmo ponto passa por `AddScore` (com multiplicador) | Baixa (pontuação) | Teste `KnownIssue_SustainPointsLostToOverstrum_UseTheMultiplier`: 408 pontos de sustain ao soltar × 0 no overstrum; total 3758 × 3452 | Candidato a PR no upstream; exige fork do YARG.Core para corrigir aqui |
| 2 | `FiveFretGuitarPreset.Copy()` **não copia `SustainDropLeniency`**: "Copy of…" no menu de presets volta a tolerância de sustain ao padrão (25 ms) | Baixa (configuração) | Teste `KnownIssue_PresetCopy_KeepsSustainDropLeniency`: 0,045 → 0,025 | Idem (correção de uma linha) |
| 3 | Teste do próprio YARG.Core `EngineTimerTests.ToString_FormatsStartedTimerWithSixDecimalPlaces` falha em Windows pt-BR (vírgula decimal) | Nenhuma (só teste) | 547/548 aprovados no pt-BR; 548/548 com globalização invariante | Documentado no BUILD.md |
| 4 | **Overstrum perto do fim de um sustain soma os pontos de novo**: `Overstrum` (e `KeysEngine.Overhit`) não confere `HasFinishedScoring`, e depois do "burst" (Resolution/4 ticks antes do fim) o sustain já pontuou | Baixa (pontuação; o erro dá pontos) | Teste `KnownIssue_OverstrumAfterSustainBurst_DoesNotCountThePointsTwice`: 4150 segurando × 4349 com overstrum 60 ms antes do fim | Correção dos itens 1, 2 e 4 pronta em `docs/upstream/` (não enviada) |

Observação de desenho (não é bug): `EngineParameters.SongSpeed` nasce 0 e só vale depois de `SetSpeed`. O jogo sempre chama; qualquer ferramenta que use a engine precisa chamar também (o nosso harness chamava errado no começo e isso zerava a tolerância de sustain).

## Lado do jogo (Unity) — revisão de código, ainda sem teste executável

Ver `docs/pesquisa/mapa-input-engine.md`. Confirmados pela leitura:

- **Gatilhos analógicos sem histerese** (`ButtonBinding.cs:85`): `pressionado = valor ≥ 0,5`. Com gatilho parado perto do meio, pode haver pressões/solturas fantasmas; o debounce de 5 ms só filtra oscilações muito rápidas. **Corrigido no fork** (histerese configurável; preset do controle solta a 37,5%). Teste `AnalogTriggerTests` com a engine real e um gatilho XInput simulado (250 Hz, 8 bits): dedo pairando em 0,5 ± 0,06 durante um sustain → sem histerese o sustain caiu em 20 de 20 execuções (504 solturas falsas); com histerese, em 0 de 20. Aperto/soltura completos: resultado idêntico com e sem histerese.
- **Whammy** (revisado depois de ler o código do Input System; li a versão 1.20, que o Unity 6000.6 baixou na cópia de verificação; o projeto usa a 1.17, a conferir quando o 6000.3.5f2 estiver instalado): qualquer evento do eixo reinicia o timer e a deadzone do binding é 0, **mas** os eixos do analógico (`leftStick/x`) já passam pelo processador `axisDeadzone` do Input System (mínimo 0,125 neste projeto). O ruído do analógico em repouso vira 0 antes de chegar ao binding, então não gera star power. Só um analógico com desvio acima de 12,5% (controle gasto) geraria eventos. Sem mudança no fork.
- **Latência de áudio contada duas vezes** no modo compartilhado com calibração 0 e "Account for hardware latency" ligado. Pode compensar por acaso latências não modeladas; a calibração neutraliza; não será alterado sem medição.
- `Keyboard.current` sem checagem de nulo em `GameManager.Update`.
- Parsing de números dependente do idioma do Windows nos bindings e campos de texto.

Esses itens serão verificados/corrigidos quando o Unity estiver instalado (build + testes de modo play com controle virtual).
