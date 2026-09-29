"""Escrita de notes.chart e song.ini no formato que o YARG (e o Moonscraper) leem.

Regras de formato seguidas (ver docs/pesquisa/formato-musica-yarg.md):
- ``[Song]`` é a primeira seção e ``[SyncTrack]`` a segunda; ``Resolution`` sem aspas.
- Linhas ordenadas por tick; notas sem sustain têm duração 0; acordes com durações iguais.
- HOPO natural do YARG no .chart: nota simples, anterior existe, (anterior é acorde ou traste
  diferente) e distância ≤ limiar (65 ticks em resolução 192). ``N 5`` inverte esse estado;
  ``N 6`` (tap) tem prioridade.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

from . import RESOLUTION
from .model import DIFFICULTIES, OPEN, SECTION_NAMES, Note, SongMeta
from .tempomap import TempoMap


def hopo_threshold(resolution: int = RESOLUTION) -> int:
    """Limiar padrão de HOPO do YARG para .chart: res//3 + floor(res/192) (65 em 192)."""
    return resolution // 3 + resolution // 192


def natural_hopo(prev: Note | None, cur: Note, threshold: int) -> bool:
    if cur.is_chord or prev is None:
        return False
    if not prev.is_chord and prev.lanes == cur.lanes:
        return False
    return cur.tick - prev.tick <= threshold


def final_types(notes: Sequence[Note], resolution: int = RESOLUTION) -> list[str]:
    """Tipo que o YARG vai mostrar para cada nota ('strum', 'hopo', 'tap'), dado o que será escrito."""
    thr = hopo_threshold(resolution)
    out = []
    prev = None
    for n in notes:
        if n.tap:
            out.append("tap")
        else:
            nat = natural_hopo(prev, n, thr)
            flip = _needs_flip(prev, n, thr)
            out.append("hopo" if nat != flip else "strum")
        prev = n
    return out


def _needs_flip(prev: Note | None, cur: Note, thr: int) -> bool:
    if cur.tap or cur.hopo is None:
        return False
    return natural_hopo(prev, cur, thr) != cur.hopo


def _escape(text: str) -> str:
    return text.replace('"', "'").replace("\r", " ").replace("\n", " ")


def render_chart(meta: SongMeta, tempo: TempoMap, difficulties: dict[str, list[Note]],
                 star_power: Iterable[tuple[int, int]] = (), sections: Iterable[tuple[int, str]] = (),
                 music_stream: str = "song.ogg", guitar_stream: str | None = None,
                 end_tick: int | None = None) -> str:
    res = tempo.resolution
    thr = hopo_threshold(res)
    lines: list[str] = ["[Song]", "{"]
    lines += [
        f'  Name = "{_escape(meta.name)}"',
        f'  Artist = "{_escape(meta.artist)}"',
        f'  Charter = "{_escape(meta.charter)}"',
        f'  Album = "{_escape(meta.album)}"',
        f'  Year = ", {_escape(meta.year)}"' if meta.year else '  Year = ""',
        "  Offset = 0",
        f"  Resolution = {res}",
        '  Player2 = bass',
        "  Difficulty = 0",
        "  PreviewStart = 0",
        "  PreviewEnd = 0",
        f'  Genre = "{_escape(meta.genre)}"',
        '  MediaType = "cd"',
        f'  MusicStream = "{music_stream}"',
    ]
    if guitar_stream:
        lines.append(f'  GuitarStream = "{guitar_stream}"')
    lines += ["}", "[SyncTrack]", "{"]
    sync: list[tuple[int, int, str]] = []
    for ts in tempo.timesigs:
        exp = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4}[ts.denominator]
        sync.append((ts.tick, 0, f"TS {ts.numerator}" + ("" if exp == 2 else f" {exp}")))
    for t in tempo.tempos:
        sync.append((t.tick, 1, f"B {t.millibpm}"))
    for tick, _, text in sorted(sync):
        lines.append(f"  {tick} = {text}")
    lines += ["}", "[Events]", "{"]
    ev = [(tick, f'E "section {_escape(name)}"') for tick, name in sections]
    if end_tick is not None:
        ev.append((end_tick, 'E "end"'))
    for tick, text in sorted(ev):
        lines.append(f"  {tick} = {text}")
    lines.append("}")

    sp = sorted(star_power)
    for diff in DIFFICULTIES:
        notes = difficulties.get(diff)
        if not notes:
            continue
        lines += [f"[{SECTION_NAMES[diff]}]", "{"]
        body: list[tuple[int, int, str]] = []
        prev = None
        for n in notes:
            for lane in sorted(n.lanes):
                body.append((n.tick, 0, f"N {lane} {n.length}"))
            if n.tap:
                body.append((n.tick, 1, "N 6 0"))
            elif _needs_flip(prev, n, thr):
                body.append((n.tick, 1, "N 5 0"))
            prev = n
        for start, length in sp:
            body.append((start, 2, f"S 2 {length}"))
        for tick, _, text in sorted(body):
            lines.append(f"  {tick} = {text}")
        lines.append("}")
    return "\r\n".join(lines) + "\r\n"


def render_song_ini(meta: SongMeta) -> str:
    fields = [
        ("name", meta.name), ("artist", meta.artist), ("album", meta.album), ("genre", meta.genre),
        ("year", meta.year), ("charter", meta.charter), ("song_length", str(meta.song_length_ms)),
        ("preview_start_time", str(meta.preview_start_ms)), ("diff_guitar", str(meta.diff_guitar)),
        ("delay", "0"), ("loading_phrase", meta.loading_phrase),
    ]
    fields += list(meta.extra.items())
    out = ["[song]"]
    for key, value in fields:
        value = str(value).replace("\r", " ").replace("\n", " ").strip()
        out.append(f"{key} = {value}")
    return "\r\n".join(out) + "\r\n"


def write_song_folder(folder: Path, meta: SongMeta, chart_text: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "notes.chart").write_text(chart_text, encoding="utf-8", newline="")
    (folder / "song.ini").write_text(render_song_ini(meta), encoding="utf-8", newline="")


def validate_notes(notes: Sequence[Note]) -> list[str]:
    """Checagens de formato que fariam o YARG rejeitar ou interpretar diferente."""
    problems: list[str] = []
    prev_tick = -1
    for i, n in enumerate(notes):
        if n.tick < 0:
            problems.append(f"nota {i}: tick negativo")
        if n.tick <= prev_tick:
            problems.append(f"nota {i}: tick {n.tick} não é maior que o anterior ({prev_tick})")
        if not n.lanes or any(l not in (0, 1, 2, 3, 4, OPEN) for l in n.lanes):
            problems.append(f"nota {i}: trastes inválidos {n.lanes}")
        if OPEN in n.lanes and len(n.lanes) > 1:
            problems.append(f"nota {i}: nota aberta em acorde")
        if len(set(n.lanes)) != len(n.lanes):
            problems.append(f"nota {i}: traste repetido")
        if n.length < 0:
            problems.append(f"nota {i}: sustain negativo")
        if i + 1 < len(notes) and n.length and n.tick + n.length > notes[i + 1].tick:
            problems.append(f"nota {i}: sustain atravessa a próxima nota")
        prev_tick = n.tick
    return problems
