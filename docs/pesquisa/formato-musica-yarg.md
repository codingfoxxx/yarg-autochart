# Formato de música do YARG (guitarra 5 trastes) — especificação a partir do código

Levantado por leitura estática do código em 2026-09-28/29 (nada foi executado).
Versões: YARG `dev` @ `275e9a13`, YARG.Core @ `e2d44e8d`.

Prefixos das citações:
- `C:` = `YARG/YARG.Core/YARG.Core/` (biblioteca central)
- `U:` = `YARG/` (projeto Unity)
- `ND:` = documentação de formatos do TheNathannator (GuitarGame_ChartFormats, `docs/Chart-File-Formats/`)
- `YD:` = fontes da documentação oficial do YARG (repositório `YARC-Official/docs`)

## 1. Descoberta e cache

**Pastas varridas**
- Raízes: lista `SongFolders` do `settings.json` (mais o setlist do launcher). `U:Assets/Script/Song/SongContainer.cs:153-158`, `U:Assets/Script/Settings/SettingsManager.Settings.cs:137`.
- A varredura é recursiva. Uma pasta que vira entrada "ini" é folha: subpastas dela não são visitadas (log `LooseChart_Warning`). `C:Song/Cache/CacheHandler.cs:637-736` (regra de folha 712-720).
- Arquivos `.sng` e `.yargsong` também são lidos (`CacheHandler.cs:764-775`, `ScanSngFile` 862-899). Outros arquivos são testados como pacote CON do Xbox (`:776-783`).
- Pasta chamada `songs` com `songs.dta` é tratada como RB desempacotado (`:664-683`). Pastas `songs_updates`/`songs_upgrades` são mods de RB (`:648-661, 697-709`). **Não usar esses nomes.**
- Nomes de arquivo sem diferenciar maiúsculas (chaves em minúsculas). Duas entradas que só diferem na caixa são descartadas. `C:Song/Cache/FileCollection.cs:29-43`.
- Arquivos "só na nuvem" do OneDrive (`RECALL_ON_DATA_ACCESS`) são ignorados. `FileCollection.cs:14-21`.

**Nomes exatos**
- Metadados: `song.ini`.
- Chart: o primeiro que existir entre `notes.mid`, `notes.midi`, `notes.chart`, `notes.txt` (UltraStar). `C:Song/Entries/Ini/SongEntry.IniBase.cs:39-45`, `CacheHandler.cs:808-816`. Outros nomes nunca são lidos.
- **Regressão neste commit:** `int i = hasIni ? 0 : 3` (`CacheHandler.cs:808-810`, commit f47e2809; antes era `: 2`). Sem `song.ini`, só `notes.txt` é tentado: um `notes.chart` sozinho não aparece. **Sempre gerar `song.ini`.**
- Áudio obrigatório: pelo menos um `<stem><ext>`, senão `NoAudio` (`CacheHandler.cs:822-826`).
  - Stems: `song guitar bass rhythm keys vocals vocals_1 vocals_2 drums drums_1..drums_4 crowd`.
  - Extensões: `.opus .ogg .mp3 .wav .aiff`. **FLAC e M4A não.**
  - `preview.*`, `*_clean`, `*_explicit` não contam. `IniBase.cs:18-35`, `FileCollection.cs:78-88`.

**Requisitos mínimos de uma entrada "ini"**
1. `song.ini` com cabeçalho `[song]` (`C:IO/Ini/YARGIniReader.cs:54-82`).
2. Chave `name` (do ini ou do `[Song] Name` do `.chart`) (`IniBase.cs:204-207, 393`).
3. Pelo menos uma nota jogável em alguma parte/dificuldade (`IniBase.cs:199-202`).
4. O áudio acima.
5. Resolução ≥ 1 (`.chart`) ou divisão MIDI ≠ 0 (`IniBase.cs:388-391`, `C:Song/Entries/SongEntry.Scanning.cs:12-16`).

