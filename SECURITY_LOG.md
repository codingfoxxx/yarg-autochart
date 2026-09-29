# SECURITY_LOG — downloads, verificações e mudanças no sistema

Regras (ver DECISION.md §7): só fontes oficiais; SHA-256 conferido contra o valor publicado pela fonte; assinatura digital (Authenticode) verificada quando existe; Windows Defender (`MpCmdRun -Scan -ScanType 3`) antes de executar; pacotes com versões fixadas; testes de código desconhecido em contêiner.

Máquina: Windows 11 Home, Defender ativo (plataforma 4.18.26080.4, assinaturas 1.459.452.0 em 28/09/2026). Terminal sem privilégio de administrador.

## Ferramentas que já existiam na máquina (não baixadas por este projeto)

| Ferramenta | Versão | Observação |
|---|---|---|
| Git for Windows + Git LFS | 2.53.0.windows.2 / 3.7.1 | Git Credential Manager com a conta `codingfoxxx` |
| Python | 3.11.9 e 3.14.3 (python.org, via Python Install Manager) | o projeto usa 3.11 |
| FFmpeg | 9.0.1 "full_build" (gyan.dev, distribuidor listado em ffmpeg.org) | usado para decodificar/codificar áudio |
| Node.js | 24.14.1 | não usado no projeto |
| Docker Desktop (WSL2) | 29.3.1 | contêineres para isolamento |
| Windows Defender | ver acima | antivírus usado nas varreduras |

## Downloads

| Data | Item | Origem (oficial) | SHA-256 | Verificação | Defender | Uso |
|---|---|---|---|---|---|---|
| 2026-09-28 | Código YARG (clone git, `dev` @ `275e9a13`) | https://github.com/YARC-Official/YARG | commit `275e9a13` | HTTPS do GitHub; LFS ainda não baixado | limpo (pasta inteira) | leitura / fork |
| 2026-09-28 | YARG.Core (submódulo @ `e2d44e8d`) | https://github.com/YARC-Official/YARG.Core | commit `e2d44e8d` | HTTPS do GitHub | limpo | leitura / fork |
| 2026-09-28 | Documentação de formatos (clone raso) | https://github.com/TheNathannator/GuitarGame_ChartFormats | — | só texto, nada executado | — | pesquisa |
| 2026-09-28 | Documentação do YARG (clone raso) | https://github.com/YARC-Official/docs | — | só texto, nada executado | — | pesquisa |
| 2026-09-29 | GitHub CLI 2.101.0 (zip portátil) | https://github.com/cli/cli/releases/download/v2.101.0/gh_2.101.0_windows_amd64.zip | `bc6c814367b193cd8e713611d61e36013c0ef843b8f516458fe3eda039192794` | igual ao `gh_2.101.0_checksums.txt` oficial; `gh.exe` assinado por **GitHub, Inc.** (válida) | limpo | publicar no GitHub |
| 2026-09-29 | Unity Hub 3.21.3 (MSIX) | https://public-cdn.cloud.unity3d.com/hub/prod/3.21.3/UnityHubSetup-3.21.3-x64.msix | `7ae12850cdaa46c534ead6c37ec70a34ed34c4f158d8473804c761595ac254b7` | igual ao manifesto do winget; assinado por **Unity Technologies SF** (válida) | limpo | licença + editor |

### Instalado pelo Lucas, não por este projeto

- **Unity Editor 6000.6.3f1** (+ WebGL e documentação), pelo assistente de primeiro uso do Unity Hub, em 29/09 ~00:29. O próprio Hub validou o checksum ("Checksum check: Passed") e instalou em `C:\Program Files\Unity\Hub\Editor\6000.6.3f1` (~8,4 GB). **Não é a versão usada pelo YARG** (6000.3.5f2); pode ser desinstalado pelo Hub para recuperar espaço.

## Binários que já vêm dentro do repositório do YARG

45 binários versionados no commit `275e9a13` (bibliotecas nativas de terceiros usadas pelo jogo). Varredura do Defender na pasta inteira: **nenhuma ameaça**. Hashes e assinaturas dos binários Windows abaixo; os de Linux/macOS não são usados neste projeto (listados só com hash).

<!-- tabela gerada por script (ver PROGRESS.md) -->

