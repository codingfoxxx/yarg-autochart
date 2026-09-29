# Verificação de compilação do fork sem o editor do Unity

Com o **Smart App Control** do Windows 11 ligado, o editor do Unity 6 não consegue compilar: o
pipeline dele roda ferramentas .NET sem assinatura (`ApiUpdater.MovedFromExtractor.dll` e outras)
que o Windows bloqueia (detalhes no `SECURITY_LOG.md`). O compilador C# que o Unity usa (Roslyn,
do SDK .NET embutido no editor) é assinado pela Microsoft e roda normalmente.

Estes scripts reaproveitam o **grafo de build que o editor grava antes de falhar**
(`Library/Bee/*.dag.json`, com a linha de comando exata de cada compilação) e executam só as
etapas "Csc", na ordem das dependências. Resultado: os mesmos erros de C# que o editor mostraria.

## Uso

Uma vez (cria a cópia só-de-scripts e o grafo; ~4 min):

1. Copiar `Assets/{Script,Plugins,Editor,VLCUnity}`, `packages.config`, `NuGet.config`,
   `ProjectSettings`, `Packages/manifest.json` e `packages-lock.json` do fork, e o
   `YARG.Core/YARG.Core`, para `_work/unity-compilecheck` (o PROGRESS.md registra o comando).
2. Abrir essa cópia com o Unity em modo batch (`Unity.exe -batchmode -nographics -quit -projectPath …`).
   Ele falha por causa do Smart App Control, mas deixa o grafo pronto.
3. Restaurar os pacotes NuGet do `packages.config` (`dotnet restore` de um projeto com as mesmas
   versões) para `_work/unity-compilecheck/Assets/Packages`, como o NuGetForUnity faria.
4. `python tools/unity-compile-check/preparar_copia.py` (referências do NuGet e remendos de versão).

Depois, a cada mudança no fork:

```
.venv\Scripts\python.exe tools\unity-compile-check\compilar.py --sincronizar-de YARG
```

Sai com código 0 se tudo compilou. Leva ~3 s por rodada (só recompila o que mudou).

## Limitações (importante)

- Usa o Unity **instalado** (6000.6.3f1), não o do projeto (6000.3.5f2). O 6000.6 troca algumas
  versões de pacote (Cinemachine 2.10 → 6.6, Input System 1.17 → 1.20) e transforma algumas APIs
  obsoletas em erro. `preparar_copia.py` remenda **só na cópia** esses pontos (VRM10, SoftMask, e
  dois arquivos do jogo) para a referência ficar limpa: 116 assemblies, 0 erros. Um erro que aparecer
  depois disso é da mudança feita no fork.
- Só compila. Não roda ILPostProcessing, não importa assets, não gera build.
- Os geradores de código do Unity que o Windows bloqueia (UIToolkit, IlInterpreter) não rodam; o
  código do YARG compila sem eles.
