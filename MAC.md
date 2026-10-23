# Jogar no Mac

O executável de `_builds/` do Windows não roda no Mac: aqui o jogo é compilado a partir do fork. **Testado em 2026-10-23** num MacBook M4 Pro (macOS 26): build em ~7 min, o jogo abre em pt-BR e acha as músicas.

## 1. Baixar o código

```bash
git clone --recurse-submodules https://github.com/codingfoxxx/yarg-autochart.git ~/GuitarHero
cd ~/GuitarHero/YARG
git checkout pessoal
git submodule update --init --recursive
git lfs pull
```

O fork do jogo fica na branch `pessoal` do submódulo `YARG`. Texturas, fontes e modelos estão no Git LFS: sem o `git lfs pull` o build sai sem eles. Sem Homebrew, o `git-lfs` pode ser o binário oficial (`git-lfs-darwin-arm64`, conferir o sha256 do release) em `~/.local/bin`.

## 2. Ferramentas

| Item | Onde | Observação |
|---|---|---|
| Unity Hub | `/Applications/Unity Hub.app` | só para o login e a licença Personal (uma vez) |
| Unity **6000.3.5f2** | `/Applications/Unity/Hub/Editor/6000.3.5f2` | pelo Hub, ou extraindo o `.pkg` oficial (`download.unity3d.com/download_unity/3fa8bc678cb0/MacEditorInstallerArm64/Unity-6000.3.5f2.pkg`) nessa pasta. O build para Mac (Mono) já vem com o editor |
| Blender 4.5 LTS | `/Applications/Blender.app` | o Unity usa para importar `Notes.blend` (notas "Rectangular"); opcional |
| SDK .NET 10 | `~/GuitarHero/_tools/dotnet` | `bash dotnet-install.sh --channel 10.0 --install-dir _tools/dotnet --no-path`; restaura os pacotes NuGet antes do build |

O Hub pode instalar sozinho um editor mais novo no primeiro login; o projeto precisa do 6000.3.5f2.

## 3. Compilar

```bash
~/GuitarHero/scripts/assinatura-mac.sh   # só na primeira vez
~/GuitarHero/scripts/build-jogo-mac.sh
```

Confere os pré-requisitos, restaura o NuGet se faltar, compila em modo batch e gera `_builds/YARG.app` (universal), com o log em `_builds/build.log`. A licença vem do login feito no Hub.

**Assinatura:** o build do Unity sai com assinatura ad-hoc, que muda a cada compilação. O macOS guarda as permissões (o jogo pede o **microfone** ao abrir) presas à assinatura, então a cada build ele perguntaria de novo, e o jogo **congela na tela de carregamento** até a resposta (a janela fica atrás do jogo em tela cheia e expira sozinha em 5 min). O `assinatura-mac.sh` cria um certificado local autoassinado, num chaveiro próprio (`~/Library/Keychains/yarg-assinatura.keychain-db`, senha aleatória em `_tools/assinatura/`), e o script de build assina o app com ele: a permissão respondida uma vez vale para todos os builds.

## 4. Músicas

As músicas **não estão neste repositório** (público): são faixas comerciais. Ficam no repositório **privado** `codingfoxxx/guitarhero-musicas`:

```bash
git clone https://github.com/codingfoxxx/guitarhero-musicas.git ~/YARG/songs
```

No jogo, *Configurações → Músicas*, adicionar a pasta e escanear. Com *Escanear Tudo ao Iniciar* ligado, pastas novas aparecem sozinhas ao abrir.

## 5. Abrir em português

O idioma só é escolhido pelo argumento `-lang`:

```bash
open -a ~/GuitarHero/_builds/YARG.app --args -lang pt-BR
```

O atalho `/Applications/Guitar Hero.app` (um applet do AppleScript com esse comando) faz isso.

## 6. Onde ficam os dados

`~/Library/Application Support/YARC/YARG/release/` (configurações, perfis, mapeamentos, recordes em `scores/`, cache de músicas). Log do Unity em `~/Library/Logs/YARC/YARG/Player.log`. Para trazer o progresso do Windows, copie `profiles/` e `scores/` de `%USERPROFILE%\AppData\LocalLow\YARC\YARG\release\` para cá, com o jogo fechado.

## 7. Controle

Pareie um controle de Xbox (ou PlayStation) por Bluetooth ou cabo; o fork o vincula sozinho a um perfil de 5 trastes com *AllTaps*. O mapeamento dos botões está em `COMO-JOGAR.md`.

## Se o jogo travar na tela de carregamento

- Pedido de permissão escondido atrás do jogo: aperte Cmd+Tab ou saia da tela cheia e responda (Permitir ou Não permitir, tanto faz para guitarra). Só deve aparecer na primeira abertura depois de criar o certificado.
- Conferir no log do sistema: `/usr/bin/log show --last 10m --predicate 'process == "tccd"' | grep -i microphone`.

## Avisos conhecidos no log

- `libVLCUnityPlugin.dylib ... Library not loaded: @rpath/libvlc.dylib`: a libvlc não vem no projeto. Vídeos de fundo caem no player de vídeo do Unity; não afeta músicas sem vídeo.
- `catalog_0.1.0.json` de `yarg-assets-release.ulna.net`: o servidor de cenários extras do upstream ainda não existe para builds "release". Os cenários que vêm no jogo funcionam.
