# DECISION.md — decisões de arquitetura

Escrito ao fim da Fase 0 (2026-09-29), antes de qualquer mudança no código do YARG.
As pesquisas que embasam cada decisão estão em [`docs/pesquisa/`](docs/pesquisa/).

## Resumo

| Tema | Decisão |
|---|---|
| Base do fork | Upstream `YARC-Official/YARG`, branch `dev` @ `275e9a13` (26/09/2026); submódulo YARG.Core @ `e2d44e8d` |
| Branch de trabalho | `pessoal` no fork `codingfoxxx/YARG` (padrão do fork no GitHub); `master` e `dev` ficam como espelhos do upstream |
| Atualizar do upstream | `git fetch upstream` + `git merge upstream/dev` na `pessoal` (merge, nunca rebase do que já foi publicado) |
| Repositórios | Dois públicos: o fork `codingfoxxx/YARG` (só o jogo) e `codingfoxxx/yarg-autochart` (ferramentas + documentação) |
| Mudanças no YARG | Mínimas, isoladas, cada uma com commit próprio e justificativa no `CHANGELOG-FORK.md`; mudança de gameplay sempre configurável |
| Formato gerado | `notes.chart`, resolução 192, com `song.ini` e `song.ogg` (+ `guitar.ogg` opcional) |
| Batida/tempo | Beat This! (`beat-this` 1.1.0, MIT, pesos MIT) |
| Stem da guitarra | Demucs `htdemucs_6s` (`demucs` 4.1.0), em CPU por padrão |
| Onsets | Fluxo espectral estilo SuperFlux (`librosa` 0.11.0) no stem da guitarra |
| Altura das notas | Basic Pitch 0.4.0 via ONNX (Apache-2.0) |
| Trastes, dificuldades, HOPO, sustain, star power | Regras determinísticas escritas por nós (sem treinar modelo) |
| Validação | Validador .NET que usa o próprio YARG.Core para varrer, carregar e "jogar" o chart com bot |
| Editor manual | Moonscraper Chart Editor 1.5.13 |
| Integração no jogo | Não na v1: CLI + script de "arrastar o áudio e gerar" |

---

## 1. Estratégia de fork

### Base: `dev`, não o release v0.15.0

O release estável mais novo é o v0.15.0 (24/06/2026). Desde então o `dev` recebeu 265 commits, vários exatamente no que importa para este projeto:

- #1558 "Improved song sync, mic latency, various audio improvements" (sincronizador novo);
- #1589 "Fix audio desync issues";
- "Fix settings calibration issues";
- #1535 offset de áudio por música;
- #1653 biblioteca nativa de áudio (buffer de leitura antecipada);
- "Fix inputs not working when playing new song", "Block input during loading…".

Basear no v0.15.0 significaria auditar um código de sincronia que já foi substituído. O `dev` é o que o próprio YARG publica como build "bleeding edge". O risco (instabilidade de branch em desenvolvimento) é mitigado fixando o commit `275e9a13` e testando; quando sair o v0.16, fazemos merge.

### Fluxo de branches e remotes

- `origin` = `https://github.com/codingfoxxx/YARG` (fork real, criado pela API de fork do GitHub, com todas as branches).
- `upstream` = `https://github.com/YARC-Official/YARG`.
- `pessoal` nasce de `275e9a13`. É a branch padrão do fork no GitHub, para quem abrir o repositório ver o aviso de fork.
- Tags do fork: `pessoal-v0.1.0`, `pessoal-v0.2.0`… (sem colidir com as tags `vX.Y.Z` do upstream).
- Submódulo YARG.Core: continua apontando para o oficial enquanto não mexermos no core. Na primeira mudança necessária no core, criamos o fork `codingfoxxx/YARG.Core` (branch `pessoal`) e trocamos a URL do submódulo **só** na branch `pessoal`.
- GitHub Actions herdadas do upstream (crowdin, labels…) ficam desligadas no fork: não são nossas e usariam segredos que não temos.

### Regras para mudar o código do YARG

