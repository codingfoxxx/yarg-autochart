"""Linha de comando: ``python -m autochart gerar <áudio> [opções]``."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .model import DIFFICULTIES, SongMeta


def _default_output() -> Path:
    env = os.environ.get("AUTOCHART_SAIDA")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3] / "songs"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autochart", description="Gera charts de guitarra (YARG) a partir de áudio.")
    sub = p.add_subparsers(dest="comando", required=True)

    g = sub.add_parser("gerar", help="gera uma pasta de música a partir de um arquivo de áudio")
    g.add_argument("audio", type=Path, help="arquivo de áudio (mp3, ogg, wav, flac, m4a…)")
    g.add_argument("--titulo", help="nome da música (padrão: nome do arquivo)")
    g.add_argument("--artista", default="Desconhecido")
    g.add_argument("--album", default="")
    g.add_argument("--ano", default="")
    g.add_argument("--genero", default="")
    g.add_argument("--saida", type=Path, default=None,
                   help="pasta onde criar a música (padrão: AUTOCHART_SAIDA ou ./songs)")
    g.add_argument("--fonte", choices=["guitarra", "outros", "baixo", "mix"], default="guitarra",
                   help="de onde tirar as notas (padrão: stem de guitarra separado pelo Demucs)")
    g.add_argument("--densidade", type=float, default=1.0, help="0.5 a 1.5; menor = menos notas no Expert")
    g.add_argument("--sensibilidade", type=float, default=0.5, help="0 a 1; maior = detecta mais ataques")
    g.add_argument("--sem-stems", action="store_true", help="grava só song.ogg (sem guitar.ogg separado)")
    g.add_argument("--dispositivo", default="cpu", help="cpu (padrão) ou cuda")
    g.add_argument("--dificuldades", default=",".join(DIFFICULTIES), help="lista separada por vírgula")
    g.add_argument("--sem-validacao", action="store_true",
                   help="não roda o validador do YARG.Core no fim (mais rápido)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.comando == "gerar":
        from .pipeline import Options, generate
        if not args.audio.is_file():
            print(f"Arquivo não encontrado: {args.audio}", file=sys.stderr)
            return 2
        diffs = tuple(d.strip().capitalize() for d in args.dificuldades.split(",") if d.strip())
        unknown = [d for d in diffs if d not in DIFFICULTIES]
        if unknown:
            print(f"Dificuldade desconhecida: {', '.join(unknown)}", file=sys.stderr)
            return 2
        meta = SongMeta(name=args.titulo or args.audio.stem, artist=args.artista, album=args.album,
                        year=args.ano, genre=args.genero, charter="autochart (gerado automaticamente)",
                        loading_phrase="Chart gerado automaticamente pelo autochart. Revise no Moonscraper se quiser.")
        opts = Options(fonte=args.fonte, densidade=args.densidade, sensibilidade=args.sensibilidade,
                       stems=not args.sem_stems, dispositivo=args.dispositivo, dificuldades=diffs,
                       validar=not args.sem_validacao)
        result = generate(args.audio, args.saida or _default_output(), meta, opts)
        return 1 if result.report.get("violacoes") else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
