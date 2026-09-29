# Estado da arte para gerar charts automaticamente (2026-09-29)

Pesquisa feita lendo documentação, páginas do PyPI/GitHub e artigos. Nada foi instalado nem executado nessa etapa.
(NV) = não verificado. Referências numeradas no fim.

## Conclusões principais

1. **Beat This!** (CPJKU, ISMIR 2024) está no PyPI como `beat-this` 1.1.0 (14/04/2026). Código **e pesos** MIT. Não precisa do madmom (só na opção `--dbn`). Dá batidas e tempos fortes (downbeats); BPM e compasso eu derivo. [1-7]
2. **librosa 1.0.0 exige Python ≥ 3.12 e numpy ≥ 2.1.** No Python 3.11, fixar `librosa==0.11.0`. [15,16]
3. **O repositório facebookresearch/demucs foi arquivado**; a linha mantida é `adefossez/demucs`, publicada como `demucs` 4.1.0 (11/07/2026), código MIT. **Os pesos "não são cobertos pela licença MIT e são fornecidos só para fins científicos".** [40-44]
4. Demucs em CPU: ~26-29 s por minuto de áudio → ~2 min para uma música de 4 min. [40,48,49]
5. Trabalho mais parecido com o nosso: **STRUM** (maio/2026, MIT) — Demucs 6 stems → onsets por CRNN → pYIN → mapeador de trastes. F1 de onsets da guitarra 0,65 (±100 ms); a escolha de trastes bate com a humana só ~20% (acaso, com 5 trastes). Nenhum projeto aberto faz direito tempo variável, compasso, HOPO, star power e reduções de dificuldade. [35-37]
6. **basic-pitch** (Spotify, Apache-2.0) está parado no Python ≤ 3.11; no Windows puxa TensorFlow < 2.15.1 (numpy < 2). Contorno: backend ONNX com `--no-deps` (NV). [59-62]

## A. Batida, downbeat, tempo e compasso

| Ferramenta | Licença código / pesos | Situação | Windows + py3.11 | Qualidade | Veredito |
|---|---|---|---|---|---|
| **Beat This!** | MIT / MIT | 1.1.0 (04/2026) | `pip install beat-this` (torch, torchaudio, einops, rotary-embedding-torch, soxr) | GTZAN: batida F1 89,1, downbeat 78,3; Ballroom 97,5/95,3; Harmonix 95,8/90,7; SMC 62,7 [4] | **Usar** |
| madmom | BSD / **modelos CC BY-NC-SA** | PyPI de 2018; git sem Windows no CI | quebra no py ≥ 3.10 | GTZAN 79,1/51,4 [13] | Evitar |
| librosa `beat_track`/`plp` | ISC | 0.11.0 | sim | tempo global único, sem downbeat | Só reserva |
| Essentia | **AGPL** | ativo | **sem wheel para Windows** | — | Não |
| BeatNet | CC BY 4.0 | 2023 | exige numba antigo + madmom | GTZAN 80,6/54,1 | Não |
| All-In-One (allin1) | MIT | 2023 | exige NATTEN/madmom | Harmonix 0,958/0,915 + seções | Opcional (rótulos de seção) |

Cuidados com o Beat This!: em música com tempo instável pode disparar em ataques de guitarra (SMC F 0,627; 8% erros de oitava de tempo); ambiguidade de meio/dobro do tempo é conhecida; compassos ímpares e 6/8 sem avaliação publicada. O DBN dele só aceita 3 ou 4 tempos por compasso e 55-215 BPM, então não usar. [5,30]

## B. Onsets (ataques das notas)

- `librosa.onset.onset_strength` com `max_size > 1` = estilo SuperFlux. Referências: SuperFlux F 0,836, RNN 0,873, CNN 0,903 [33]; detector específico de guitarra ~0,88 F1, "no nível do SuperFlux e CNN" [34]. **Padrão: SuperFlux no stem de guitarra**, com o mix como reserva quando o stem estiver quase mudo.
- Teto de avaliação: só 89% dos eventos de charts da comunidade ficam a ±100 ms de um onset real [35] — não avaliar contra charts humanos com tolerância apertada.

## C. Separação de fontes (stem da guitarra)

