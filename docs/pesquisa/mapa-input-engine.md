# Mapa de input, timing, calibração e engine de 5 trastes do YARG

Mapeamento por leitura de código (2026-09-28). Base: YARG `dev` @ `275e9a13` (Unity 6000.3.5f2), YARG.Core @ `e2d44e8d`.
Caminhos relativos à raiz do projeto Unity; `core:` = submódulo `YARG.Core/`.
Itens marcados "(verificar)" dependem de internals do Unity Input System, PlasticBand ou HIDrogen, que não estão no repositório.
Este é o ponto de partida da auditoria de timing (Eixo A); as suspeitas estão no fim.

## 1. Pipeline de input

- Configuração: `Assets/Settings/InputSystem.inputsettings.asset` (update dinâmico, press point 0,5, release 0,75, deadzone de stick 0,125/0,925). Só o Input System novo (`ProjectSettings.asset:984`), `runInBackground: 1`.
- Polling de dispositivos que precisam de polling (XInput): configuração `InputPollingFrequency`, padrão **250 Hz**, faixa 60-1000 (`Assets/Script/Settings/SettingsManager.Settings.cs:226-228`, aplicado em `Assets/Script/Input/InputManager.cs:71`).
- Cada binding registra `InputState.AddChangeMonitor` (`Assets/Script/Input/Bindings/ControlBinding.cs:425`). Cadeia: `NotifyControlStateChanged(control, time, ...)` → `SingleButtonBinding.UpdateState` → `ButtonBinding.OnStateChanged` → `FireInputEvent` gera um `GameInput` (`core:YARG.Core/Input/GameInput.cs`) → `BasePlayer.OnGameInput` (`Assets/Script/Gameplay/Player/BasePlayer.cs:302`).
- **Timestamps por evento, com precisão menor que um frame**: vêm do monitor de mudança, limitados a `min(time, InputState.currentTime)` (`ControlBinding.cs:535`). Exceções carimbadas com o tempo do frame: eventos liberados pelo debounce (`ButtonBinding.cs:279-307`) e reenvios ao despausar.
- Conversão para o tempo do chart: `SongRunner.GetInputTime(t) = âncora + (t − âncoraInputSystem) × velocidade` (`Assets/Script/Playback/SongRunner.cs:425-428`). `BasePlayer.OnGameInput` (`:354-404`) soma a calibração de input do perfil, chama `Engine.QueueInput` e grava no replay.
- Ordem por frame: `GameManager.Update` (`[DefaultExecutionOrder(-1)]`) → `_songRunner.Update()` → `GameplayUpdate` de cada jogador → `BaseEngine.Update(InputTime + calibração)`.
- Relógios (`SongRunner.cs:439-446`): `InputTime` (o da engine), `SongTime = InputTime + AudioCalibration×v`, `VisualTime = InputTime + VideoCalibration×v`. **A engine julga pelo InputTime, nunca pelo relógio do áudio.**
- **Veredito:** o input é processado na thread principal, uma vez por frame, mas cada evento mantém seu timestamp próprio e a engine o consome nesse instante. O julgamento independe do FPS, exceto: eventos liberados pelo debounce, granularidade do polling e corridas raras.

## 2. Relógio de áudio e sincronia

- Desenho (`docs/song_sync.md` no repositório do YARG): o relógio do Input System é o mestre; o áudio é escravo.
- Cadeia: stems → stream de tempo BASS_FX → mixer → buffer nativo de leitura antecipada (`Native/YargAudio`) → saída (compartilhada, ASIO ou WASAPI exclusivo).
- Posição "ouvida" = posição decodificada − (fila + atraso do endpoint), num snapshot nativo consistente (`Native/YargAudio/src/ReadAheadStream.cpp:179-213`).
- Controle: `Control = decodificado − v×atraso − OutputLatency×v`; erro = alvo − Control. Correção começa em 3 ms e para em 1,5 ms, aplicada como mudança de tempo **sem alterar o tom**, com janela de acomodação (`SongRunner.cs:796-999`). Sem seek durante a música.
- Buffer de reprodução padrão 75 ms, cresce sozinho em underrun (`SettingsManager.Settings.cs:429-437`).
- Commits recentes relevantes: #1558 (sincronizador novo), #1589 (desync), 63226ac1 (offset por música), ASIO/WASAPI exclusivo.

## 3. Calibração