1. **Mínimo e isolado.** Preferir arquivos novos (classes novas) a editar arquivos existentes. Onde for inevitável editar, diff pequeno e comentário `// [pessoal]` no ponto de edição, para achar tudo em futuros merges (`git grep "\[pessoal\]"`).
2. **Um commit por mudança**, com mensagem descritiva e entrada no `CHANGELOG-FORK.md` explicando o quê e por quê.
3. **Gameplay nunca imposto.** Toda mudança que altere comportamento de jogo vem com configuração; o padrão é o comportamento do upstream, exceto quando for correção de bug comprovada (com teste).
4. **Arquivos Unity (cenas, prefabs) só quando não houver alternativa por código**: são YAML enormes, difíceis de revisar e de fazer merge.
5. **Sem marcas de IA** em commits, PRs e arquivos (regra do Lucas).
6. Mudanças que forem correção de bug genérica ficam em commits limpos, prontos para virar pull request no upstream, se o Lucas quiser.

### Identificação do fork

- Faixa curta no topo do `README.md` do fork dizendo que é um fork pessoal, não oficial, com link para o original.
- `FORK.md` (o que é, diferenças, licenças), `CHANGELOG-FORK.md`, `BUILD.md` na raiz do fork.
- Todos os avisos de copyright e o `LICENSE` (LGPL-3.0) do upstream ficam intactos.
- Nomes públicos evitam as marcas "Guitar Hero" e "Rock Band" (Activision/Harmonix). A pasta local continua se chamando `GuitarHero` porque é só um nome de pasta no PC do Lucas.

## 2. Dois repositórios, e por quê

| Repositório | Conteúdo | Licença |
|---|---|---|
| `codingfoxxx/YARG` (fork) | Código do jogo + as mudanças do fork + `BUILD.md`, `FORK.md`, `CHANGELOG-FORK.md` | LGPL-3.0 (herdada) |
| `codingfoxxx/yarg-autochart` (novo) | Ferramenta de auto-charting (Python), validador e testes de engine (.NET), scripts, documentação do projeto (este arquivo, PROGRESS, LICENSES, SECURITY_LOG, PLAYTEST, relatório final), charts das músicas de teste | MIT para o nosso código; dependências mantêm as suas (ver LICENSES.md) |

Por que não tudo no fork:

- **Atualização do upstream fica trivial.** O fork só difere do original onde realmente mexemos no jogo; nada de pastas Python ou .NET extras aparecendo em cada merge.
- **Licenças e distribuição separadas.** O jogo é LGPL e tem componentes com restrição não comercial (BASS, dois sons CC BY-NC); a ferramenta é código novo, pode ser MIT, e não precisa carregar essas restrições.
- **Ciclos diferentes.** A ferramenta evolui (e é testada) sem precisar recompilar o Unity; o build do jogo não depende de Python.
- **Clareza para quem visita:** um repositório é "o jogo", o outro é "as ferramentas e a documentação".

Ligação entre os dois: o repositório de ferramentas inclui o fork como **submódulo git em `./YARG`**. Assim, o validador e os testes compilam contra exatamente o mesmo YARG.Core do jogo, e cada commit das ferramentas registra com qual versão do fork foi validado.

### Estrutura local (`C:\Dev\GuitarHero`, fora do OneDrive por escolha do Lucas)

```
C:\Dev\GuitarHero\            ← repositório yarg-autochart
  README.md, DECISION.md, PROGRESS.md, LICENSES.md, SECURITY_LOG.md, PLAYTEST.md, BUILD-FERRAMENTAS.md
  autochart\                  ← pacote Python (CLI)
  tools\validator\            ← validador .NET (usa o YARG.Core do fork)
  tests\                      ← testes da engine (NUnit) e da ferramenta (pytest)
  scripts\                    ← "arraste o áudio aqui", setup, build
  docs\pesquisa\              ← relatórios da Fase 0
  YARG\                       ← submódulo: o fork (com o submódulo YARG.Core dentro)
  songs\                      ← saídas geradas (fora do git)
  _tools\ _downloads\ _builds\ _work\   ← ferramentas portáteis, instaladores, builds, rascunhos (fora do git)
```

## 3. O que pretendo mudar no YARG (a confirmar pela auditoria)

A lista abaixo é o plano. Cada item só entra se a auditoria confirmar o problema ou o ganho; cada um vira entrada no `CHANGELOG-FORK.md`.

