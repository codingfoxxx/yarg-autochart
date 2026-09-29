# yarg-autochart

Ferramentas e documentação do meu fork pessoal do [YARG](https://github.com/YARC-Official/YARG) (Yet Another Rhythm Game), um jogo de ritmo livre no estilo "guitarra de plástico", aqui ajustado para jogar com **controle de Xbox** no PC.

> Projeto pessoal, **não oficial** e sem afiliação com a YARC. O jogo em si fica no fork [`codingfoxxx/YARG`](https://github.com/codingfoxxx/YARG) (branch `pessoal`).

## O que tem aqui

| Pasta | Conteúdo | Estado |
|---|---|---|
| `autochart/` | Gerador de charts: recebe um áudio (mp3/ogg/wav/flac) e cria uma pasta de música pronta para o YARG, com as 4 dificuldades, relatório de qualidade e validação no código do jogo ([README](autochart/README.md)) | funcionando |
| `samples/` | 3 músicas Creative Commons com charts gerados e relatórios (áudio no Release) | pronto |
| `tools/validator/` | Validador em .NET que usa o próprio YARG.Core para carregar e "jogar" o chart gerado | funcionando |
| `tools/unity-compile-check/` | Confere se o código do fork compila sem o editor do Unity (útil com o Smart App Control) | funcionando |
| `tests/` | Testes da engine de 5 trastes com inputs temporizados, da histerese dos gatilhos e da calibração do fork (.NET), e da ferramenta (Python) | 43 + 26 testes |
| `scripts/` | Arrastar um áudio para gerar a música, preparar o ambiente, validar, testes em contêiner, build do jogo | funcionando |
| `docs/` | Pesquisa da Fase 0 e auditoria de timing da engine | pronto |
| `YARG/` | O fork do jogo, como submódulo git ([mudanças](https://github.com/codingfoxxx/YARG/blob/pessoal/CHANGELOG-FORK.md)) | código pronto, build pendente |

Documentos do projeto: [PLAYTEST.md](PLAYTEST.md) (roteiro de teste com o controle), [DECISION.md](DECISION.md) (decisões e justificativas), [PROGRESS.md](PROGRESS.md) (diário), [SECURITY_LOG.md](SECURITY_LOG.md) (tudo que foi baixado e verificado) e [LICENSES.md](LICENSES.md) (licenças).

## Músicas

Nenhuma música comercial é distribuída aqui. As músicas de teste têm licença livre (Creative Commons), com fonte e créditos registrados; o áudio vai nos Releases, não no git. A ferramenta serve para você gerar charts das músicas que **você possui legalmente**.

## Licença

O código deste repositório é MIT (ver [LICENSE](LICENSE)). O YARG e o YARG.Core são LGPL-3.0 e têm componentes com restrições próprias (por exemplo, a biblioteca de áudio BASS é gratuita só para uso não comercial); detalhes em LICENSES.md.