| Ferramenta | Licença | Velocidade CPU | Qualidade | Veredito |
|---|---|---|---|---|
| **`htdemucs_6s`** (`demucs==4.1.0`) | código MIT / pesos "só fins científicos" | ~2 min por música de 4 min | MoisesDB: guitarra SDR 3,07 dB [50] | **Padrão** |
| htdemucs / htdemucs_ft ("other") | idem | ft 4× mais lento | "other" 7,0 dB em 4 stems | Reserva |
| BS-RoFormer 6 stems (`audio-separator`) | wrapper MIT; **pesos de licença desconhecida** | 20-30 min em CPU (NV) | guitarra 9 dB (autodeclarado) | Só opcional com GPU |
| Spleeter | MIT | — | sem stem de guitarra; numpy < 2 | Não |

Licença dos pesos: tratar os do Demucs como "uso de pesquisa". Para uso pessoal, só internamente, o risco é baixo; **não redistribuir stems separados nas músicas publicadas**.

## D. Transcrição de notas (altura → trastes, duração → sustain)

| Ferramenta | Licença | Situação | Qualidade | Veredito |
|---|---|---|---|---|
| **Basic Pitch 0.4.0** | Apache-2.0 | sem release desde 08/2024; py ≤ 3.11; ONNX se não houver TF | GuitarSet F (sem offset) 0,79 [63]; 19× tempo real em CPU | **Usar** (polifônico, barato) |
| MuScriptor | código MIT; **pesos CC BY-NC, termos proíbem transcrever música sem direitos** | 2026 | 0,808 | Não |
| YourMT3+/MT3/Omnizart | GPL-3.0 / Apache / MIT | pesados ou abandonados | — | Não |
| torchcrepe / PESTO / pYIN | MIT / **LGPL** / ISC | — | só monofônico | Refino opcional |

Achado do STRUM: altura → traste não reproduz a escolha humana (os charters seguem critérios visuais e de ergonomia). **Avaliar o mapeamento de trastes por jogabilidade e direção do contorno melódico, não por "acerto" contra humanos.**

## E. Trabalhos anteriores

- Dance Dance Convolution (2017, MIT), TaikoNation, GenerationMania, osumapper, Mapperatorinator, DeepSaber, InfernoSaber: só ideias.
- **STRUM** (MIT, 2026): melhor referência; treinado em charts da comunidade.
- audio2chart, CloneCharter, Tab Hero: transformers treinados em dezenas de milhares de charts da comunidade; só Expert, tempo fixo, sem HOPO/SP; resultados fracos ou sem avaliação.
- **Dados:** nenhum conjunto de áudio + chart com licença limpa. Todos derivam de charts da comunidade de músicas comerciais — juridicamente nebuloso. **Não treinar com eles.** O YARG rejeita em premiações reduções geradas automaticamente sem curadoria [84].

## F. Editores de chart

| Editor | Licença | Versão | Formatos | Observação |
|---|---|---|---|---|
| **Moonscraper** | BSD-3 (BASS não comercial) | 1.5.13 (15/02/2026) | `.chart` nativo, lê/exporta `.mid` | `MSCE.1.5.13.Installer.Win64.exe` (23,2 MB), SHA-256 no GitHub; recomendado pela wiki do YARG para iniciantes [85-87,90] |
| Editor on Fire (EOF) | BSD-3 | 1.8RC15 | `.mid`, `.chart` | muito ativo, interface pesada |
| ChartForge | licença não informada | 1.5.4 | vários | novo (NV) |

**Recomendação: Moonscraper.**

## G. Regras da comunidade para reduções de 5 trastes (RBN/C3, blog RB Customs, wiki do YARG) [91-95]

| | Easy | Medium | Hard | Expert |
|---|---|---|---|---|
| Trastes | 3 por vez (VVA; ou AAzL por deslocamento de faixa) | 4 por vez (VVAAz; ou VAAzL) | 5 | 5 |
| Acordes | nenhum | só de 2 notas; sem V+Az, V+L, Vm+L | sem 3 notas, sem V+L | todos; acordes de 3 nunca com V e L juntos |
| Densidade | ~mínimas; tirar semínimas | ~semínimas; tirar colcheias | tirar semicolcheias; acima de 160 BPM tirar 1 colcheia a cada 4 | transcrição literal |
| Sustain | folga extra de 1/16; ≥ semínima de intervalo | ≥ 3/16 de intervalo | como Expert | folga ≥ 1/32 (1/16 padrão); ≤ 1/16 = sem cauda |
| HOPO | nenhum forçado | nenhum forçado | acorde→acorde vira nota→acorde | automático, forçar com parcimônia |