**A1. Controle de Xbox**
- O preset atual do YARG para gamepad é ergonômico e fica como padrão: verde = LT, vermelho = LB, amarelo = RB, azul = RT, laranja = A, palhetada no D-pad cima/baixo, star power no View, whammy no analógico esquerdo X.
- **Histerese para botões analógicos** (gatilhos): hoje `pressionado = valor ≥ 0,5`, sem histerese. Um gatilho parado perto do meio pode gerar pressões/solturas fantasmas, e com anti-ghosting isso bloqueia HOPOs. Plano: ponto de soltura configurável por controle (padrão = ponto de pressão, ou seja, comportamento atual), e o preset de gamepad passa a usar pressão mais curta e soltura com margem nos gatilhos.
- **Deadzone no whammy do preset de gamepad**: hoje qualquer ruído do analógico reinicia o timer de whammy (ganho de star power indevido).
- A avaliar: preset alternativo "botões frontais" (A/B/X/Y + LB) e deixar o gamepad entrar no perfil com menos passos.

**A2. Calibração guiada para quem joga com controle**
- O calibrador atual só mede áudio, quase não tem texto e grava num ajuste global.
- Plano: tela com instruções claras (pt-BR e inglês), contador de progresso, resultado explicado, repetir, e escolha de onde salvar: no perfil (a calibração de input por perfil já existe no YARG, só não tem ferramenta) ou global. Etapa de vídeo se o custo for razoável.

**A3. Correções da auditoria de timing** (cada uma com teste automatizado)
- Já confirmado e trivial: `Keyboard.current` sem checagem de nulo em `GameManager.Update`.
- Suspeitas em investigação (ver `docs/pesquisa/mapa-input-engine.md`): pontuação de sustain no overstrum, cópia de preset que perde um campo, timer com offset não escalado, calibração de input não escalada pela velocidade. **A latência de áudio contada duas vezes não será alterada sem medição real**: a calibração a neutraliza, e mudar às cegas pode piorar.

**A4. Qualidade de vida**: mensagens de erro mais claras onde a auditoria mostrar confusão (ex.: música nova que não aparece sem "Refresh All Caches").

**A5. Infra de build**: build por linha de comando com o mecanismo padrão do Unity (`-buildWindows64Player`), sem código novo no jogo se possível.

**Fica fora do código do YARG**: auto-charting, validador, testes de engine (no repositório de ferramentas, compilando contra o YARG.Core do fork; um teste só vai para o fork do YARG.Core junto com uma correção do core), medição de desempenho (PresentMon, externo), documentação do projeto.

## 4. Formato do chart gerado: `.chart`

- **Moonscraper edita `.chart` nativamente**, então a correção manual é fiel ao jogo. Um `notes.mid` na mesma pasta teria prioridade sobre o `notes.chart` (ordem de leitura do YARG), e editar um e esquecer o outro é uma armadilha.
- O YARG.Core lê `.chart` com um parser derivado do Moonscraper: mesma semântica nos dois.
- A desvantagem do `.chart` (`N 5` inverte o HOPO/strum natural em vez de fixá-lo) é resolvida calculando o estado natural com a mesma fórmula do YARG: resolução 192, limiar padrão 65 ticks (idêntico no Moonscraper), sem `hopo_frequency` no ini. O validador confirma nota a nota com o parser do YARG.
- Texto simples: fácil de depurar, comparar e versionar.

## 5. Auto-charting

### Por que regras determinísticas e não um modelo treinado

- Não existe conjunto de dados "áudio + chart" com licença limpa; todos os disponíveis derivam de charts de músicas comerciais. Treinar com eles contraria a regra do projeto de não usar material de licença duvidosa.
- Os modelos publicados (audio2chart, CloneCharter, Tab Hero) só fazem Expert, com tempo fixo e sem HOPO/star power, e têm avaliação fraca.
- Regras explícitas são auditáveis, reproduzíveis (mesma entrada → mesmo chart) e ajustáveis por parâmetros (densidade, sensibilidade).

### Pilha escolhida (Python 3.11, versões fixadas com hash)