- Globais (`settings.json`): `AudioCalibration` (ms, padrão 0; maior = áudio mais cedo), `VideoCalibration` (ms, padrão 0), `AccountForHardwareLatency` (padrão ligado; soma a latência estimada do dispositivo), autocalibração (desligada por padrão), `UseSongOffsetCalibration` (padrão ligado).
- **Por perfil:** `YargProfile.InputCalibrationMilliseconds` (ms, padrão 0), editado num campo de texto (`Assets/Script/Menu/ProfileList/ProfileSidebar.cs:422-431`), salvo em `profiles/profiles.json`. Aplicado como −segundos ao tempo dos eventos e ao relógio da engine.
- Calibrador (`Assets/Script/Menu/Calibrator/Calibrator.cs`): toca `calibration_music.ogg` a 80 BPM; o jogador aperta qualquer botão de menu no tempo; descarta amostras com mais de 50 ms de desvio do intervalo esperado; exige mais de 8 amostras; usa a mediana; grava só a **calibração de áudio**. Quase não tem texto de instrução.
- Autocalibração em jogo (`Assets/Script/Helpers/AutoCalibrator.cs`): a cada 20 acertos, filtro IQR, mediana, amortecimento de 50%.

## 4. Bindings (mapeamento de controles)

- Classes: `ControlBinding`, `ButtonBinding`/`SingleButtonBinding`, `AxisBinding`, `IndividualButtonBinding`, `BindingCollection`, `ProfileBindings` (salvo em `profiles/bindings.json`).
- Ações de 5 trastes: `GuitarAction` Fret1-5 (verde…laranja), StrumUp, StrumDown, Whammy, StarPower, trastes de solo (`core:YARG.Core/Input/InputActions.cs:44-116`).
- Padrões:
  - Teclado: 1-5 trastes, setas cima/baixo palhetada, Backspace star power, `;` whammy.
  - Guitarras PlasticBand: mapeamento direto; star power em select, inclinação e pedal.
  - **Controle genérico (Xbox)** (`Assets/Script/Input/Bindings/Defaults/BindingCollection.Gamepad.cs:76-95`): **verde = LT, vermelho = LB, amarelo = RB, azul = RT, laranja = A**, palhetada no **D-pad cima/baixo**, star power no **View/Select**, whammy no **analógico esquerdo X**. Só vale depois que o controle é adicionado a um perfil; no Windows o jogo pergunta "que tipo de controle é" (`Assets/Script/Menu/ProfileList/ProfileView.cs:262-273, 368-401`). Perfis automáticos ignoram gamepads comuns (`Assets/Script/Player/PlayerContainer.cs:909-952`).
- Fluxo de mapear: Perfil → Edit Binds → adicionar → aperte o controle. "Quick bind" só existe para bateria e pro keys, não para guitarra.
- Parâmetros por controle: invertido, **PressPoint** (padrão 0,5), modo e limiar de debounce (5 ms). Eixos: mínimo, máximo, deadzones (padrão 0).
- **Botão analógico: `IsPressed = valor >= PressPoint`, sem histerese** (`Assets/Script/Input/Bindings/ButtonBinding.cs:85`).
- Sem detecção de conflito entre ações.

## 5. Engine de 5 trastes (YARG.Core)

- Classes: `BaseEngine`, `BaseEngine<...>` (`BaseEngine.Generic.cs`), `GuitarEngine`, `YargFiveFretGuitarEngine`, `HitWindowSettings`, `EngineTimer`, `EnginePreset`.
- Atualização: `QueueInput` (entrada fora de ordem é empurrada para frente com aviso, `BaseEngine.cs:336-365`); `Update(tempo)` processa cada entrada no seu próprio instante e agenda atualizações exatas nos limites das janelas, dos sustains e dos timers. **O julgamento não depende do FPS.**
- `MutateStateWithInput` (`YargFiveFretGuitarEngine.cs:78-138`): star power (botão), whammy (**qualquer evento reinicia o timer, o valor do eixo é ignorado**), palhetada só ao apertar, trastes alteram a máscara de botões.
- Janela de acerto: padrão estática de **140 ms no total (±70 ms)**; dinâmica opcional.
- Palhetada: tolerância de 50 ms (25 ms sem nota na janela). HOPO: tolerância de 80 ms. Anti-ghosting ligado por padrão. Sustain: tolerância de soltura de 25 ms.
- Star power: +25% por frase; barra cheia = 8 compassos; ativar exige ≥ 50%.
- Pontuação: 50 por nota, sustain 25 por batida, multiplicador `min(combo/10+1, 4)` (baixo 6), dobra no star power.
- Presets (`core:YARG.Core/Game/Presets/EnginePreset.Defaults.cs`): Default, Casual (sem anti-ghost, frente infinita), Precision (janela dinâmica 120/40 ms), Solo Taps.