**Cache**
- `songcache.bin` e `badsongs.txt` na pasta persistente (`U:Assets/Script/Helpers/PathHelper.cs:132-133`).
- Pasta persistente = `Application.persistentDataPath` + `release`/`nightly`/`dev` (`PathHelper.cs:99-106`); no Windows: `%USERPROFILE%\AppData\LocalLow\YARC\YARG\<canal>\`.
- Linha de comando `-persistent-data-path <pasta>` troca essa pasta (`U:Assets/Script/Persistent/CommandLineArgs.cs:36,79-84`). **Útil para testes isolados.**
- Na mesma pasta: `settings.json`, `profiles/profiles.json`, `profiles/bindings.json`, `scores/`, `song_offsets.json`, `logs/AAAA-MM-DD[_n].log`.
- `CACHE_VERSION = 26_09_04_00` (`CacheHandler.cs:38`); versão diferente descarta o cache inteiro.
- Entrada do cache vale só se `max(LastWrite, Creation)` do chart e do ini baterem exatamente (`C:Song/Entries/Ini/SongEntry.UnpackedIni.cs:310-338`).
- **Ao abrir o jogo roda só a varredura rápida, que NÃO vê músicas novas ou editadas** (`CacheHandler.cs:78-102, 1390-1398`). Para ver: Configurações → Song Manager → Refresh All Caches, ou o refresh da biblioteca (`U:Assets/Script/Menu/MusicLibrary/MusicLibraryMenu.cs:1396`). Apagar `songcache.bin` força varredura completa.
- Editar chart/ini depois da varredura sem re-varrer: "Chart requires a rescan!" ao tocar (`UnpackedIni.cs:243-265`).
- O hash da música é o SHA-1 dos bytes do arquivo de chart (`IniBase.cs:213`).

## 2. Áudio

- Cada stem tenta `.opus .ogg .mp3 .wav .aiff` nessa ordem (`UnpackedIni.cs:102-121, 268-279`).
- Só `song.ogg`: um único stem de fundo, sem silenciar a guitarra ao errar (`U:Assets/Script/Gameplay/GameManager.Audio.cs:111-117`). Com `guitar.ogg` separado, o jogo abafa a guitarra nos erros.
- Mixer interno a 44,1 kHz estéreo float; o BASS reamostra qualquer entrada (`U:Assets/Script/Audio/Bass/BassSong.cs:74`).
- Falha ao decodificar não é pega na varredura: a música aparece e falha ao tocar ("Failed to load audio!").
- `delay` no `song.ini`: inteiro em ms; positivo = notas mais tarde que o áudio. `SongOffset = -(delay + override)` (`U:Assets/Script/Playback/SongRunner.cs:289`). `[Song] Offset` do `.chart` é em segundos e só vale se `delay` for 0/ausente (`SongMetadata.cs:539-546`).
- Offset por música (commit 63226ac1): `song_offsets.json` = `{ "<SHA1 do chart>": ms }` (`U:Assets/Script/Song/SongOffsetContainer.cs:14-61`). Regerar o chart muda o hash e perde o ajuste.
- Duração: `song_length` (ms) é só para exibição; a partida dura `max(áudio, fim do chart)`, salvo evento `[end]`.

## 3. song.ini

- UTF-8 com ou sem BOM (UTF-16/32 com BOM também). Chaves e seções em minúsculas. Valor até o fim da linha, sem aspas, sem comentário no fim da linha.
- Bool: `1`/`true`. Inteiro inválido vira 0.
- Tags lidas: `name`, `artist`, `album`, `genre`, `sub_genre`, `year`, `charter`/`frets`, `icon`, `playlist`, `album_track`, `playlist_track`, `rating`, `tags`, `song_length`, `preview`, `preview_start_time`, `preview_end_time`, `delay`, `video_*`, `background`, `video`, `cover`, `diff_guitar` (e demais `diff_*`), `loading_phrase`, `credit_*`, `link_*`, `vocal_*`.
- Tags que mudam a leitura da guitarra (`IniBase.cs:221-269`): `hopo_frequency` (ticks, só se > 0), `eighthnote_hopo`, `hopofreq` (0-5; **qualquer outro valor rejeita a música**), `sustain_cutoff_threshold` (ticks), `multiplier_note`/`star_power_note` (só `.mid`; só 103 muda algo).
- Capa: `cover` ou `album.{png,jpg,jpeg,...}`. Fundo: `bg.*`/`background.*`/vídeo.

## 4. `.chart` como o YARG.Core lê

- `[Song]` tem que ser a **primeira** seção e `[SyncTrack]` a **segunda**, exatamente com essa caixa; senão a carga falha (`C:MoonscraperChartParser/IO/Chart/ChartReader.cs:111-127, 139`). Nada antes de `[Song]`.
- `[Song]`: chaves com caixa exata `Album Artist Charter Difficulty Genre Name Offset PreviewEnd PreviewStart Resolution Year`. `Resolution` e `Offset` sem aspas (com aspas: resolução 0 → rejeitada; `resolution` minúsculo → lido como 192).
- `[SyncTrack]`: `B n` = BPM×1000; `TS a [e]` = a/2^e (e padrão 2); `A` ignorado. Padrão 120 BPM e 4/4 no tick 0. BPM 0 não é tratado. TS fora do início de compasso gera compasso "interrompido": evitar.
- `[Events]`: `E "section Nome"`, `E "end"`, `E "solo"`/`E "soloend"` (este último nas seções de instrumento).
- Guitarra: `[ExpertSingle] [HardSingle] [MediumSingle] [EasySingle]` (caixa exata). Linhas `tick = TIPO args`, ticks não decrescentes, espaços (não tabs).
- Notas: `N 0..4` = verde, vermelho, amarelo, azul, laranja; `N 7` = aberta; `N 5` = **inverte** HOPO/strum; `N 6` = tap. `S 2 dur` = star power.
- **HOPO natural** (`C:.../MoonNote.cs:277-284`): `!acorde && anterior != null && (anterior.acorde || traste != anterior.traste) && tick - anterior.tick <= limiar`. Estado final = `natural XOR forçado`. Tap vence o forçado. Sem cancelamento "acorde→nota" no `.chart`.
- Limiar padrão no `.chart`: `res//3 + floor(res/192)` → **65 ticks em res 192** (igual ao Moonscraper: 65×res/192). No `.mid`: `res//3 + 1`.
- Sustain no `.chart`: sem corte padrão (`N x 1` = sustain de 1 tick!). Notas sem sustain têm duração **0**.
- Acordes: notas no mesmo tick. Traste repetido no mesmo tick é ignorado mas ainda conta como acorde para o HOPO. Sustain que passa da próxima nota vira `ExtendedSustain`; durações diferentes no acorde viram `Disjoint` (mudam a jogabilidade: evitar).

