# LICENSES — licenças do projeto, do fork e dos conteúdos

Inventário feito em 2026-09-29 lendo os arquivos de licença do repositório e as páginas oficiais (nada foi assumido pelo nome). Versões: YARG `dev` @ `275e9a13`, YARG.Core @ `e2d44e8d`. **Não é parecer jurídico**; é o levantamento que orienta o que publicamos.

## 1. Resumo e política adotada

| O quê | Situação | O que fazemos |
|---|---|---|
| **Código-fonte do fork** (`codingfoxxx/YARG`) | LGPL-3.0; publicar o fork é permitido | Publicado, com `LICENSE` original, `COPYING` (texto da GPL-3.0, que faltava), `NOTICE` e `FORK.md` |
| **Executável (build) do jogo** | Só uso **não comercial** (BASS, sons CC BY-NC, shader CC BY-NC-SA). O nome "YARG" e os logos **não têm licença de uso**: um executável modificado distribuído como "YARG" usaria a marca de terceiros | Build **só local** por enquanto. Um Release público exige antes: trocar nome/ícone/logos (rebranding), pacote de avisos de terceiros, sem libvlc e sem o app do Discord da YARC. **Decisão pendente do Lucas** |
| **Ferramentas deste repositório** (`yarg-autochart`) | Código nosso | MIT (`LICENSE`); dependências mantêm as próprias licenças (§4) |
| **Músicas de teste** | Só CC0 / CC BY / CC BY-SA com fonte oficial | Áudio fora do git, nos Releases, com créditos (§5) |
| **Música comercial** | Proibida no repositório | Nunca commitada; `.gitignore` bloqueia arquivos de áudio |

## 2. Código do YARG e do YARG.Core

- `LICENSE` (raiz do YARG e do YARG.Core): "GNU LESSER GENERAL PUBLIC LICENSE Version 3, 29 June 2007" (texto idêntico ao da gnu.org). O README diz "(or later)". Não há cabeçalho de licença por arquivo.
- `YARG.Core/YARG.Core/package.json` declara `"license": "MIT"`: contradição de metadados; vale o `LICENSE` (LGPL-3.0).
- Parser do Moonscraper dentro do YARG.Core (`MoonscraperChartParser/`): BSD-3-Clause, "Copyright (c) 2016-2021, Alexander Ong" (manter os cabeçalhos).

**Obrigações da LGPL-3.0 ao distribuir um binário modificado**
1. Manter todos os avisos e declarar as modificações com data (feito: `NOTICE`, `CHANGELOG-FORK.md`).
2. Acompanhar o texto da GPL-3.0 (LGPL §4b) — adicionado como `COPYING`.
3. Oferecer o código-fonte correspondente, incluindo o submódulo YARG.Core e os objetos LFS. Os "Source code (zip)" automáticos do GitHub **não** incluem submódulos nem LFS: anexar um arquivo próprio ou apontar a tag + instruções.
4. Permitir trocar as bibliotecas: o player Windows usa **Mono** (as DLLs em `YARG_Data/Managed` são substituíveis). **Não mudar para IL2CPP.**

## 3. Componentes de terceiros dentro do jogo

