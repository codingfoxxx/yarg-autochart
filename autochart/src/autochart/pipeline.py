"""Pipeline completo: áudio → pasta de música pronta para o YARG."""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata as md
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from . import RESOLUTION, __version__, analysis, audio
from .chart import render_chart, validate_notes, write_song_folder
from .difficulty import build_difficulties
from .events import build_events, fill_missing_pitch, make_bleed_ratio
from .model import DIFFICULTIES, SongMeta
from .quantize import quantize
from .report import (alignment_metrics, difficulty_stats, estimate_diff_guitar, playability_violations,
                     write_report)
from .sections import detect_sections
from .starpower import place_star_power
from .tempomap import build_tempo_map
from .validate import validate_with_yarg

SOURCES = ("guitarra", "outros", "baixo", "mix")
_STEM_OF = {"guitarra": "guitar", "outros": "other", "baixo": "bass"}
MIN_BEATS = 8  # abaixo disso não dá para montar um mapa de tempo confiável


class SemRitmoError(ValueError):
    """O áudio não tem batidas suficientes para gerar um chart."""


@dataclass
class Options:
    fonte: str = "guitarra"            # de onde vêm as notas: stem de guitarra, "outros", baixo ou mix
    densidade: float = 1.0             # < 1 = menos notas no Expert
    sensibilidade: float = 0.5         # detecção de ataques (0..1)
    stems: bool = True                 # grava guitar.ogg separado (o jogo abafa a guitarra no erro)
    dispositivo: str = "cpu"
    dificuldades: tuple[str, ...] = DIFFICULTIES
    silencio_inicial_min: float = 1.5  # garante pelo menos isso antes da 1ª batida
    validar: bool = True               # roda o validador do YARG.Core no fim
    tolerancia_grid: float = 0.008     # s, na média móvel dos resíduos; ver tempomap.build_tempo_map


@dataclass
class Result:
    folder: Path
    report: dict = field(default_factory=dict)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


_CACHED_STEMS = ("guitar", "other", "bass", "piano", "vocals")


def _stem_cache_dir(sha: str, pad: float) -> Path:
    root = Path(__file__).resolve().parents[3] / "_cache" / "stems"
    return root / f"{sha[:16]}-pad{int(round(pad * 1000))}"


def _cached_stems(sha: str, pad: float, n: int) -> dict[str, np.ndarray] | None:
    """Stems já separados deste mesmo áudio (mesmo SHA-256 e mesmo silêncio inicial)."""
    import soundfile as sf
    folder = _stem_cache_dir(sha, pad)
    if not all((folder / f"{s}.flac").is_file() for s in _CACHED_STEMS):
        return None
    out = {}
    for s in _CACHED_STEMS:
        data, _ = sf.read(str(folder / f"{s}.flac"), dtype="float32", always_2d=True)
        if len(data) != n:
            return None
        out[s] = data
    return out


def _store_stems(sha: str, pad: float, stems: dict[str, np.ndarray]) -> None:
    import soundfile as sf
    folder = _stem_cache_dir(sha, pad)
    folder.mkdir(parents=True, exist_ok=True)
    for s in _CACHED_STEMS:
        if s in stems:
            sf.write(str(folder / f"{s}.flac"), np.clip(stems[s], -1, 1), audio.SAMPLE_RATE, subtype="PCM_24")


def _safe_name(text: str) -> str:
    bad = '<>:"/\\|?*'
    out = "".join("_" if c in bad or ord(c) < 32 else c for c in text).strip().rstrip(".")
    return out or "musica"