| Etapa | Escolha | Alternativas descartadas |
|---|---|---|
| Decodificação | `ffmpeg` (já instalado) → PCM 44,1 kHz; o mesmo PCM gera o `song.ogg` e a análise (alinhamento garantido) | — |
| Batidas e downbeats | **Beat This!** 1.1.0: estado da arte (GTZAN 89,1/78,3), MIT inclusive pesos, sem madmom | madmom (quebra no py ≥ 3.10, modelos NC), essentia (AGPL, sem Windows), BeatNet (dependências velhas), librosa (tempo único, sem downbeat) |
| Stem da guitarra | **Demucs `htdemucs_6s`** (tem stem "guitar"), CPU ~2 min/música | Spleeter (sem guitarra), RoFormers (pesos sem licença clara, lentos em CPU) |
| Onsets | **librosa** 0.11.0, fluxo espectral estilo SuperFlux no stem | madmom CNN (licença NC, instalação) |
| Altura (para escolher trastes) | **Basic Pitch** 0.4.0 via ONNX (Apache-2.0, 19× tempo real) | MuScriptor (pesos NC e termos restritivos), MT3 (pesado) |
| MIDI/chart | escritor próprio de `.chart` (formato documentado em domínio público) | — |

Opções da CLI: fonte do chart (`--fonte mix|guitarra|other|baixo`), densidade, sensibilidade de onsets, metadados, dificuldades, semente, e `--stems` para gerar `guitar.ogg` (guitarra separada; o jogo abafa a guitarra quando você erra).

### Pipeline

1. **Áudio:** decodifica uma vez; opcionalmente adiciona silêncio inicial para dar tempo de leitura antes da primeira nota (ajustando todos os tempos).
2. **Mapa de tempo:** batidas e downbeats do Beat This! no mix completo → segmentos de tempo constante por partes (troca de BPM só quando o desvio passa de alguns ms), para o grid bater nas batidas reais sem criar um BPM por batida. Compasso pelo número de batidas entre downbeats; compasso inicial incompleto (anacruse) com evento `TS` próprio. Correção de oitava (meio/dobro do tempo) por faixa de BPM plausível e densidade de onsets.
3. **Eventos de nota:** onsets no stem (ou no mix) + notas do Basic Pitch; cada onset recebe altura (contorno) e polifonia (nota simples, acorde de 2 ou de 3).
4. **Quantização:** cada onset vai para a subdivisão mais simples que explique bem o tempo (1/4, 1/8, 1/16, tercinas), com detecção de "swing" por compasso; o erro de quantização vira métrica.
5. **Expert:** densidade limitada (intervalo mínimo e teto de notas por segundo), mapeamento de trastes pelo **contorno relativo de altura** numa janela deslizante (sobe a altura → traste à direita), notas repetidas no mesmo traste, **riffs repetidos recebem o mesmo desenho de trastes** (detecção de compassos semelhantes), restrições de jogabilidade (saltos grandes em notas rápidas proibidos, acordes só em formas tocáveis).
6. **Reduções Hard/Medium/Easy** pelas regras da comunidade (tabela em `docs/pesquisa/estado-da-arte-autochart.md` §G): mantém notas de maior peso métrico (tempo forte > batida > colcheia > semicolcheia), reduz trastes disponíveis (5/5/4/3), simplifica acordes, "re-embrulha" trastes preservando o movimento melódico. Toda nota de dificuldade menor coincide no tempo com uma nota do Expert.
7. **Sustains:** pela energia do stem após o ataque e pela duração da nota transcrita; mínimo ~200 ms; terminam antes da próxima nota com folga de 1/16 (Expert) até 1/4 (Easy); acordes com durações iguais.
8. **HOPO:** Easy/Medium só strum; Hard/Expert seguem a regra natural, e forçamos strum onde o áudio indica palhetada (ataque forte) e HOPO onde indica ligado (mudança de altura sem ataque); o `N 5` é calculado a partir da fórmula exata do YARG.
9. **Star power:** ~1 frase a cada 40 tempos, ~1 compasso cada, em trechos marcantes (início de refrão, sustains), nenhuma nos últimos ~8 compassos, as mesmas janelas em todas as dificuldades e com notas em todas.
10. **Seções** (`section …`) por segmentação estrutural simples, para o modo de prática.
11. **Saída:** pasta `Artista - Título/` com `song.ini`, `notes.chart`, `song.ogg` (+ `guitar.ogg`), `autochart.json` (parâmetros, versões e hashes, para reprodutibilidade) e `relatorio.md`.

### Métricas de qualidade (relatório por música)

