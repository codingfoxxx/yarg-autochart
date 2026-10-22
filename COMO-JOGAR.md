# Guia Rápido: Como Jogar Guitar Hero na Manete (Controle)

Este guia explica como jogar o YARG no controle comum (Xbox, PlayStation ou genérico), por que as notas não estavam tocando antes e como importar músicas oficiais e criar suas próprias músicas.

---

## 1. Por que a manete não funcionava e as notas não tocavam?

Havia dois motivos principais:

1. **O perfil padrão do jogo estava vinculado apenas ao Teclado:**
   - O YARG cria por padrão um perfil de teclado. Se o controle não estiver atribuído ao perfil ativo, o jogo ignora os comandos da manete durante a música.
2. **Falta de Palhetada (Strumming):**
   - No simulador original com guitarra de plástico, para tocar notas normais você precisa segurar o traste **e dar uma palhetada (Strum)** no direcional.
   - Quem joga na manete (controle) quer apenas apertar o botão no ritmo da música (como no Guitar Hero clássico de PS2/Xbox 360 ou no *Gamepad Mode* do Clone Hero). Sem o modo de notas de tap ativado, apertar apenas o botão resultava em **Miss** contínuo.

### O que já foi corrigido para você:
- **Modificador `AllTaps` ativado no seu perfil:** Todas as notas agora são acertadas **diretamente ao pressionar o botão no tempo certo**, sem obrigar palhetada!
- Se você quiser usar o direcional (palheta) junto, ainda funciona normalmente.

---

## 2. Como conectar a manete e começar a jogar agora

1. **Conecte sua manete** via cabo USB no PC.
2. Abra o jogo executando o atalho na Área de Trabalho ou direto em:
   `C:\dev\GuitarHero\_builds\YARG\YARG.exe`
3. No Menu Principal:
   - Vá em **Perfis** (*Profiles*).
   - No seu perfil (**New Profile** ou crie um novo perfil de **Guitarra / 5 Trastes**):
   - Clique em **Adicionar Dispositivo** (*Add Device*).
   - Escolha o seu controle na lista.
   - Na janela que perguntar *"Which kind of controller is this?"*, selecione **Gamepad**.
4. **Mapeamento padrão dos botões (Layout Clássico de 5 dedos):**

| Ação / Traste | Botão do Controle (Xbox / PlayStation) |
|---|---|
| **Verde** | **LT / L2** (Gatilho esquerdo) |
| **Vermelho** | **LB / L1** (Botão superior esquerdo) |
| **Amarelo** | **RB / R1** (Botão superior direito) |
| **Azul** | **RT / R2** (Gatilho direito) |
| **Laranja** | **A / X** (Botão de ação inferior) ou **B / Círculo** |
| **Palhetada (Strum)** | **Analógico Direito ↑ / ↓** (ou Direcional ↑ / ↓) |
| **Star Power** | **View / Select** ou **Y / Triângulo** |
| **Whammy (Distorção)** | **Analógico Esquerdo** (mexer para os lados) |
| **Navegação de Menus** | **Analógico Direito / Direcional** (cima/baixo), **X** (confirmar), **Círculo** (voltar) |

---

## 3. Como importar músicas famosas do jogo oficial

A comunidade inteira de Guitar Hero e Clone Hero mantém todos os pacotes oficiais de todos os jogos da franquia, já sincronizados e com as faixas de áudio originais.

### Onde baixar as músicas oficiais:
1. **Planilha da Comunidade (Clone Hero / YARG Songs Spreadsheet):**
   - Acesse: `https://docs.google.com/spreadsheets/d/13B823ukxdVMocowo1s5XnT3T0BuyM1OhyWuUC3YPEtU`
   - Lá você encontra links diretos para download no Google Drive / Google Drive Mirror de todos os jogos:
     - **Guitar Hero 1, 2, Rocks the 80s**
     - **Guitar Hero 3: Legends of Rock** (todas as músicas famosas: *Through the Fire and Flames*, *Knights of Cydonia*, *Bulls on Parade*, etc.)
     - **Guitar Hero: World Tour, Metallica, Smash Hits, 5, Warriors of Rock, Van Halen, Aerosmith**
     - **Rock Band 1, 2, 3, 4, The Beatles, Green Day**

2. **Repositório de Músicas da Comunidade (Encore / Chorus):**
   - Acesse: [https://en-core.klyser.me/](https://en-core.klyser.me/)
   - Digite o nome de qualquer música ou banda (ex: Queen, Metallica, Iron Maiden, Slipknot, Avenged Sevenfold, etc.).
   - Clique em **Download**.

### Como colocar no jogo:
1. Extraia a pasta da música ou do álbum baixado dentro de:
   `C:\dev\GuitarHero\songs\`
2. Cada pasta de música deve conter os arquivos (`notes.chart` ou `notes.mid`, `song.ini` e `song.ogg`/`song.mp3`).
3. No jogo:
   - Na biblioteca de músicas, aperte **LB (Laranja)** no controle ou clique com o mouse em **Escanear Músicas** (*Scan Songs*).
   - O jogo já está configurado com **Escanear Tudo ao Iniciar**, então novas músicas também aparecem automaticamente ao abrir o jogo!

---

## 4. Como criar qualquer música que você quiser (Algoritmo Autochart)

O seu projeto já conta com uma inteligência artificial completa (`autochart`) baseada em modelos de aprendizado profundo (Spotify Basic Pitch, Beat This! e Demucs) que gera charts completos de 4 dificuldades (Easy, Medium, Hard, Expert) a partir de qualquer arquivo de áudio.

### Passo a passo para gerar:
1. Pegue um arquivo de áudio qualquer no seu PC (`.mp3`, `.ogg`, `.wav`, `.flac`, `.m4a`).
2. **Arraste o arquivo de áudio e solte em cima de:**
   `C:\dev\GuitarHero\scripts\gerar-musica.bat`
3. Digite o nome da música e o nome do artista quando a janela pedir.
4. Em cerca de 40 a 60 segundos, a música estará pronta em `C:\dev\GuitarHero\songs\Artista - Música\`.
5. Abra o jogo e toque!
