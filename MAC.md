# Jogar no Mac

O executável de `_builds/` é só de Windows. No Mac o jogo precisa ser compilado a partir do fork. **Este caminho ainda não foi testado num Mac.**

## 1. Baixar o código

```bash
git clone --recurse-submodules https://github.com/codingfoxxx/yarg-autochart.git GuitarHero
cd GuitarHero/YARG
git checkout pessoal
git submodule update --init --recursive
```

O fork do jogo fica na branch `pessoal` do submódulo `YARG` (inclui o suporte a controle de Xbox).

## 2. Compilar

1. Instalar o Unity Hub e o editor **6000.3.5f2** (versão exigida), com o módulo *Mac Build Support*.
2. No Hub, abrir a pasta `GuitarHero/YARG` como projeto (a primeira importação demora).
3. `File > Build Profiles`, escolher **macOS** e compilar.
4. Alternativa sem compilar: apertar *Play* dentro do editor.

Os detalhes do build (e do que é específico do Windows) estão em `YARG/BUILD.md`.

## 3. Músicas

As músicas **não estão no GitHub**: são faixas comerciais e os repositórios são públicos. Copie a pasta `songs/` do PC por AirDrop, pendrive ou nuvem e, no jogo, aponte a pasta em *Settings > Songs* e escaneie.

Cada música é uma pasta com `song.ini`, `notes.chart` ou `notes.mid` e o áudio (`.ogg`/`.opus`/`.mp3`).

## 4. Controle

Plugue um controle de Xbox (ou PlayStation); o fork o vincula sozinho a um perfil de 5 trastes com *AllTaps*. O mapeamento dos botões está em `COMO-JOGAR.md`.
