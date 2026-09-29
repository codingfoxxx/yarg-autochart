# autochart — charts de guitarra a partir de qualquer áudio

Gera uma **pasta de música pronta para o YARG** (`song.ini`, `notes.chart`, `song.ogg` e, por padrão, `guitar.ogg`) a partir de um arquivo de áudio (mp3, ogg, wav, flac, m4a…), com as **4 dificuldades** (Easy, Medium, Hard, Expert), mapa de tempo, acordes, sustains, HOPOs, star power e seções para o modo prática. Cada música sai com um **relatório de qualidade** e é **validada com o próprio código do jogo** (YARG.Core).

> Use com músicas que você possui legalmente. O chart gerado é um ponto de partida: dá para jogar direto e corrigir o que quiser no Moonscraper.

## Jeito mais fácil

1. Uma vez só: `scripts\preparar-ambiente.ps1` (cria o `.venv` com os pacotes verificados e baixa os modelos conferindo o hash).
2. **Arraste o arquivo de áudio em cima de `scripts\gerar-musica.bat`**, informe nome e artista.
3. A música aparece em `C:\Dev\GuitarHero\songs\Artista - Música\`. No YARG, adicione essa pasta `songs` uma vez em *Configurações → Músicas*. O jogo só enxerga músicas novas depois de uma varredura completa: no fork, ligue **Escanear Tudo ao Iniciar** na mesma aba (ela acontece a cada abertura), ou, na biblioteca, aperte **Laranja (LB no controle) → Escanear Músicas**.

## Linha de comando

```
.venv\Scripts\python.exe -m autochart gerar "arquivo.mp3" --titulo "Nome" --artista "Artista" [opções]
```

| Opção | Padrão | O que faz |
|---|---|---|
| `--saida PASTA` | `songs\` (ou `AUTOCHART_SAIDA`) | onde criar a pasta da música |
| `--fonte guitarra\|outros\|baixo\|mix` | `guitarra` | de onde tirar as notas: stem de guitarra separado, stem "outros", baixo ou o mix inteiro |
| `--densidade 0.5–1.5` | `1.0` | menor = menos notas no Expert (as outras dificuldades seguem) |
| `--sensibilidade 0–1` | `0.5` | maior = detecta ataques mais fracos |
| `--sem-stems` | — | grava só `song.ogg` (sem a guitarra separada; o jogo não abafa a guitarra quando você erra) |
| `--dificuldades` | todas | ex.: `Expert,Hard` |
| `--dispositivo cuda` | `cpu` | usa a GPU NVIDIA (opcional) |
| `--sem-validacao` | — | pula a validação no YARG.Core |
| `--album --ano --genero` | vazio | metadados do `song.ini` |

Tempo típico numa CPU Ryzen 7 7700: **~50 s para uma música de 3 min** (a separação de stems é a maior parte; repetir a mesma música usa o cache e leva ~15 s).

## Como funciona

1. **Batidas** — Beat This! (ISMIR 2024) no mix completo, com picos em precisão sub-quadro; fase do grid alinhada aos ataques de bateria; correção de batidas espúrias/perdidas e de trechos em meio tempo.
2. **Mapa de tempo** — um BPM único quando a música foi gravada com metrônomo; trechos de BPM constante quando há deriva real (música ao vivo). Fórmula de compasso (4/4, 3/4…) e anacruse detectadas.
3. **Stem da guitarra** — Demucs `htdemucs_6s`.
4. **Ataques** — fluxo espectral (estilo SuperFlux) no stem, refinado no envelope de amplitude.
5. **Alturas** — Basic Pitch (Spotify) via ONNX: altura, polifonia (nota × acorde de 2 ou 3) e duração. Notas só transcritas entram se forem ligados (hammer-on/pull-off) ou ataques perdidos, e são descartadas se estiverem mais fortes em outro instrumento (vazamento).
6. **Quantização** — o "vocabulário rítmico" da música (se usa semicolcheias, tercinas…) é inferido do próprio áudio; a imprecisão humana não vira subdivisão complexa.
7. **Trastes** — programação dinâmica sobre o contorno melódico (subiu a altura → traste à direita), com ergonomia e riffs repetidos com o mesmo desenho.
8. **Dificuldades** — Expert ⊇ Hard ⊇ Medium ⊇ Easy, guardando as notas de maior peso métrico; 5/5/4/3 trastes; acordes, sustains e HOPOs pelas regras da comunidade (Rock Band Network / C3).
9. **Star power** — ~1 frase a cada 40 tempos, em trechos marcantes, igual em todas as dificuldades. **Seções** por segmentação estrutural.
10. **Saída e validação** — `.chart` (resolução 192) com o HOPO natural calculado pela mesma regra do YARG; o validador roda o scanner, o parser e a engine do YARG.Core e confere nota a nota o tipo (palhetada/HOPO/tap).

Detalhes e justificativas: [DECISION.md](../DECISION.md) e [docs/pesquisa/](../docs/pesquisa/).

## O relatório (`relatorio.md` e `autochart.json`)

| Métrica | O que significa |
|---|---|
| Encaixe do grid | distância entre as batidas detectadas e as linhas de batida do chart (mediana/p95) |
| Nota → evento | distância entre cada nota e o ataque que a originou (erro de grid + quantização; inclui a imprecisão humana) |
| Ataques fortes cobertos | % dos ataques fortes do áudio que viraram nota |
| Notas só da transcrição | % de notas sem ataque detectado (ligados/ataques suaves) |
| NPS | notas por segundo (média e pico em 2 s) por dificuldade |
| Consistência de riffs | % de riffs repetidos que já saíram com o mesmo desenho (depois disso, todos são igualados) |
| Violações | regras de jogabilidade quebradas (trastes/acordes proibidos, notas próximas demais, sustain atravessando nota, HOPO no mesmo traste, HOPO no Easy/Medium, frase de star power vazia) — **tem que ser 0** |
| Validação no YARG.Core | a música foi encontrada pelo scanner do jogo? os tipos de nota conferem? quanto acerta um jogador perfeito e jogadores "humanos" com erro de ±20/35 ms? |

## Corrigir à mão no Moonscraper

1. Instale o **Moonscraper Chart Editor 1.5.13** (instalador oficial conferido em `_downloads\MSCE.1.5.13.Installer.Win64.exe`; SHA-256 `30c5d007…fefe`, ver SECURITY_LOG.md).
2. *File → Open* no `notes.chart` da música. O áudio carrega sozinho (`MusicStream`/`GuitarStream` no `[Song]`).
3. Edite e salve (*File → Save*, formato `.chart`). O HOPO que o Moonscraper mostra é o mesmo que o YARG vai mostrar (mesma regra e mesmo limiar de 65 ticks).
4. No YARG, escaneie as músicas de novo (**Laranja/LB → Escanear Músicas** na biblioteca). Rode `scripts\validar-musica.ps1 "pasta da música"` para conferir o chart editado no YARG.Core.

Não gere de novo por cima de uma pasta editada (o gerador sobrescreve o `notes.chart`).

## Limitações conhecidas

- **Metal/mix muito denso**: a separação da guitarra piora e os ataques ficam "borrados"; o chart fica mais aproximado.
- **Imprecisão humana**: notas vão para o grid musical; guitarristas soltos ficam a ~15–25 ms do ataque real (dentro da janela de ±70 ms do jogo).
- **Fórmula de compasso única** na música inteira (mudanças raras ficam para a edição manual). Sem notas abertas nem taps gerados.
- A escolha de trastes segue o contorno melódico, não a posição real no braço; charters humanos também usam critérios visuais que a ferramenta não reproduz.
- Seções com nomes genéricos ("Parte A", "Parte B"…).

## Licenças e segurança

- Código: MIT. Dependências e modelos: ver [LICENSES.md](../LICENSES.md). **Os pesos do Demucs são fornecidos "só para fins científicos"**: a ferramenta os usa localmente; stems separados não são publicados.
- Pacotes Python instalados só a partir de arquivos com hash (`requirements-win.lock`), gerados num contêiner isolado (`sandbox/`). Pesos carregados só de arquivos locais com hash conferido; sem downloads nem telemetria em tempo de execução.
- **Smart App Control (Windows 11)**: o PyTorch fica fixado em 2.8.0 porque as DLLs de versões mais novas, sem reputação, são bloqueadas. Não é preciso (nem recomendado) desligar essa proteção.

## Testes

```
.venv\Scripts\python.exe -m unittest discover -s autochart\tests
scripts\validar-musica.ps1 "C:\Dev\GuitarHero\songs\Artista - Música"
```