- **Grid:** desvio mediano das batidas detectadas em relação às linhas de batida do chart (ms), quantidade de mudanças de BPM.
- **Alinhamento:** distância de cada nota ao onset mais próximo (mediana, p95); % de notas a ≤ 25/50 ms de um onset; % dos onsets fortes cobertos por nota.
- **Densidade:** notas por segundo (média e pico em janelas de 2 s) por dificuldade; % de acordes, sustains e HOPOs.
- **Jogabilidade (tem que dar zero violações):** intervalo mínimo por dificuldade, trastes/acordes proibidos por dificuldade, HOPO no mesmo traste, sustain atravessando nota, frase de star power sem nota em alguma dificuldade.
- **Coerência:** % de riffs repetidos que receberam o mesmo desenho; monotonicidade Easy < Medium < Hard < Expert.
- **Engine real:** o validador carrega o chart com o YARG.Core, roda a engine de 5 trastes com um bot perfeito (tem que dar 100% e combo total) e com um bot "humano" (atraso aleatório de ±20-35 ms), que estima a dificuldade.

### Integração com o jogo

Não na primeira versão. Um botão no YARG exigiria UI nova, chamar Python a partir do Unity e lidar com instalação; seria a maior mudança no código do YARG, contrariando o princípio de mudanças mínimas. Em vez disso: CLI documentada + `scripts\gerar-musica.bat` (arraste o áudio em cima) que gera a pasta já dentro da biblioteca configurada, com o lembrete de apertar "Refresh All Caches".

## 6. Edição manual: Moonscraper

Moonscraper Chart Editor 1.5.13 (BSD-3, jan/2026): edita `.chart` nativamente, é o editor recomendado pela wiki do YARG para iniciantes e publica SHA-256 dos instaladores. EOF fica como segunda opção. Não faremos editor próprio: não há ganho claro sobre o Moonscraper.

## 7. Segurança e isolamento

- Só fontes oficiais (sites dos projetos, GitHub oficial, PyPI, CDN da Unity/Microsoft/Blender), com SHA-256 conferido contra o valor publicado, assinatura digital verificada quando existe e varredura do Windows Defender antes de executar. Tudo registrado em `SECURITY_LOG.md`.
- Instalações portáteis em `_tools\` (sem administrador, sem janelas de UAC), exceto o Unity Hub (MSIX por usuário).
- Pacotes Python com versões fixadas e **hashes** (`pip install --require-hashes`), só wheels quando possível (sem executar `setup.py` de terceiros). Nomes conferidos contra typosquatting.
- **Isolamento:** a primeira instalação da pilha de ML e o primeiro download de pesos de modelo (arquivos que o PyTorch carrega) rodam num contêiner Docker descartável; os hashes dos pesos obtidos lá são fixados, e a instalação local só aceita arquivos com esses hashes. Pesos carregados com `weights_only=True` onde a biblioteca permitir.
- Nenhum segredo em arquivo versionado. O `gh` guarda o token no Gerenciador de Credenciais do Windows.

## 8. Músicas de teste

Candidatas em [`docs/pesquisa/musicas-livres.md`](docs/pesquisa/musicas-livres.md) (todas CC BY ou CC0). Preferência por variedade: 4/4 médio (The Vagabond, 128 BPM), rápido (Gallows Hill, 175), 3/4 (Burn The World Waltz, 177), com reservas instrumentais de download direto (surf rock do ccMixter). O áudio **não** entra no git: vai no GitHub Releases com os créditos exigidos; o repositório guarda charts, `song.ini` e relatórios. **Stems separados pelo Demucs não serão publicados** (pesos "só para fins científicos").

## 9. Riscos conhecidos e plano B

| Risco | Plano B |
|---|---|
| `dev` do upstream instável | Pinar commit; se quebrar, recuar para o commit bom mais próximo do `dev` ou para v0.15.0 |
| Disco (só ~16 GB livres) | Instalações mínimas (Unity sem módulos extras, torch CPU), limpeza de instaladores após uso; vigia noturno suspende o PC abaixo de 3 GB |
| Licença do Unity no Hub MSIX fica numa pasta virtualizada | Rodar o Editor com o Hub aberto (cliente de licença via IPC) ou dentro do contexto do pacote |
| Beat This! erra oitava de tempo / tempo instável | Correção por faixa plausível + densidade; opção `--bpm` manual; relatório destaca baixa confiança |
| basic-pitch não instala com numpy 2 | Ambiente separado ou altura por CQT/cromagrama (librosa) |
| GPU instável | Tudo em CPU por padrão |
| Não consigo apertar botões nem sentir o timing | Testes automatizados de engine com inputs temporizados, replays determinísticos, validação com o YARG.Core e roteiro de playtest para o Lucas |