## 5. `.mid` (resumo)

- Notas por dificuldade: Easy 60-64, Medium 72-76, Hard 84-88, Expert 96-100; forçar HOPO +5 / forçar strum +6 (Expert 101/102) — **marcadores absolutos**. Star power 116, solo 103, tap 104.
- Sustains menores que `res//3` são descartados; tempo só da trilha 0; primeiro evento de cada trilha tratado como nome.

## 6. Formato escolhido para o gerador

- `.mid` dá controle absoluto do tipo de nota; `.chart` só inverte.
- **Decisão do projeto: `.chart` em resolução 192**, sem `hopo_frequency` no ini (limiar padrão de 65 ticks, idêntico no YARG e no Moonscraper). O gerador calcula o estado natural exatamente como acima e emite `N 5` só onde a intenção difere; o validador confere com o parser do próprio YARG.Core. Motivo: é o formato nativo do Moonscraper, então a edição manual fica fiel ao jogo, e um `notes.mid` na mesma pasta teria prioridade sobre o `.chart` editado.

## 7. O que faz o YARG rejeitar ou esconder

- Na varredura (`badsongs.txt`): `NoAudio`, `NoName`, `NoNotes`, `InvalidResolution`, `MultipleMidiTrackNames`, `IniEntryCorruption` (linha inválida antes da primeira nota, `hopofreq` fora de 0-5), `PathTooLong`.
- Na carga: `[Song]`/`[SyncTrack]` fora de ordem → "Failed to load chart!".
- Dificuldade sem notas simplesmente não aparece; o YARG não gera reduções. "Beginner" é derivado do Easy automaticamente.

## 8. Star power

- `.chart`: `S 2 dur`, cobre `tick <= nota < tick + dur` (fim exclusivo) → a duração tem que passar do tick da última nota.
- Acertar todas as notas da frase: +25% da barra; ativar precisa de 50% (2 frases). `C:Engine/Guitar/GuitarEngine.cs:257-266`, `C:Engine/BaseEngine.cs:44`.

## Checklist do gerador

- Pasta `<Artista> - <Título>/` com `song.ini`, `notes.chart`, `song.ogg` (e opcionalmente `guitar.ogg`, `album.png`).
- `song.ini`: UTF-8, `[song]` na primeira linha, `name`, `artist`, `album`, `genre`, `year`, `charter`, `diff_guitar`, `song_length`, `preview_start_time`, `delay = 0`.
- `.chart`: `[Song]` (com `Resolution = 192`, `Offset = 0`) → `[SyncTrack]` (TS e B no tick 0) → `[Events]` → dificuldades. Linhas ordenadas por tick. Sem sustain = duração 0. Acordes com a mesma duração. Star power até 1 tick depois da última nota.
- Validador: nomes, cabeçalhos, ordem das seções, BPM > 0, ticks não decrescentes, sem (tick, traste) duplicado, sem sustain atravessando a próxima nota, HOPO natural calculado = intenção, star power com notas em todas as dificuldades.
