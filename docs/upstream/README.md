# Correções prontas para o YARG.Core (não enviadas)

Três defeitos do YARG.Core achados na auditoria da engine, com correção e testes. **Nada foi enviado ao projeto oficial**: abrir um PR na YARC (ou criar um fork público do YARG.Core para usar a correção no nosso jogo) é decisão do Lucas. O fork do jogo continua usando o YARG.Core original (`e2d44e8d`).

Base: `YARC-Official/YARG.Core` @ `e2d44e8d`. Aplicar com `git apply <patch>` na raiz do YARG.Core.

## 0001: `Copy()` dos presets esquece a tolerância de soltura do sustain

- **Defeito:** `FiveFretGuitarPreset.Copy()` e `ProKeysPreset.Copy()` não copiam `SustainDropLeniency`. No menu de presets de engine, "Copiar" um preset personalizado volta esse valor ao padrão (25 ms) sem avisar.
- **Correção:** uma linha em cada `Copy()` (`0001-preset-copy-sustain-drop-leniency.patch`).
- **Teste:** `KnownIssue_PresetCopy_KeepsSustainDropLeniency` (`tests/EngineTests`): 0,045 → 0,025 antes; 0,045 depois.

## 0002: pontos de sustain interrompido por overstrum/overhit

`GuitarEngine.Overstrum()` e `KeysEngine.Overhit()` pontuam os sustains em andamento de um jeito diferente de quando o jogador solta o traste (`UpdateSustains`):

1. **Sem multiplicador e fora do `SustainScore`:** somam direto em `CommittedScore`. Teste `KnownIssue_SustainPointsLostToOverstrum_UseTheMultiplier`, com um sustain a 4x interrompido na metade: soltando, 3758 pontos (408 de sustain); com overstrum no mesmo ponto, 3452 (0 de sustain).
2. **Contagem dupla perto do fim:** não conferem `HasFinishedScoring`. A partir de `Resolution/4` ticks antes do fim do sustain (o "burst"), todos os pontos já foram somados; um overstrum nesse intervalo soma os pontos de novo, então **o erro dá pontos**. Teste `KnownIssue_OverstrumAfterSustainBurst_DoesNotCountThePointsTwice`: segurando até o fim, 4150; com overstrum 60 ms antes do fim, 4349.

- **Correção** (`0002-broken-sustain-scoring.patch`): método `CommitBrokenSustainPoints` em `BaseEngine<...>`, com a mesma conta do caminho de "sustain solto" em `UpdateSustains` (multiplicador via `AddScore`, soma em `SustainScore` sem o dobro do star power) e que não faz nada se o sustain já terminou de pontuar. `Overstrum` e `Overhit` passam a usá-lo. O terceiro argumento de `OnSustainEnd` continua com o valor de antes da chamada.
- **Depois da correção:** overstrum no meio = 3758 com 408 de sustain (igual a soltar); overstrum depois do burst = 4150 (igual a segurar).
- **Atenção para o upstream:** muda a pontuação, então replays antigos com overstrum durante sustain passam a dar outro placar na verificação. O projeto provavelmente vai querer subir a versão da engine dos replays (`ENGINE_VERSION`).

## Verificação (29/09, em contêiner Linux, porque o Smart App Control barra as DLLs de teste no Windows)

| Suíte | Sem os patches | Com os patches |
|---|---|---|
| `tests/EngineTests` (43 testes) | 43/43 | 43/43 |
| Problemas conhecidos (3 testes `Explicit`) | 0/3 | **3/3** |
| `YARG.Core.UnitTests` (suíte oficial) | 548 aprovados, 2 ignorados | 548 aprovados, 2 ignorados |

Comandos: `scripts\testes-dotnet-conteiner.ps1 -Filtro "Category=KnownIssue"` e `scripts\testes-yargcore-conteiner.ps1`.