| Componente | Onde | Licença (trecho literal / fonte) | Pode publicar no código? | Pode ir no executável? | Obrigações / alertas |
|---|---|---|---|---|---|
| **BASS** 2.4.17 + bassmix, bassopus, bassasio, basswasapi (Un4seen) | `Assets/Plugins/BassNative/**` | "BASS is free for non-commercial use. If you are a non-commercial entity (eg. an individual) and you are not making any money from your product (through sales/advertising/etc), then you can use BASS in it for free." (`bass.txt`, un4seen.com) | Sim (já está no upstream) | Sim, **só não comercial** | DLLs sem modificação; incluir `bass.txt`; sem venda, anúncio ou doação. A frase "These licences only cover your own software, not the publishing of other's software" é ambígua para um fork: considerar pedir confirmação a bass@un4seen.com antes de um Release público |
| **BASS_FX** (JOBnik) | `**/bass_fx.dll` | "You may freely distribute the BASS_FX package as long as NO FEE is charged and all the files remain INTACT AND UNMODIFIED." | Sim | Sim, sem cobrança | Não modificar |
| **Discord Game SDK** | `Assets/Plugins/DiscordGameSDK/**`; usado em `Assets/Script/Integration/DiscordController.cs` com o **ID de aplicativo da YARC** | Sem arquivo de licença (README do YARG: "Licenseless"); regem os Termos de Desenvolvedor do Discord (uso "solely as necessary to integrate with… your Application"; proíbem redistribuir as APIs) | Incerto (já está no upstream) | Só integrado a um app próprio | Para Release público: desligar o Rich Presence ou usar um app ID próprio |
| **VLC para Unity** (LibVLCSharp, vlc-unity) | `Assets/Plugins/vlc/**` | "vlc-unity is released under LGPLv2.1 (or later)"; LibVLCSharp: LGPL v2.1 | Sim | Sim (DLLs separadas, texto da LGPL-2.1) | **O libvlc em si não está no repositório**; os builds oficiais o adicionam por fora. O pacote noturno do VLC tem módulos GPL. Nosso build vai **sem libvlc** (o jogo usa o VideoPlayer do Unity como alternativa; vídeo de fundo não importa aqui) |
| libusb-1.0 | `Assets/Plugins/LibUSB/*` (Linux/macOS) | LGPL-2.1 | Sim | Sim | Pode vazar para o build Windows pela opção "Any" do importador: podar |
| SQLite 3.44.0 | `Assets/Plugins/Sqlite3/**` | domínio público (sqlite.org/copyright) | Sim | Sim | — |
| stb_image (STB2CSharp) | `YARG.Core/STB2CSharp/**` → `Assets/Plugins/STB2CSharp/**` | MIT ou Unlicense, à escolha | Sim | Sim | — |
| yarg_audio (biblioteca nativa do próprio YARG) | `Native/YargAudio/**` + binários em `Assets/Plugins/YargAudio/**` | sem licença própria → LGPL-3.0 do repositório | Sim | Sim | O CI do upstream recompila e confere o binário versionado |
| DOTween (padrão) | `Assets/Plugins/Demigiant/DOTween/**` | "You can redistribute verbatim copies of the code, along with any readme files and attributions… you cannot redistribute modified versions" | Sim | Sim | Manter `readme.txt`; não editar |
| Haukcode.sACN (cópia modificada) | `Assets/Plugins/Haukcode.sACN/**` | MIT, "Copyright (c) 2018 Hakan Lindestaf" | Sim | Sim | Falta o texto MIT no repositório |
| Pacotes Unity (Input System, URP, TextMesh Pro, Cinemachine…) | `Packages/manifest.json`; cópias de shaders em `Assets/` | Unity Companion License 1.4 (uso ligado a projetos Unity) | Sim | Sim | Requer licença do Unity; Personal limita a < US$ 200 mil de receita |
| Pacotes UPM de terceiros (SoftMaskForUGUI, UniTask, NuGetForUnity, PlasticBand, HIDrogen, UniVRM, Minis/RtMidi, SimpleFileBrowser…) | `Packages/manifest.json` | MIT (ou domínio público no Minis) | Sim (não versionados) | Sim | Avisos MIT no pacote de Release |
| **OpenVAT** | `Packages/manifest.json` (`sharpen3d/openvat-unity`) | **sem licença** no repositório de origem | Não versionado | **Incerto** | Problema do upstream; registrar |
| Pacotes NuGet (DryWetMidi, Newtonsoft.Json, ZString, ManagedBass, FuzzySharp, sqlite-net, UniRx…) | `Assets/packages.config`, `*.csproj` | MIT | Sim (restaurados, não versionados) | Sim | Avisos MIT |
| Fontes (Barlow, Red Hat Display, Noto Sans JP, Noto Sans Symbols 2, Unbounded, Liberation Sans) | `Assets/Art/Fonts/**`, `Assets/TextMesh Pro/Fonts/**` | "This Font Software is licensed under the SIL Open Font License, Version 1.1." | Sim | Sim | Levar linhas de copyright + texto OFL (só o da Liberation está no repositório) |
| Ícones Lucide | `Assets/Art/Menu/**`, `Assets/Art/UI/**` | ISC (+ MIT dos derivados do Feather) | Sim | Sim | Aviso ISC/MIT |
| Poly Haven (textura de madeira) | `Assets/Authoring/Venue/Common/Textures/WoodPlanks*` | CC0 | Sim | Sim | — |
| Emojis EmojiOne (amostra do TextMesh Pro) | `Assets/TextMesh Pro/Sprites/EmojiOne.*` | versão 2 era CC BY 4.0 | Sim | Sim | Atribuição; parece não usado |
| **Sons CC BY-NC 4.0** (freesound, soundslikewillem) | `Assets/StreamingAssets/sfx/chatter.opus` (id 449550, confirmado), `crowd_open_1/2.opus` (id 193062, confirmado, **não creditado no README do upstream**), `crowd_end_1/2.opus` (provável id 193064) | "Attribution NonCommercial 4.0" | Sim, com atribuição | Sim, **só não comercial** | Creditar autor, título, link e licença; dizer que foram cortados e convertidos |
| **Shaders CC BY-NC-SA 3.0** (Shadertoy) | `Assets/Art/Shaders/CheckerBoard.shader` (vai no build, fundo do menu de configurações), `Assets/Authoring/SongTimer.shader` (só na cena de autoria) | "License: CC BY-NC-SA 3.0" | Sim, como arquivos à parte | Só não comercial | Adaptação fica BY-NC-SA; substituir se um dia houver uso comercial |
| Outros áudios (metrônomo, bateria, vox, `calibration_music.ogg`) | `Assets/StreamingAssets/**` | **sem licença/crédito** no repositório (CONTRIBUTING do upstream exige que sejam originais ou licenciados) | Incerto (upstream) | Incerto | Registrado como lacuna do upstream |
| Dicionário CMU | `Assets/Resources/cmudict.txt` | BSD-like, "Copyright (C) 1993-2015 Carnegie Mellon University" | Sim | Sim | Falta o aviso da CMU |
| Detecção de pitch (vocais) | `Assets/Script/Audio/PitchDetection/*` | baseada num projeto Ms-PL (incerto) | Incerto | Incerto | Lacuna do upstream |
| Leitor Milo | `YARG.Core/YARG.Core/IO/Milo/YARGMiloReader.cs` | "adapted from Onyx's Haskell milo file parser" (Onyx é GPL-3.0) | Incerto | Incerto | Possível derivação GPL dentro de arquivo LGPL (upstream) |
| MIDI de teste de música comercial | `YARG.Core/YARG.Core.UnitTests/Engine/Test Charts/drawntotheflame.mid` (Thunderstone) | sem licença | Não está nos nossos repositórios (o submódulo aponta para o YARG.Core oficial) | Não vai no jogo | Se um dia fizermos fork do YARG.Core, não usar esse arquivo em testes nossos |
| **Marca YARG** (nome e logos) | `Images/*`, `Assets/Art/UI/{Logo,Splash_Logo,Icon_*}.png`, `ProjectSettings` (company YARC, product YARG) | Sem política de marca no repositório do jogo; o `LICENSE` do YARC-Launcher: "this license does not grant permission to use the name "YARG"… or any associated YARG logos"; termos da YARC: "YARC does not endorse mods or external programs" | Sim (histórico do upstream; uso nominativo no fork) | **Não sem permissão** | Rebranding antes de qualquer executável público; nunca usar "Guitar Hero", "Rock Band" ou "Clone Hero" como marca |
| Setlist oficial e serviços da YARC | não está no repositório; o código detecta o setlist do launcher e baixa um catálogo remoto | "The YARG setlist IS NOT open source… must be used exclusively for YARG" | — | — | Não incluir; em Release público, considerar desligar a detecção e o catálogo remoto |