| Arquivo | SHA-256 | Assinatura |
|---|---|---|
| `Assets/Plugins/BassNative/Linux/x86_64/libbass.so` | `35b44d8d38c711191ca7bf931cc96c7c5e8deb0e5bc0d187c87be978da31eb16` | — |
| `Assets/Plugins/BassNative/Linux/x86_64/libbass_fx.so` | `63a41ba9627d4577874fd8f241789834ad058f4ef3bac930bf9bbce54b4cedba` | — |
| `Assets/Plugins/BassNative/Linux/x86_64/libbassmix.so` | `a5a3082ce6873ad992168cd77454934d7955ff24696f9e32f005258164f9eae5` | — |
| `Assets/Plugins/BassNative/Linux/x86_64/libbassopus.so` | `e5e9fcf72dbf122b1b6d0cfecaee7463a2721fef08aa08e9cac2df65ca95a942` | — |
| `Assets/Plugins/BassNative/Mac/libbass.dylib` | `81cdff529b28db3d84aac9097047f02aebf255f0a7d486951879cfdb3dba617c` | — |
| `Assets/Plugins/BassNative/Mac/libbass_fx.dylib` | `a1bcbb5f381138ecc37d64b009171b30a5f8028c994dcc2b25cf547fefe5022d` | — |
| `Assets/Plugins/BassNative/Mac/libbassmix.dylib` | `db84a970531b29290a4d9468d1eca1d84f4b84b9ebd66ccccbc2772e2bed3ce6` | — |
| `Assets/Plugins/BassNative/Mac/libbassopus.dylib` | `ca6c29e8fd3ef3d50b9e6a86fffd2dc3ef56b61fdd8f7448fe37bd0f4a31bde2` | — |
| `Assets/Plugins/BassNative/Windows/x86/bass.dll` | `d92b8bf2f976a7f021187b862a48cff01f5e5b23f4bb907a89def9350be3345d` | válida: Un4seen Developments Ltd |
| `Assets/Plugins/BassNative/Windows/x86/bass_fx.dll` | `7bc733acc1d2b89e5a6546f4ebc321b1c2370e42354ea415bc5fcc6807275eba` | sem assinatura |
| `Assets/Plugins/BassNative/Windows/x86/bassasio.dll` | `e1e648977210d75e85e57ca18ede64fbb3ba70797e549af2a001f993c1518b95` | válida: Un4seen Developments Ltd |
| `Assets/Plugins/BassNative/Windows/x86/bassmix.dll` | `cff3edc109bc0d186ba8ddf60bc99e48ff3467771e741c7168adbdbe03379506` | válida: Un4seen Developments Ltd |
| `Assets/Plugins/BassNative/Windows/x86/bassopus.dll` | `c27d0897e66a637ba13eb03d3ea16d53d6e0111baabb5b9344f2693f3c520141` | válida: Un4seen Developments Ltd |
| `Assets/Plugins/BassNative/Windows/x86/basswasapi.dll` | `41543ef516df19cf3d167050377f8dbaf2ce5e1e3f9413aae6decca50498d19a` | válida: Un4seen Developments Ltd |
| `Assets/Plugins/BassNative/Windows/x86_64/bass.dll` | `16ea6a7ca7abaf22ea20298770ab93cd5cb931dde173dfe859ab9f2bf5c1b487` | válida: Un4seen Developments Ltd |
| `Assets/Plugins/BassNative/Windows/x86_64/bass_fx.dll` | `a6e1847eef52d882b4137af514d834c2e220daceb417c821d1e502fb7a34c84a` | sem assinatura |
| `Assets/Plugins/BassNative/Windows/x86_64/bassasio.dll` | `73bf79c8eccd63dea8eb3e3e9b5ffe6f9406deb9bbcccc7557ca54f5013b4b96` | válida: Un4seen Developments Ltd |
| `Assets/Plugins/BassNative/Windows/x86_64/bassmix.dll` | `5b4a9fe4667ca4698defb7a6a550b6d026aeb75b60bb47a5e2db71bc2eb54e2c` | válida: Un4seen Developments Ltd |
| `Assets/Plugins/BassNative/Windows/x86_64/bassopus.dll` | `f56fd9bd59bcf510f1d61855f6dc564205ef57a8a01ebabe4d1e199bf7c1677e` | válida: Un4seen Developments Ltd |
| `Assets/Plugins/BassNative/Windows/x86_64/basswasapi.dll` | `6f0869c11431e01f759fbe1cd6080299c833c519eb8ab1feae12106907b1fbd1` | válida: Un4seen Developments Ltd |
| `Assets/Plugins/Demigiant/DOTween/DOTween.dll` | `f0833b8c3ee2bb33cd480150052a161ad5bc22137a8f5ca274fd9fe490cfbd93` | sem assinatura |
| `Assets/Plugins/Demigiant/DOTween/Editor/DOTweenEditor.dll` | `f232b168c267dc04a5dc43679667daee923a1b3b3ceb493a0cc025ed4e07b5b0` | sem assinatura |
| `Assets/Plugins/DiscordGameSDK/Plugins/aarch64/discord_game_sdk.bundle` | `48755dc71a43075b2ab511b16be0e166ee1fb0ebc4530ce8ff8fe061f2cd742b` | — |
| `Assets/Plugins/DiscordGameSDK/Plugins/aarch64/discord_game_sdk.dylib` | `48755dc71a43075b2ab511b16be0e166ee1fb0ebc4530ce8ff8fe061f2cd742b` | — |
| `Assets/Plugins/DiscordGameSDK/Plugins/x86/discord_game_sdk.dll` | `e49ca81252852250a254f8c3f169859696542af2d0a81348f5984f0af880f43b` | válida: Discord Inc. |
| `Assets/Plugins/DiscordGameSDK/Plugins/x86_64/discord_game_sdk.bundle` | `c4960f31a59020f94ce394fdfc5762a6f5077dd711d26ce936086e77beceea09` | — |
| `Assets/Plugins/DiscordGameSDK/Plugins/x86_64/discord_game_sdk.dll` | `a6b6d7df00a58dc50248d91048578d0fe52182286b487ef89a961fd10467dbd1` | válida: Discord Inc. |
| `Assets/Plugins/DiscordGameSDK/Plugins/x86_64/discord_game_sdk.dylib` | `c4960f31a59020f94ce394fdfc5762a6f5077dd711d26ce936086e77beceea09` | — |
| `Assets/Plugins/DiscordGameSDK/Plugins/x86_64/discord_game_sdk.so` | `ed22f6755eff063893f3a0fe3fad02b1ddf260fba1c3064d3fe3046b350c75d8` | — |
| `Assets/Plugins/LibUSB/libusb-1.0.dylib` | `a21ab9e5fad7253a40b49940fe99588821ebc3d78812ec5b9f86ab4fdb4e6795` | — |
| `Assets/Plugins/LibUSB/libusb-1.0.so` | `751349e3def1808981dc26bbeb746e2d6ff4ca97fc2c8bc8faaa8f46c879057f` | — |
| `Assets/Plugins/STB2CSharp/Linux/x86_64/STB2CSharp.so` | `c0ee414178177e049ce27ac4f0c77a967f87a0ef64e90dac020799e53f47873d` | — |
| `Assets/Plugins/STB2CSharp/MacOS/STB2CSharp.dylib` | `6193f84003181780654dd54f249c4e37b916aedf87d802376639995fde570d4f` | — |
| `Assets/Plugins/STB2CSharp/Windows/x86/STB2CSharp.dll` | `67ad1e1d694124c0f721b492565d87266331ee9b5814117dd5f5e4bf5c6042e0` | sem assinatura |
| `Assets/Plugins/STB2CSharp/Windows/x86_64/STB2CSharp.dll` | `e703bb89dd229066e73c91371c47bebb20b0fd1fdede0dbedcddd57b5e4e6eea` | sem assinatura |
| `Assets/Plugins/Sqlite3/Linux/x86_64/libsqlite3.so` | `d0e8964ccb884e2a065dd92d8199c882af4ceba29a11486613148169eb9b8675` | — |
| `Assets/Plugins/Sqlite3/Mac/libsqlite3.dylib` | `5d99d35cee2885bb0bf5b4ea1b6047f63819d17c3291d260ec237269dcd57064` | — |
| `Assets/Plugins/Sqlite3/Windows/x86_64/sqlite3.dll` | `0f5e3505f3632ba654823d83165d9950d3ccb86c16ea6daf0fb90707eeecf8dd` | sem assinatura |
| `Assets/Plugins/YargAudio/Linux/x86_64/libyarg_audio.so` | `0042baa10bbb369c84e21fe41192d0aaf0ccc819c1ca4214ef482929d914ed94` | — |
| `Assets/Plugins/YargAudio/Mac/libyarg_audio.dylib` | `158fa9abdd078e6b8705db88183785097330a7c9be6db00af978b6f14981d56c` | — |
| `Assets/Plugins/YargAudio/Windows/x86_64/yarg_audio.dll` | `5fcdf899cfe6970ca7d3263afd1cdd194a7bda25f379c0d8ece2764b9e360f5a` | sem assinatura |
| `Assets/Plugins/vlc/LibVLCSharp.dll` | `d324ef44d6c1266a8bedce10c0a55392081bc255fb16da9fa74262b15c88fbe2` | sem assinatura |
| `Assets/Plugins/vlc/Linux/x86_64/libVLCUnityPlugin.so` | `98c104bdad458c316f8a171fdffc42bb668cbde5d8e8934d8b04b5161373a094` | — |
| `Assets/Plugins/vlc/Mac/libVLCUnityPlugin.dylib` | `c464e49b6cedfa3112609586d3cd3ae7f32572c5669e4e5bdc921e7f46d8dd83` | — |
| `Assets/Plugins/vlc/Windows/x86_64/VLCUnityPlugin.dll` | `71b1faa948338a8d1c911cae45ffd91f9c3e1b158ac983e91ec6da0f043d56b0` | sem assinatura |

