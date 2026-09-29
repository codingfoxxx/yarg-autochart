# PLAYTEST: roteiro de teste com o controle de Xbox

Roteiro para o Lucas testar o jogo e o autochart, com o que observar e como relatar. Tempo total: ~1 h.

> **Estado em 29/09, 03:30:** o jogo ainda **não foi compilado**. Faltam o Unity 6000.3.5f2 e a decisão sobre o Smart App Control (ver `PROGRESS.md`). As partes **[depois do build]** dependem disso. A parte do autochart (seção 5) já pode ser testada.
> Os caminhos de menu abaixo foram tirados do código do jogo, não de telas vistas rodando. Os nomes podem variar um pouco.

## 0. Antes de começar

- Controle de Xbox **com fio** no primeiro teste (Bluetooth adiciona atraso; dá para comparar depois).
- Use o mesmo fone ou caixa de som de sempre. Monitor em modo jogo, se tiver.
- Músicas de teste: baixe o zip do Release [musicas-teste-v1](https://github.com/codingfoxxx/yarg-autochart/releases/tag/musicas-teste-v1) e extraia as 3 pastas em `C:\Dev\GuitarHero\songs\`. Ou gere as suas (seção 5).

## 1. Primeira abertura [depois do build]

1. Abra o jogo. **Esperado:** menu principal em até ~30 s (a primeira varredura de músicas pode demorar).
2. **Configurações → Músicas** (*Settings → Songs*): adicione a pasta `C:\Dev\GuitarHero\songs` e use **Atualizar todos os caches** (*Refresh All Caches*). **Esperado:** as 3 músicas aparecem em **Jogar**.
3. **Perfis → Adicionar Perfil** (*Profiles → Add Profile*): crie um perfil de **Guitarra (5 botões)**. Ative o perfil, adicione um dispositivo e escolha o controle de Xbox. Na pergunta *"Which kind of controller is this?"*, escolha **Gamepad**. O mapeamento padrão é aplicado sozinho.
   - O jogo **não** cria perfil automático para controle comum, só para guitarras e baterias de verdade. Esse passo é sempre manual.

Anote: alguma mensagem de erro? Algo confuso nesse caminho?

## 2. Mapeamento do controle [depois do build]

Padrão do preset **Gamepad** (5 trastes):

| Traste / ação | Botão | Dedo sugerido |
|---|---|---|
| Verde | **LT** (gatilho esquerdo) | médio esquerdo |
| Vermelho | **LB** | indicador esquerdo |
| Amarelo | **RB** | indicador direito |
| Azul | **RT** (gatilho direito) | médio direito |
| Laranja | **A** | polegar direito |
| Palhetada | **direcional ↑ / ↓** | polegar esquerdo |
| Star power | **View** (botão de janelas) | — |
| Whammy | analógico esquerdo, eixo X | polegar esquerdo |

Na tela de edição de binds do perfil (*Edit Binds*):

1. Aperte cada botão: **esperado:** o indicador do traste certo acende. Nenhum botão acende duas ações.
2. **Teste da histerese (mudança do fork):** aperte **LT devagar**. Ele acende perto da **metade do curso**. Agora solte devagar: **deve continuar aceso até ~1/3 do curso** e só apagar depois disso. No YARG original, ele apaga assim que passa da metade.
   - Se os gatilhos parecerem lentos para acionar, dá para baixar o ponto de acionamento (*Press Point*) no mesmo lugar. Anote o valor que ficou bom.
3. Mexa o analógico esquerdo de leve e solte. **Esperado:** o whammy só reage fora do centro (o Input System ignora os primeiros 12,5% do curso).

## 3. Calibração guiada (mudança do fork) [depois do build]

**Configurações → Geral → Calibração → Abrir Calibrador** (*Settings → General → Open Calibrator*).

1. **Calibrar latência** (A). **Esperado:** instruções em português, legíveis, cabendo na tela.
2. Aperte qualquer botão para começar. Toque junto com cada batida por **30 s** (a música toca 2 vezes). Use a **palhetada (direcional ↓)**, que é o movimento que mais importa no jogo. **Esperado:** contador "Toque N".
3. No fim, espere 1 s: aparecem **Salvar no perfil** (A), **Salvar para todos** (Y), **Repetir** (X), **Voltar** (B).
   - **Esperado:** resultado em ms, consistência (boa/razoável/baixa) e quantos toques foram usados. Se a consistência sair "baixa", repita.
4. Escolha **Salvar no perfil**. Confira em **Perfis**, no seu perfil, o campo de calibração de entrada com o mesmo valor.

Anote: o resultado (ms), a consistência, e se o texto ficou cortado ou pequeno demais.

## 4. Jogar [depois do build]

Toque as 3 músicas, primeiro no **Medium**, depois no **Expert**:

| Música | O que ela testa |
|---|---|
| Admiral Bob: *The Beach is No Place…* | andamento fixo (124 BPM): referência de sincronia |
| Blue_Wave_Theory: *Attack of the Aguaviva* | gravação ao vivo, andamento variando (165→175 BPM) |
| Kevin MacLeod: *Burn The World Waltz* | compasso 3/4, metal denso (o chart mais difícil de gerar) |

Durante cada música, observe:

- **Sincronia:** as notas batem com o som? Se todas parecem atrasadas ou adiantadas do mesmo jeito, é calibração (repita a seção 3). Se varia ao longo da música, anote o momento aproximado.
- **HOPOs** (notas com aparência diferente): dá para tocar só com os trastes, sem palhetar?
- **Sustains:** segurando o gatilho até o fim, o sustain não pode cair.
- **Star power:** junte 2 frases (notas brilhantes) e ative com **View**. O whammy (analógico X) em sustains de star power deve encher a barra.
- **Chart:** ficou parecido com a música? Notas estranhas, trechos vazios ou cheios demais? Anote a música e o minuto.
- **Desempenho:** **Configurações → Geral → Mostrar Avançado → Exibir Contador de FPS**. Esperado: 60 fps ou mais, estável, e áudio sem estalos ou engasgos.
- Resultado final: porcentagem de acertos e estrelas de cada música/dificuldade.

## 5. Autochart com uma música sua (já dá para testar)

1. Uma vez só: `scripts\preparar-ambiente.ps1`.
2. **Arraste um mp3 seu em cima de `scripts\gerar-musica.bat`** e informe nome e artista.
3. **Esperado:** em ~1 min, a pasta aparece em `C:\Dev\GuitarHero\songs\Artista - Música\`, com `relatorio.md`. No fim do relatório, "Validação no YARG.Core" deve dizer **OK**. Se o Windows barrar o validador, ele roda no Docker (Docker Desktop precisa estar aberto) ou aparece "não executada" com o motivo.
4. [depois do build] No jogo, **Atualizar todos os caches** e jogue a música.

Anote: tempo que levou, o que o relatório diz, e se o chart ficou jogável.

## 6. Corrigir um chart no Moonscraper (opcional)

1. Instale o Moonscraper (instalador verificado em `_downloads\`; ver `autochart/README.md`). O Smart App Control pode barrar o instalador, que não tem assinatura.
2. *File → Open* no `notes.chart`, edite, salve. `scripts\validar-musica.ps1 "pasta da música"` confere o chart com o código do jogo.

## 7. Como relatar

Para cada problema, anote: **música, dificuldade, minuto aproximado, o que aconteceu, o que era esperado**. Ajuda muito mandar também:

- o **replay** da partida: pasta `scores\replays` dentro de `%USERPROFILE%\AppData\LocalLow\YARC\YARG\<canal>\`. O canal é `release` num build normal e `dev` jogando pelo editor do Unity. Com o replay eu reproduzo a partida na engine, com os mesmos inputs;
- o **log** do jogo: pasta `logs` no mesmo lugar, e o `Player.log` do Unity em `%USERPROFILE%\AppData\LocalLow\YARC\YARG\`.

## O que ainda não foi testado (honestidade)

- **Nada do jogo rodando foi testado ainda.** O código do fork compila (verificador próprio, 0 erros) e a lógica tem testes automáticos (43 testes .NET: engine, histerese, calibração), mas telas, controle real, áudio e desempenho só no seu teste.
- Controle deslizante do ponto de soltura dos gatilhos na tela de binds: ainda não existe (o valor fica no arquivo de binds; precisa do editor do Unity).
- Calibração de vídeo guiada: não existe. Use o campo *Calibração de Vídeo (ms)* se as notas parecerem fora do tempo em relação à linha de acerto.