## 4. Ferramentas e dependências do repositório `yarg-autochart`

| Componente | Licença | Observação |
|---|---|---|
| Nosso código (autochart, validador, testes, scripts) | MIT | `LICENSE` |
| YARG.Core (usado pelo validador e pelos testes) | LGPL-3.0 | via submódulo (não copiado); o validador só faz referência à biblioteca |
| Beat This! (`beat-this`) | MIT, **inclusive os pesos** | — |
| Demucs (`demucs`) | código MIT; **pesos "not covered by the MIT license… provided only for scientific purposes"** | uso interno para análise; **stems separados não são publicados** |
| librosa 0.11.0 | ISC | — |
| Basic Pitch 0.4.0 | Apache-2.0 | — |
| ONNX Runtime | MIT | — |
| PyTorch / torchaudio | BSD-3-Clause | — |
| NumPy, SciPy, soundfile | BSD | — |
| mido | MIT | — |
| FFmpeg (já instalado; build "full" do gyan.dev) | GPL (build com componentes GPL) | chamado como programa externo, **não distribuído** |
| Moonscraper Chart Editor 1.5.13 | BSD-3 (usa BASS: não comercial) | editor recomendado; não redistribuído |

A lista final, com versões e hashes, fica no `requirements` travado da ferramenta e no SECURITY_LOG.md.

## 5. Músicas de teste

Ainda não baixadas. Cada música entra aqui com: título, artista, licença (com trecho literal e link da página oficial), URL de download, SHA-256 do arquivo original, e o texto de crédito exigido. Candidatas em [docs/pesquisa/musicas-livres.md](docs/pesquisa/musicas-livres.md).

## 6. Pendências de licença (para decidir com o Lucas)

1. **Executável público:** fazer rebranding (nome, ícone, logos, dados em pasta própria) antes de publicar um Release? Até lá, build só local.
2. Pedir confirmação à Un4seen (BASS) para redistribuir um fork não comercial.
3. Rich Presence do Discord: desligar no fork ou criar um app próprio.
