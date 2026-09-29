@echo off
rem Arraste um arquivo de audio (mp3, ogg, wav, flac, m4a...) em cima deste arquivo.
if "%~1"=="" (
  echo Arraste um arquivo de audio em cima deste .bat para gerar a musica.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0gerar-musica.ps1" "%~1"
pause
