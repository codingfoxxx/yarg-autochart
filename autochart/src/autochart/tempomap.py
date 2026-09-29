"""Mapa de tempo: batidas detectadas → eventos de BPM e de fórmula de compasso, em ticks.

O .chart guarda o BPM como inteiro em milésimos (``B 120000``). Aqui o mapa já é montado com
esses valores arredondados e o tempo de cada tick é calculado exatamente como o YARG calcula
(soma de trechos de tempo constante), para que as notas caiam onde previmos.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass, field

import numpy as np

from . import RESOLUTION


@dataclass(frozen=True)
class TempoEvent:
    tick: int
    millibpm: int  # BPM × 1000, como no .chart

    @property
    def bpm(self) -> float:
        return self.millibpm / 1000.0


@dataclass(frozen=True)
class TimeSignature:
    tick: int
    numerator: int
    denominator: int = 4


@dataclass
class GridReport:
    """Qualidade do encaixe do grid nas batidas detectadas (para o relatório)."""
    beat_errors_ms: list[float] = field(default_factory=list)
    tempo_changes: int = 0
    lead_in_beats: int = 0
    pickup_beats: int = 0
    meter_changes: int = 0

    @property
    def median_error_ms(self) -> float:
        return float(np.median(np.abs(self.beat_errors_ms))) if self.beat_errors_ms else 0.0

    @property
    def p95_error_ms(self) -> float:
        return float(np.percentile(np.abs(self.beat_errors_ms), 95)) if self.beat_errors_ms else 0.0


class TempoMap:
    def __init__(self, tempos: list[TempoEvent], timesigs: list[TimeSignature], resolution: int = RESOLUTION):
        if not tempos or tempos[0].tick != 0:
            raise ValueError("o mapa de tempo precisa de um BPM no tick 0")
        if any(t.millibpm <= 0 for t in tempos):
            raise ValueError("BPM tem que ser positivo")
        if any(b.tick <= a.tick for a, b in zip(tempos, tempos[1:])):
            raise ValueError("eventos de tempo fora de ordem ou repetidos")
        if not timesigs or timesigs[0].tick != 0:
            raise ValueError("o mapa precisa de uma fórmula de compasso no tick 0")
        self.resolution = resolution
        self.tempos = list(tempos)
        self.timesigs = list(timesigs)
        self._ticks = [t.tick for t in self.tempos]
        self._starts = [0.0]
        for a, b in zip(self.tempos, self.tempos[1:]):
            self._starts.append(self._starts[-1] + (b.tick - a.tick) / resolution * 60.0 / a.bpm)

    # ------------------------------------------------------------------ conversões
    def tick_to_time(self, tick: float) -> float:
        i = max(0, bisect.bisect_right(self._ticks, tick) - 1)
        t = self.tempos[i]
        return self._starts[i] + (tick - t.tick) / self.resolution * 60.0 / t.bpm

    def time_to_tick(self, time: float) -> float:
        """Tick fracionário correspondente a um tempo (s)."""
        i = max(0, bisect.bisect_right(self._starts, time) - 1)
        t = self.tempos[i]
        return t.tick + (time - self._starts[i]) * t.bpm / 60.0 * self.resolution

    def bpm_at_tick(self, tick: float) -> float:
        i = max(0, bisect.bisect_right(self._ticks, tick) - 1)
        return self.tempos[i].bpm

    def seconds_per_beat_at(self, tick: float) -> float:
        return 60.0 / self.bpm_at_tick(tick)

    def timesig_at(self, tick: float) -> TimeSignature:
        idx = max(0, bisect.bisect_right([s.tick for s in self.timesigs], tick) - 1)
        return self.timesigs[idx]

    def measure_starts(self, end_tick: int) -> list[int]:
        """Ticks de início de cada compasso até ``end_tick`` (respeita mudanças de compasso)."""
        starts: list[int] = []
        sigs = self.timesigs + [TimeSignature(end_tick + 1, 4)]
        for sig, nxt in zip(sigs, sigs[1:]):
            length = sig.numerator * self.resolution * 4 // sig.denominator
            tick = sig.tick
            while tick < nxt.tick and tick <= end_tick:
                starts.append(tick)
                tick += length
        return starts

    def beat_ticks(self, end_tick: int) -> list[int]:
        return list(range(0, end_tick + 1, self.resolution))


def _fit_ibi(beats: np.ndarray, start: int, end: int, anchor: float) -> float:
    """IBI (s) de mínimos quadrados com o início fixo em ``anchor`` (continuidade do grid)."""
    k = np.arange(1, end - start + 1, dtype=float)
    y = beats[start + 1:end + 1] - anchor
    return float(np.dot(k, y) / np.dot(k, k))


def _max_residual(beats: np.ndarray, start: int, end: int, anchor: float, ibi: float) -> float:
    k = np.arange(0, end - start + 1, dtype=float)
    return float(np.max(np.abs(beats[start:end + 1] - (anchor + k * ibi))))


def build_tempo_map(beats: np.ndarray, downbeats: np.ndarray | None = None, *, tolerance: float = 0.015,
                    min_segment_beats: int = 8, resolution: int = RESOLUTION) -> tuple[TempoMap, GridReport]:
    """Monta o mapa de tempo a partir das batidas (s) e dos tempos fortes (s).

    - Antes da primeira batida: ``k0`` batidas de "lead-in" no mesmo andamento inicial.
    - Depois: trechos de BPM constante, cada um o mais longo possível com todas as batidas a no
      máximo ``tolerance`` do grid; cada trecho começa exatamente onde o anterior termina.
    - Compasso: batidas entre tempos fortes; anacruse vira um primeiro compasso mais curto.
    """
    beats = np.asarray(beats, dtype=float)
    if len(beats) < 4:
        raise ValueError("batidas insuficientes para montar o mapa de tempo")
    report = GridReport()

    # Início e andamento do primeiro trecho por mínimos quadrados livres (não confia numa única
    # batida detectada, que tem ruído de alguns ms).
    m = min(len(beats), 16)
    design = np.vstack([np.ones(m), np.arange(m)]).T
    intercept, slope = np.linalg.lstsq(design, beats[:m], rcond=None)[0]
    b0, ibi0 = float(intercept), float(slope)
    if b0 < 0.2 or ibi0 <= 0:
        raise ValueError("a primeira batida precisa de pelo menos 0,2 s de áudio antes (use silêncio inicial)")
    k0 = max(1, int(round(b0 / ibi0)))
    report.lead_in_beats = k0

    tempos: list[TempoEvent] = []
    lead_millibpm = int(round(60.0 * k0 / b0 * 1000))
    tempos.append(TempoEvent(0, lead_millibpm))
    anchor = k0 * 60.0 / (lead_millibpm / 1000.0)  # tempo real do tick k0*res no mapa arredondado

    # Trechos de tempo constante (guloso, com continuidade).
    n = len(beats)
    start = 0
    segment_bpms: list[tuple[int, int]] = []  # (índice da batida inicial, millibpm)
    while start < n - 1:
        end = min(start + min_segment_beats, n - 1)
        ibi = _fit_ibi(beats, start, end, anchor)
        best_end, best_ibi = end, ibi
        while end < n - 1:
            cand = end + 1
            cand_ibi = _fit_ibi(beats, start, cand, anchor)
            if _max_residual(beats, start, cand, anchor, cand_ibi) > tolerance:
                break
            end, best_end, best_ibi = cand, cand, cand_ibi
        millibpm = int(round(60.0 / best_ibi * 1000))
        segment_bpms.append((start, millibpm))
        anchor += (best_end - start) * 60.0 / (millibpm / 1000.0)
        start = best_end

    for beat_index, millibpm in segment_bpms:
        tick = (k0 + beat_index) * resolution
        if tempos and tempos[-1].millibpm == millibpm:
            continue
        if tempos and tempos[-1].tick == tick:
            tempos[-1] = TempoEvent(tick, millibpm)
        else:
            tempos.append(TempoEvent(tick, millibpm))
    report.tempo_changes = len(tempos) - 1

    timesigs, pickup, meter_changes = _time_signatures(beats, downbeats, k0, resolution)
    report.pickup_beats = pickup
    report.meter_changes = meter_changes

    tmap = TempoMap(tempos, timesigs, resolution)
    report.beat_errors_ms = [
        (tmap.tick_to_time((k0 + i) * resolution) - float(b)) * 1000.0 for i, b in enumerate(beats)
    ]
    return tmap, report


def _time_signatures(beats: np.ndarray, downbeats: np.ndarray | None, k0: int,
                     resolution: int) -> tuple[list[TimeSignature], int, int]:
    """Fórmulas de compasso a partir dos tempos fortes; devolve (eventos, batidas de anacruse, mudanças)."""
    if downbeats is None or len(downbeats) < 2:
        return [TimeSignature(0, 4)], 0, 0

    ibi = float(np.median(np.diff(beats)))
    idx = []
    for d in downbeats:
        j = int(np.argmin(np.abs(beats - d)))
        if abs(beats[j] - d) <= 0.25 * ibi and (not idx or j > idx[-1]):
            idx.append(j)
    if len(idx) < 2:
        return [TimeSignature(0, 4)], 0, 0

    raw = [int(x) for x in np.diff(idx)]
    values, counts = np.unique(raw, return_counts=True)
    main = int(values[np.argmax(counts)])
    main = min(max(main, 2), 7)

    # Regulariza os compassos (sem mover tempos fortes, para o alinhamento valer por construção):
    # - múltiplo do compasso principal → vários compassos principais (tempo forte perdido);
    # - compasso de 1 batida → funde com o seguinte (tempo forte espúrio).
    bars: list[int] = []
    carry = 0
    for length in raw:
        length += carry
        carry = 0
        if length == 1:
            carry = 1
            continue
        if length % main == 0:
            bars.extend([main] * (length // main))
        else:
            bars.append(length)
    if carry and bars:
        bars[-1] += carry

    first = idx[0]
    pickup = k0 + first  # batidas desde o tick 0 até o primeiro tempo forte
    sigs: list[TimeSignature] = []
    remainder = pickup % main
    if remainder:
        sigs.append(TimeSignature(0, remainder))
        sigs.append(TimeSignature(remainder * resolution, main))
    else:
        sigs.append(TimeSignature(0, main))

    # Cada compasso começa onde o anterior termina; TS novo só quando o tamanho muda.
    changes = 0
    current = main
    beat = pickup
    for length in bars:
        if length != current:
            sigs.append(TimeSignature(beat * resolution, length))
            current = length
            changes += 1
        beat += length
    # Depois do último tempo forte detectado, volta ao compasso principal.
    if current != main:
        sigs.append(TimeSignature(beat * resolution, main))
    return _normalize_timesigs(sigs), int(remainder), changes


def _normalize_timesigs(sigs: list[TimeSignature]) -> list[TimeSignature]:
    """Um evento por tick (vale o último) e sem eventos que repetem a fórmula anterior."""
    by_tick: dict[int, TimeSignature] = {}
    for s in sigs:
        by_tick[s.tick] = s
    out: list[TimeSignature] = []
    for tick in sorted(by_tick):
        s = by_tick[tick]
        if out and (out[-1].numerator, out[-1].denominator) == (s.numerator, s.denominator):
            continue
        out.append(s)
    return out