(V = verde, Vm = vermelho, A = amarelo, Az = azul, L = laranja)

- Todo traste usado no Expert deve aparecer nas dificuldades menores; ao tirar notas, "re-embrulhar" os trastes preservando o movimento melódico.
- Wiki do YARG: sustain mínimo 200 ms; intervalo 50-150 ms (90 recomendado); chart precisa de mapa de tempo.
- Star power: ~1 frase a cada 40 tempos (~10 compassos em 4/4), cada uma ~1 compasso, espaçadas, nenhuma nos ~8 compassos finais, sem sobreposição [92].

## Pilha recomendada (Python 3.11)

```
torch==2.11.0  torchaudio==2.11.0     # wheels CPU do PyPI; GPU opcional (índice cu128)
beat-this==1.1.0                      # checkpoint final0.ckpt guardado localmente
demucs==4.1.0                         # htdemucs_6s em CPU
librosa==0.11.0  numpy 2.x  soundfile  mido==1.3.3
onnxruntime==1.30.0
basic-pitch==0.4.0 --no-deps  + resampy mir_eval pretty_midi scikit-learn scipy
```
(Combinação ainda não testada junto: travar versões e fazer teste de fumaça.)

## Riscos

- Pesos do Demucs "só fins científicos"; datasets da comunidade juridicamente nebulosos.
- Beat This! pode errar oitava de tempo e produzir batidas não periódicas → suavizar o mapa de tempo e validar ouvindo (clique).
- Stem de guitarra com ~3 dB de SDR → vazamento e onsets falsos.
- basic-pitch sem release desde 2024; rota ONNX com numpy 2 não testada.
- Beat This! baixa o checkpoint da nuvem da JKU na primeira execução → baixar uma vez, conferir hash e guardar.

## Referências

1 github.com/CPJKU/beat_this · 3 pypi.org/project/beat-this · 4 arxiv.org/abs/2407.21658 · 5 beat_this/model/postprocessor.py · 6 beat_this/utils.py · 7 beat_this/pyproject.toml · 13 arxiv.org/abs/2108.03576 · 15 pypi.org/project/librosa · 16 librosa 1.0.0 setup.cfg · 30 arxiv.org/abs/2605.12287 · 33 ofai.at/~jan.schlueter/pubs/2014_icassp.pdf · 34 arxiv.org/abs/2408.13734 · 35 arxiv.org/abs/2605.12135 (STRUM) · 36 huggingface.co/opria123/strum · 37 github.com/opria123/strum · 40 github.com/adefossez/demucs · 42 pypi.org/project/demucs · 43 github.com/facebookresearch/demucs · 44 github.com/facebookresearch/demucs/issues/327 · 48 linuxlinks.com (benchmark Demucs) · 49 mixxx.org/news/2025-10-27-gsoc2025-demucs-to-onnx-dhunstack · 50 arxiv.org/abs/2307.15913 · 59 github.com/spotify/basic-pitch · 60 pypi.org/project/basic-pitch · 62 basic_pitch/__init__.py · 63 arxiv.org/abs/2203.09893 · 84 wiki.yarg.in/wiki/Chart_awards · 85 github.com/FireFox2000000/Moonscraper-Chart-Editor · 86 …/releases/tag/1.5.13 · 87 moonscrapercharteditor.com · 90 wiki.yarg.in/wiki/Help:Charting · 91 docs.c3universe.com/rbndocs (Guitar and Bass Authoring) · 92 docs.c3universe.com/rbndocs (Overdrive and Big Rock Endings) · 93 rockbandcustomsblog.wordpress.com (reduções Easy/Medium/Hard) · 94 wiki.yarg.in/wiki/5-Fret_Guitar_Lower_Difficulty_Range_Shifts · 95 wiki.yarg.in/wiki/YARN_submission_guidelines