## Mudanças feitas no sistema

| Data | Mudança | Como desfazer |
|---|---|---|
| 2026-09-28 | Limpeza dos caches do npm (6,0 GB) e do pip (1,7 GB), autorizada pelo Lucas | nada a desfazer (caches se recriam) |
| 2026-09-29 | Unity Hub instalado por usuário (MSIX) | Configurações → Apps → Unity Hub → Desinstalar |
| 2026-09-29 | Atalho `Guitar Hero.lnk` na Área de Trabalho apontando para `C:\Dev\GuitarHero` | apagar o atalho |
| 2026-09-29 | Vigia noturno (processo PowerShell oculto, `_work\vigia-noturno.ps1`) que impede a suspensão por ociosidade enquanto há trabalho, suspende o PC quando ocioso e pode registrar a tarefa agendada `GuitarHero-Despertar` (acordar o PC) | encerra sozinho às 11:00; criar `_work\parar-vigia.txt` para parar antes; `Unregister-ScheduledTask GuitarHero-Despertar` |
| 2026-09-29 | Docker Desktop iniciado; o disco virtual `docker_data.vhdx` cresceu de 24,68 para 26,50 GB (imagem e camadas do sandbox) | remover a imagem `python:3.11-slim-bookworm` pelo Docker libera espaço dentro do disco virtual (o arquivo não encolhe sozinho) |
| 2026-09-29 | `.venv` (Python 3.11, ~1,5 GB), `models\` (~130 MB), `_cache\stems` (~120 MB por música) | apagar as pastas |
| 2026-09-29 09:33 | Unity **6000.6.3f1** desinstalado pelo desinstalador oficial (elevado, a pedido do Lucas); liberou ~15 GB. A sobra (2 arquivos de metadados do Hub) foi removida às 10:17 | reinstalar pelo Hub, se quiser |
| 2026-09-29 10:17–10:30 | Unity **6000.3.5f2** instalado em modo silencioso em `C:\Program Files\Unity\Hub\Editor\6000.3.5f2` (elevado, a pedido do Lucas) | Painel de Controle → Programas, ou o `Uninstall.exe` da pasta |
| 2026-09-29 | Cópia só-de-scripts do fork para verificar compilação (`_work\unity-compilecheck`, ~1,3 GB com a `Library` do Unity); imagem Docker do SDK .NET e volume `guitarhero-nuget` | apagar a pasta; `docker volume rm guitarhero-nuget`; `docker image rm mcr.microsoft.com/dotnet/sdk:10.0` |

## Downloads da madrugada de 29/09 (pilha do auto-charting e ferramentas)

| Item | Origem (oficial) | SHA-256 / verificação | Defender | Onde / uso |
|---|---|---|---|---|
| .NET SDK 10.0.401 (zip portátil) | builds.dotnet.microsoft.com (URL e SHA-512 do `releases.json` oficial) | SHA-512 `24b670ad…c79430` confere; `dotnet.exe` assinado por **.NET (Microsoft)** | limpo | `_tools\dotnet`; testes e validador |
| Imagem Docker `python:3.11-slim-bookworm` | Docker Hub (imagem oficial) | digest `sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b` | — | contêiner descartável do sandbox |
| Pacotes Python (1ª instalação, **dentro do contêiner**) | PyPI + download.pytorch.org (CPU) | versões em `_work/sandbox/freeze-linux.txt` | — | teste de fumaça isolado (`sandbox/`) |
| 65 wheels do Windows (CPython 3.11) | PyPI, baixados no contêiner | hashes em `autochart/requirements-win.lock` (SHA-256 do lock `e443d7e8…`); instalação com `--no-index --require-hashes`; torch 2.8.0 = `8c7ef765…` (igual ao PyPI) | limpo | `.venv` |
| Pesos Beat This! `final0.ckpt` | cloud.cp.jku.at (URL que está no código oficial do beat_this) | `8c328b45f59d8dd3dff219253ff6a8d6482be57d0133a29140e2febbf8eb8331` (baixado no contêiner; igual nas 2 execuções) | limpo | `models\beat_this` |
| Pesos Demucs `htdemucs_6s` (`5c90dfd2.safetensors`) | huggingface.co/adefossez/HTDemucs-6s (revisão `3c5ee475…`) | `d2a1745f0744721f6b8ca5bf469b67c651ea5ed1b52998cab033b2158609d411` | limpo | `models\demucs` |
| wheel `beat_this-1.1.0` (só para ler o código) | PyPI | `3f2b2d1e…a645` | — | inspeção |
| wheel do torch 2.8.0 (teste do Smart App Control) | PyPI | `8c7ef765…80aa`, igual ao PyPI | — | DLLs extraídas e carregadas num processo isolado; apagado depois |
| Texto da GPL-3.0 | gnu.org/licenses/gpl-3.0.txt | `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` (hash conhecido do texto canônico) | — | `COPYING` no fork |
| 3 MP3 de teste (CC BY) | ccMixter e incompetech (páginas oficiais) | `e1a0ad8f…`, `a5ced5ab…`, `35e03b3e…` (LICENSES.md §5) | limpo | `_work\songsrc` |
| Moonscraper Chart Editor 1.5.13 (instalador Win64) | github.com/FireFox2000000/Moonscraper-Chart-Editor (release oficial) | `30c5d0070cdfca7dc7b0f1c973468b12995ff3e14685a1308790257aa030fefe` = digest do GitHub; **sem assinatura digital** | limpo | `_downloads`; **não executado** (a instalação fica com o Lucas) |

| Instalador do Unity 6000.3.5f2 (`UnitySetup64-6000.3.5f2.exe`, 4.181.263.080 bytes) | download.unity3d.com (URL tirada da API oficial de releases da Unity, `services.api.unity.com`) | MD5 `IIwgjcwpDGQt+9lTFYWs8Q==` = o publicado pela Unity; SHA-256 `dd9dc4e81480bdef…4e007a`; assinatura **válida, Unity Technologies SF** (DigiCert) | limpo | instalado e apagado em seguida |
| Imagem Docker `mcr.microsoft.com/dotnet/sdk:10.0` | Microsoft Container Registry (imagem oficial) | digest `sha256:35d40304542c8689331f8cab17c65926cdf48fe711e289321d71924b230a7d29` (fixado nos scripts) | — | testes .NET e validador fora do Windows; volume `guitarhero-nuget` guarda o cache do NuGet |
| Pacotes NuGet do jogo (FuzzySharp 2.0.2, ManagedBass* 3.1.1, Melanchall.DryWetMidi.Nativeless 7.0.0, Microsoft.IO.Redist 6.1.3, Microsoft.VisualStudio.SolutionPersistence 1.0.52, System.Diagnostics.Tracing 4.3.0, System.Runtime.CompilerServices.Unsafe 6.0.0, UniRx 5.4.1, ZString 2.5.1, sqlite-net 1.6.292) | nuget.org, via `dotnet restore` do SDK oficial (versões exatas do `Assets/packages.config` do YARG) | assinaturas de repositório do nuget.org verificadas pelo `dotnet restore` | — | `_tools\nuget-packages`; copiados para a cópia de verificação (`_work\unity-compilecheck\Assets\Packages`) |
| Pacotes do Unity (UPM) do projeto | packages.unity.com, package.openupm.com, registry.npmjs.com e GitHub (pacotes git fixados por commit no `packages-lock.json` do YARG) | baixados pelo próprio editor do Unity; o 6000.6.3f1 trocou algumas versões (ex.: Input System 1.17.0 → 1.20.0, Cinemachine 2.10.5 → 6.6.0) | — | só na cópia de verificação (`Library\PackageCache`, ~1,2 GB, apagável) |

### Análise de risco dos pacotes e modelos

- **Typosquatting:** os 65 nomes foram revisados. `httpx2`/`httpcore2` pareciam suspeitos (o pacote conhecido é `httpx`), mas são o sucessor mantido pela organização **verificada** da Pydantic (github.com/pydantic/httpx2, ~1,5 mil estrelas, releases batendo com o PyPI) e são exigidos pelo `huggingface_hub` 2.0.0 oficial.
- **Pesos que executam código ao carregar:** o checkpoint do Beat This! é um pickle do PyTorch. No PC ele só é aberto pelo caminho local, que usa `torch.load(weights_only=True)` (só tensores); o primeiro carregamento (por URL, sem essa proteção) aconteceu apenas no contêiner. O Demucs vem em safetensors, mas o carregador instancia a classe escrita nos metadados; por isso exigimos a classe `demucs.htdemucs.HTDemucs` antes de carregar, além do hash. O caminho legado do Demucs (arquivos `.th` com `weights_only=False`) não é usado.
- **Telemetria:** o `huggingface_hub` 2.x baixa um catálogo de "agentes de IA" (`.agent_harnesses.json`) para marcar requisições feitas dentro de agentes. Em tempo de execução a ferramenta liga `HF_HUB_OFFLINE=1` e `HF_HUB_DISABLE_TELEMETRY=1` e não acessa a rede.
- **setup.py de terceiros:** nenhum rodou no PC (todos os pacotes têm wheel; os que não tivessem seriam compilados no contêiner).

### Smart App Control (Windows 11) — descobertas

- Está **ativo em modo de bloqueio** (`VerifiedAndReputablePolicyState = 1`), com as políticas carregadas no boot.
- Bloqueou as DLLs do **torch 2.14** (sem assinatura, sem reputação). Solução sem mexer na proteção: fixar **torch 2.8.0**, cujas DLLs são aceitas.
- Bloqueia uma DLL .NET compilada aqui quando ela é o **programa principal** (`dotnet app.dll` ou o `.exe` gerado), mas não quando é carregada como **dependência** de um hospedeiro assinado pela Microsoft (`testhost`). Por isso o validador roda via `dotnet test`.
- **Risco para o jogo:** o executável que o Unity gerar a partir do código (`YARG.exe`) será um binário novo, sem reputação, e pode ser bloqueado. Será verificado no primeiro build.
  - Conferido no modelo de player do Unity instalado (6000.6.3f1, `win64_player_nondevelopment_mono`): `UnityPlayer.dll`, `UnityCrashHandler64.exe` e o runtime Mono (`mono-2.0-bdwgc.dll`) são assinados pela Unity Technologies SF; os plugins, pela AMD, NVIDIA e Microsoft. Só o **`WindowsPlayer.exe` não tem assinatura**, e é justamente ele que vira o `YARG.exe` (o build troca o ícone e as informações de versão, o que muda o hash). Conclusão: o bloqueio é provável; as DLLs gerenciadas (carregadas pelo Mono) provavelmente não são checadas.
  - Se for bloqueado, as opções honestas são: (a) jogar pelo próprio editor do Unity (assinado), (b) o Lucas desligar o SAC (decisão dele, irreversível), (c) assinar o executável com um certificado de assinatura de código de verdade (pago). Contornos que usam programas do sistema para carregar o jogo não serão usados.
- O Smart App Control **não deve ser desligado** sem decisão do Lucas: desligado, só volta reinstalando o Windows.

#### Madrugada de 29/09, 02:38–03:05: o SAC também barra o **editor** do Unity

- Teste: o Unity **6000.6.3f1** (instalado sozinho pelo Hub; o projeto usa 6000.3.5f2) aberto em modo batch numa cópia só-de-scripts do fork (`_work\unity-compilecheck`). Licença: funcionou pelo cliente de licenças do Hub (a ativação do Lucas), sem nada a mais.
- Resultado: **"Scripts have compiler errors"** sem nenhum erro de C#. O log do Code Integrity (eventos 3077, política `VerifiedAndReputableDesktop` = Smart App Control) mostra o `dotnet.exe` do Unity impedido de carregar `ApiUpdater.MovedFromExtractor.dll` (486 vezes; o pipeline de compilação do Unity 6 roda essa ferramenta para cada assembly), `CommandLine.dll` (do AssemblyUpdater), `Unity.UIToolkit.SourceGenerator.dll` e `IlInterpreterAnalyzer.dll` (pacote `com.unity.pipeline`). Todas são DLLs **sem assinatura** que acompanham o próprio Unity. Outras DLLs sem assinatura do Unity (ex.: `Unity.SourceGenerators.dll`, `AssemblyUpdater.dll`) carregaram: a decisão é por arquivo, pela reputação na nuvem.
- Consequência: **com o SAC ligado, o Unity 6000.6.3f1 não compila projeto nenhum nesta máquina.** Se o 6000.3.5f2 vai ter o mesmo problema, só se sabe instalando (as DLLs equivalentes dele podem ter reputação ou não).
- O que **não** foi feito: nenhuma tentativa de fazer o Windows aceitar essas DLLs (nada de desligar, contornar ou "treinar" a proteção).
- O que foi feito para continuar verificando o código: o compilador C# que o Unity usa (Roslyn do SDK .NET embutido, `csc.dll`/`VBCSCompiler.dll`, **assinados pela Microsoft**) roda normalmente; `tools/unity-compile-check` executa só as etapas de compilação do grafo de build que o editor gravou antes de falhar.

- **Build real (29/09, 10:35–10:49), Unity 6000.3.5f2:** "Build Finished, Result: Success". Durante o build o Windows barrou `IlInterpreterAnalyzer.dll` (36×, analisador do pacote `com.unity.pipeline`), `libarchive-13.dll`, `libexpat-1.dll` e uma DLL temporária com nome de hash, sem impedir o build. **O `YARG.exe` gerado (sem assinatura) abriu normalmente**, chegou ao menu e fechou sem erro, nenhum evento 3077 ao rodar. O jogo acessa a internet (mensagens, fontes/gêneros de música) salvo com `-offline`, como o original.
- **Atualização (29/09, 10:32):** com o Unity **6000.3.5f2** as mesmas ferramentas (`ApiUpdater.MovedFromExtractor.dll`, `AssemblyUpdater.dll` + `CommandLine.dll`, também sem assinatura) **carregam normalmente**, sem nenhum evento 3077: elas têm reputação. O bloqueio era específico da 6000.6.3f1, que é mais nova e menos difundida.

#### DLLs .NET compiladas aqui: bloqueio inconsistente

- 02:55: a `EngineTests.dll` recompilada (hash `2D5ABD7E…`) foi barrada ao ser carregada pelo `testhost.exe` (antes, nesta mesma noite, as versões anteriores carregavam). 02:56: o `Validator.dll` recompilado também foi barrado. 03:00: um novo build do `Validator.dll` **carregou normalmente**; a `EngineTests.dll` (mesmo hash) continuou barrada às 03:04.
- Mitigações (sem mexer no SAC): (1) os testes .NET rodam num **contêiner Linux oficial da Microsoft** (`scripts/testes-dotnet-conteiner.ps1`, imagem `mcr.microsoft.com/dotnet/sdk:10.0`, digest abaixo); (2) o autochart, se o Windows barrar o validador, roda o mesmo validador no contêiner e, sem Docker, marca a validação como "não executada" com o motivo, em vez de acusar erro no chart.