## 6. Testes e verificação de replay

- `core:YARG.Core.UnitTests` (NUnit 4.5.1, net10.0): testes de janela, timer, sustain, estatísticas, ghosting do 6 trastes, BRE, bots. **Não há teste de ponta a ponta do 5 trastes com inputs temporizados** (strum/HOPO/tolerâncias).
- `ReplayCli` (net8.0): `verify`, `simulate_fps` (roda o replay em 50 taxas de quadro), `dump_inputs`. Replays = inputs gravados com tempo, re-executados de forma determinística.

## 7. Bot, linha de comando, depuração, FPS

- Bot: perfil com `IsBot`; aperta cada nota exatamente no tempo.
- Linha de comando: `-offline`, `-verbose-replays`, `-lang`, `-download-location`, `-persistent-data-path`.
- Overlay de depuração: Ctrl+Tab no jogo (calibração, relógios, erros de sincronia, eventos de input). Contador de FPS pela configuração `FpsStats`.
- VSync ligado por padrão; limite de FPS 60 (fundo: 10).

## Suspeitas a verificar (auditoria)

1. **Latência de saída contada duas vezes** — *confirmado no código* (`SongRunner.cs:611-622`, `BassSharedOutput.cs:22-27`, `BassLatencyProvider.cs`): no modo compartilhado do Windows, o mesmo valor (buffer + período + update ≈ 35 ms) entra no atraso do endpoint e de novo em `PlaybackLatency` quando "Account for hardware latency" está ligado. Com calibração 0, o áudio tende a sair ~35 ms adiantado em relação ao modelo, o que pode compensar por acaso latências não modeladas (mixer do Windows, DAC). Rodar o calibrador neutraliza. Só uma medição em loopback decide.
2. Calibração de input não é escalada pela velocidade da música (`BasePlayer.cs:56,276,395`).
3. Polling XInput a 250 Hz: 0-4 ms de atraso e jitter não compensados.
4. Corrida rara: eventos atrasados com timestamps anteriores são empurrados para frente pela engine.
5. **Debounce e botões analógicos:** solturas dentro dos 5 ms saem com o tempo do frame; **sem histerese** em gatilhos analógicos (LT/RT como trastes podem "trepidar" perto de 50%).
6. **Whammy:** qualquer evento reinicia o timer; deadzone do eixo 0 → ruído do analógico pode gerar star power.
7. Pontuação de sustain no overstrum soma sem multiplicador (`GuitarEngine.cs:176-186`).
8. `FiveFretGuitarPreset.Copy()` não copia `SustainDropLeniency` (`EnginePreset.Instruments.cs:129-143`).
9. `EngineTimer.StartWithOffset` com offset não escalado.
10. Autocalibrador enviesado pelos acertos na borda da janela.
11. Filtro do calibrador pode descartar amostras em cascata.
12. Replay: `ENGINE_VERSION` não mudou apesar de correções de engine posteriores.
13. Frets apertados durante a pausa podem se perder ao despausar.
14. Estatística `HoposStrummed` nunca é incrementada.
15. **`Keyboard.current` sem checagem de nulo** em `GameManager.Update` (`Assets/Script/Gameplay/GameManager.cs:299,305`) — confirmado; baixo risco no Windows.

## Arquivos-chave da auditoria

1. `Assets/Script/Playback/SongRunner.cs`
2. `Assets/Script/Input/InputManager.cs`
3. `Assets/Script/Input/Bindings/ControlBinding.cs`, `ButtonBinding.cs`, `DebounceTimer.cs`
4. `Assets/Script/Gameplay/Player/BasePlayer.cs`
5. `core:YARG.Core/Engine/BaseEngine.cs` e `BaseEngine.Generic.cs`
6. `core:YARG.Core/Engine/Guitar/Engines/YargFiveFretGuitarEngine.cs` e `GuitarEngine.cs`
7. `core:YARG.Core/Engine/HitWindowSettings.cs`, `EngineTimer.cs`
8. `core:YARG.Core/Game/Presets/EnginePreset.*.cs`
9. `Assets/Script/Menu/Calibrator/Calibrator.cs`, `Assets/Script/Helpers/AutoCalibrator.cs`
10. `Assets/Script/Audio/Bass/*` e `Native/YargAudio/src/ReadAheadStream.cpp`
11. `core:YARG.Core/Replays/Analyzer/ReplayAnalyzer.cs`, `core:ReplayCli/`