def generate(audio_path: Path, output_root: Path, meta: SongMeta, opts: Options,
             log: Callable[[str], None] = print) -> Result:
    if opts.fonte not in SOURCES:
        raise ValueError(f"fonte inválida: {opts.fonte} (use {', '.join(SOURCES)})")
    t_total = time.time()
    timings: dict[str, float] = {}

    def step(name: str, t0: float) -> None:
        timings[name] = round(time.time() - t0, 1)
        log(f"  {name}: {timings[name]} s")

    folder = output_root / _safe_name(f"{meta.artist} - {meta.name}")
    log(f"Gerando '{meta.artist} - {meta.name}' em {folder}")

    t0 = time.time()
    mix = audio.decode(audio_path)
    step("decodificação", t0)

    t0 = time.time()
    beats = analysis.track_beats(mix, device=opts.dispositivo)
    step("batidas (Beat This!)", t0)
    if len(beats.beats) < MIN_BEATS:
        raise SemRitmoError(
            f"só {len(beats.beats)} batida(s) encontrada(s) no áudio; é preciso pelo menos {MIN_BEATS}. "
            "O arquivo parece não ter um pulso rítmico claro (ruído, fala, ambiente) ou é curto demais.")

    # Silêncio inicial: dá tempo de leitura e garante que o mapa de tempo comece antes da 1ª batida.
    pad = max(0.0, round(opts.silencio_inicial_min - float(beats.beats[0]), 2))
    if pad > 0:
        mix = audio.pad_start(mix, pad)
        beats.beats = beats.beats + pad
        beats.downbeats = beats.downbeats + pad
    # Fase do grid: batidas costumam coincidir com ataques de bateria no mix. Se as batidas
    # detectadas estão sistematicamente adiantadas/atrasadas em relação aos ataques, corrige.
    t0 = time.time()
    mix_onsets = analysis.detect_onsets(mix, sensitivity=0.5)
    phase, phase_support = analysis.phase_offset(beats.beats, mix_onsets.times)
    if abs(phase) >= 0.002:
        beats.beats = beats.beats + phase
        beats.downbeats = beats.downbeats + phase
    step("fase do grid", t0)
    tempo, grid = build_tempo_map(beats.beats, beats.downbeats, tolerance=opts.tolerancia_grid)

    stems: dict[str, np.ndarray] = {}
    source_signal = mix
    source_used = "mix"
    input_sha = _sha256(audio_path)
    if opts.fonte != "mix" or opts.stems:
        t0 = time.time()
        stems = _cached_stems(input_sha, pad, len(mix))
        if stems is None:
            stems = analysis.separate(mix, device=opts.dispositivo)
            _store_stems(input_sha, pad, stems)
            step("separação (Demucs htdemucs_6s)", t0)
        else:
            step("separação (cache)", t0)
    if opts.fonte != "mix":
        wanted = stems[_STEM_OF[opts.fonte]]
        if audio.rms_db(wanted) < audio.rms_db(mix) - 24.0:
            fallback = stems["other"] if opts.fonte == "guitarra" else mix
            log(f"  aviso: o stem '{opts.fonte}' está quase mudo; usando {'outros' if opts.fonte == 'guitarra' else 'mix'}")
            source_signal = fallback
            source_used = "outros" if opts.fonte == "guitarra" else "mix"
        else:
            source_signal = wanted
            source_used = opts.fonte

    t0 = time.time()
    onsets = analysis.detect_onsets(source_signal, sensitivity=opts.sensibilidade)
    step("ataques (onsets)", t0)
    t0 = time.time()
    pitch_notes = analysis.transcribe(source_signal)
    step("alturas (Basic Pitch)", t0)

    bleed = None
    if source_used != "mix" and stems:
        others = [stems[s] for s in ("other", "piano", "vocals") if s in stems and s != _STEM_OF.get(source_used)]
        bleed = make_bleed_ratio(source_signal, others, audio.SAMPLE_RATE)
    events = build_events(onsets, pitch_notes, bleed_ratio=bleed)
    rejected_bleed = getattr(build_events, "rejected_bleed", 0)
    pitched = fill_missing_pitch(events)
    quantized, rhythm = quantize(events, tempo)
    log(f"  ritmo: {rhythm.describe()}")
    q_errors = np.array([abs(q.error_ms) for q in quantized]) if quantized else np.array([0.0])

    t0 = time.time()
    diffs, consistency = build_difficulties(quantized, tempo, density=opts.densidade, difficulties=opts.dificuldades)
    expert = diffs.get("Expert") or next(iter(diffs.values()))
    first_tick = expert[0].tick if expert else 0
    end_tick = max((n.tick + n.length for v in diffs.values() for n in v), default=0)
    sections = detect_sections(mix, audio.SAMPLE_RATE, tempo, first_tick, end_tick + RESOLUTION)
    star_power = place_star_power(diffs, tempo, section_ticks=[t for t, _ in sections])
    step("chart (dificuldades, star power, seções)", t0)

    # Áudio do jogo: com stems, guitar.ogg + song.ogg (= mix − guitarra) somam exatamente o original.
    t0 = time.time()
    folder.mkdir(parents=True, exist_ok=True)
    guitar_stream = None
    if opts.stems and "guitar" in stems:
        audio.encode_ogg(stems["guitar"], folder / "guitar.ogg")
        audio.encode_ogg(mix - stems["guitar"], folder / "song.ogg")
        guitar_stream = "guitar.ogg"
    else:
        audio.encode_ogg(mix, folder / "song.ogg")
    step("áudio (ogg)", t0)

    duration_ms = int(round(len(mix) / audio.SAMPLE_RATE * 1000))
    stats = {name: difficulty_stats(diffs.get(name, []), tempo) for name in DIFFICULTIES if name in diffs}
    for name, value in consistency.items():
        stats[name]["consistencia_riffs_pct"] = round(100 * value, 1)
    meta.song_length_ms = duration_ms
    meta.diff_guitar = estimate_diff_guitar(stats.get("Expert", {}))
    if meta.preview_start_ms < 0 and len(sections) > 1:
        meta.preview_start_ms = int(tempo.tick_to_time(sections[1][0]) * 1000)

    chart_text = render_chart(meta, tempo, diffs, star_power, sections, guitar_stream=guitar_stream)
    write_song_folder(folder, meta, chart_text)

    violations: list[str] = []
    for name, notes in diffs.items():
        violations += [f"{name}: {p}" for p in validate_notes(notes)]
        violations += playability_violations(name, notes, tempo, star_power)

    yarg_check = None
    if opts.validar:
        t0 = time.time()
        yarg_check = validate_with_yarg(folder, diffs, tempo.resolution)
        step("validação no YARG.Core", t0)
        if yarg_check is None:
            log("  aviso: validador do YARG.Core indisponível (precisa do .NET SDK e de tools/validator)")
        elif yarg_check.get("ok") is None:
            log("  aviso: validação no YARG.Core não executada: " + yarg_check.get("indisponivel", ""))
        elif not yarg_check.get("ok"):
            violations.append("validação no YARG.Core: " + (yarg_check.get("erro") or "falhou (ver validacao-yarg.json)"))
    nps = [stats[d]["nps_media"] for d in ("Easy", "Medium", "Hard", "Expert") if d in stats and stats[d].get("notas")]
    bpms = [t.bpm for t in tempo.tempos[1:]] or [tempo.tempos[0].bpm]

    data = {
        "versao": __version__,
        "gerado_em": dt.datetime.now().isoformat(timespec="seconds"),
        "tempo_total_s": round(time.time() - t_total, 1),
        "musica": {"titulo": meta.name, "artista": meta.artist, "album": meta.album, "ano": meta.year,
                   "genero": meta.genre, "diff_guitar": meta.diff_guitar},
        "entrada": {"arquivo": audio_path.name, "sha256": input_sha,
                    "duracao_s": round(duration_ms / 1000 - pad, 2)},
        "parametros": {**asdict(opts), "fonte_usada": source_used},
        "grid": {
            "bpm_min": round(min(bpms), 2), "bpm_max": round(max(bpms), 2),
            "bpm_mediana": round(float(np.median(bpms)), 2),
            "mudancas_de_tempo": grid.tempo_changes, "compasso": f"{tempo.timesigs[-1].numerator}/4",
            "anacruse": grid.pickup_beats, "mudancas_de_compasso": grid.meter_changes,
            "erro_batida_mediana_ms": round(grid.median_error_ms, 1),
            "erro_batida_p95_ms": round(grid.p95_error_ms, 1),
            "silencio_inicial_s": pad, "avisos": beats.notes,
            "correcao_de_fase_ms": round(phase * 1000, 1) if abs(phase) >= 0.002 else 0.0,
            "batidas_com_ataque_pct": round(100 * phase_support, 1),
        },
        "analise": {"ataques": int(len(onsets.times)), "notas_transcritas": len(pitch_notes),
                    "eventos": len(events), "altura_detectada_pct": round(100 * pitched, 1),
                    "descartados_por_vazamento": int(rejected_bleed),
                    "quantizacao_erro_mediano_ms": round(float(np.median(q_errors)), 1),
                    "quantizacao_erro_p95_ms": round(float(np.percentile(q_errors, 95)), 1),
                    "ritmo": rhythm.describe(),
                    "evidencia_subdivisoes_pct": {str(k): round(100 * v, 1) for k, v in rhythm.evidence.items()}},
        "alinhamento": alignment_metrics(expert, tempo, [q.event for q in quantized], onsets.times,
                                         onsets.strengths) if expert else {},
        "dificuldades": stats,
        "violacoes": violations,
        "validacao_yarg": yarg_check,
        "densidade_monotonica": all(a < b for a, b in zip(nps, nps[1:])),
        "star_power": star_power,
        "secoes": sections,
        "tempos_s": timings,
        "versoes": {p: md.version(p) for p in ("torch", "beat-this", "demucs", "librosa", "basic-pitch", "numpy")},
    }
    write_report(folder, data)
    log(f"Pronto em {data['tempo_total_s']} s: {folder}")
    if violations:
        log(f"  ATENÇÃO: {len(violations)} violação(ões) de jogabilidade (ver relatorio.md)")
    return Result(folder, data)
