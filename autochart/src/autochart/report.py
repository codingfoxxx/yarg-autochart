"""Métricas objetivas de qualidade, checagens de jogabilidade e o relatório por música."""
from __future__ import annotations

import bisect
import json
from pathlib import Path

import numpy as np

from .chart import final_types
from .difficulty import PROFILES, min_gap
from .model import OPEN, Note
from .tempomap import GridReport, TempoMap


def difficulty_stats(notes: list[Note], tempo: TempoMap) -> dict:
    if not notes:
        return {"notas": 0}
    types = final_types(notes, tempo.resolution)
    times = np.array([tempo.tick_to_time(n.tick) for n in notes])
    span = max(times[-1] - times[0], 1e-6)
    peak = 0.0
    for i, t in enumerate(times):
        j = bisect.bisect_right(times, t + 2.0)
        peak = max(peak, (j - i) / 2.0)
    lanes = [l for n in notes for l in n.lanes]
    return {
        "notas": len(notes),
        "nps_media": round(len(notes) / span, 2),
        "nps_pico_2s": round(peak, 2),
        "acordes_pct": round(100 * sum(n.is_chord for n in notes) / len(notes), 1),
        "sustains_pct": round(100 * sum(n.length > 0 for n in notes) / len(notes), 1),
        "hopo_pct": round(100 * types.count("hopo") / len(notes), 1),
        "tap_pct": round(100 * types.count("tap") / len(notes), 1),
        "trastes": {name: lanes.count(i) for i, name in enumerate(["verde", "vermelho", "amarelo", "azul", "laranja"])},
    }


def playability_violations(name: str, notes: list[Note], tempo: TempoMap, star_power: list[tuple[int, int]]) -> list[str]:
    prof = PROFILES[name]
    res = tempo.resolution
    out: list[str] = []
    types = final_types(notes, res)
    for k, n in enumerate(notes):
        where = f"{name} tick {n.tick}"
        if any(l != OPEN and l >= prof.n_lanes for l in n.lanes):
            out.append(f"{where}: traste fora dos {prof.n_lanes} permitidos {n.lanes}")
        if len(n.lanes) > prof.max_chord:
            out.append(f"{where}: acorde de {len(n.lanes)} notas (máx. {prof.max_chord})")
        if n.is_chord and (min(n.lanes), max(n.lanes)) in prof.forbidden_pairs:
            out.append(f"{where}: formato de acorde proibido {n.lanes}")
        if k:
            prev = notes[k - 1]
            gap_s = tempo.tick_to_time(n.tick) - tempo.tick_to_time(prev.tick)
            need = max(min_gap(prof, tempo, prev.tick), min_gap(prof, tempo, n.tick))
            if gap_s < need * 0.98:
                out.append(f"{where}: {gap_s * 1000:.0f} ms da nota anterior (mín. {need * 1000:.0f} ms)")
            if prev.length and prev.tick + prev.length > n.tick:
                out.append(f"{where}: sustain anterior atravessa esta nota")
            if types[k] == "hopo" and not prev.is_chord and prev.lanes == n.lanes:
                out.append(f"{where}: HOPO no mesmo traste da nota anterior (impossível)")
        if not prof.hopos and types[k] != "strum":
            out.append(f"{where}: {types[k]} numa dificuldade só de palhetada")
    ticks = [n.tick for n in notes]
    for start, length in star_power:
        if bisect.bisect_left(ticks, start + length) - bisect.bisect_left(ticks, start) == 0:
            out.append(f"{name}: frase de star power em {start} sem notas")
    return out


def alignment_metrics(notes: list[Note], tempo: TempoMap, events: list, onset_times: np.ndarray,
                      onset_strengths: np.ndarray) -> dict:
    """Quão perto do áudio as notas do chart ficaram.

    - nota → evento de origem (o ataque detectado ou o início da nota transcrita): erro que a
      quantização e o grid introduzem, para todas as notas;
    - nota → ataque detectado mais próximo: só para notas que vieram de ataques;
    - cobertura: fração dos ataques fortes do áudio que viraram nota.
    """
    if not notes:
        return {}
    note_times = np.array([tempo.tick_to_time(n.tick) for n in notes])
    src = [events[n.source_index] for n in notes]
    to_event = np.abs(note_times - np.array([e.time for e in src])) * 1000.0
    from_onset = np.array([e.from_onset for e in src])
    out = {
        "nota_ao_evento_mediana_ms": round(float(np.median(to_event)), 1),
        "nota_ao_evento_p95_ms": round(float(np.percentile(to_event, 95)), 1),
        "notas_ate_25ms_pct": round(float(np.mean(to_event <= 25) * 100), 1),
        "notas_ate_50ms_pct": round(float(np.mean(to_event <= 50) * 100), 1),
        "notas_so_da_transcricao_pct": round(float(np.mean(~from_onset) * 100), 1),
    }
    if len(onset_times) and from_onset.any():
        nt = note_times[from_onset]
        idx = np.clip(np.searchsorted(onset_times, nt), 1, len(onset_times) - 1)
        d = np.minimum(np.abs(onset_times[idx] - nt), np.abs(onset_times[idx - 1] - nt)) * 1000.0
        out["nota_ao_ataque_mediana_ms"] = round(float(np.median(d)), 1)
        out["nota_ao_ataque_p95_ms"] = round(float(np.percentile(d, 95)), 1)
    strong = onset_times[onset_strengths >= 0.6]
    covered = 0
    for t in strong:
        j = int(np.searchsorted(note_times, t))
        near = [abs(note_times[x] - t) for x in (j - 1, j) if 0 <= x < len(note_times)]
        covered += bool(near) and min(near) <= 0.05
    out["ataques_fortes_cobertos_pct"] = round(100.0 * covered / len(strong), 1) if len(strong) else None
    return out


def estimate_diff_guitar(expert_stats: dict) -> int:
    peak = expert_stats.get("nps_pico_2s", 0)
    for level, limit in enumerate((3, 5, 7, 9, 11, 13)):
        if peak < limit:
            return level
    return 6


def write_report(folder: Path, data: dict) -> None:
    (folder / "autochart.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [f"# Relatório — {data['musica']['artista']} - {data['musica']['titulo']}", ""]
    lines.append(f"Gerado por autochart {data['versao']} em {data['gerado_em']} ({data['tempo_total_s']} s).")
    lines.append(f"Arquivo de origem: `{data['entrada']['arquivo']}` (SHA-256 `{data['entrada']['sha256'][:16]}…`), "
                 f"{data['entrada']['duracao_s']} s. Fonte do chart: **{data['parametros']['fonte']}**.")
    lines.append("")
    g = data["grid"]
    lines += ["## Tempo e grid", "",
              f"- BPM: {g['bpm_min']}–{g['bpm_max']} (mediana {g['bpm_mediana']}), {g['mudancas_de_tempo']} mudança(s) de tempo, "
              f"compasso {g['compasso']}{' com anacruse de ' + str(g['anacruse']) + ' batida(s)' if g['anacruse'] else ''}.",
              f"- Encaixe do grid nas batidas detectadas: mediana {g['erro_batida_mediana_ms']} ms, p95 {g['erro_batida_p95_ms']} ms.",
              f"- Silêncio inicial acrescentado: {g['silencio_inicial_s']} s.",
              f"- Correção de fase do grid (batida → ataque no mix): {g.get('correcao_de_fase_ms', 0)} ms "
              f"({g.get('batidas_com_ataque_pct', 0)}% das batidas com ataque a até 40 ms)."]
    for note in g.get("avisos", []):
        lines.append(f"- Aviso: {note}")
    a = data["alinhamento"]
    lines += ["", "## Alinhamento (Expert)", ""]
    if a:
        lines += [f"- Distância de cada nota ao evento de áudio que a originou: mediana {a['nota_ao_evento_mediana_ms']} ms, "
                  f"p95 {a['nota_ao_evento_p95_ms']} ms (até 25 ms: {a['notas_ate_25ms_pct']}%; até 50 ms: {a['notas_ate_50ms_pct']}%).",
                  f"- Notas vindas só da transcrição (ataque não detectado ou ligado): {a['notas_so_da_transcricao_pct']}%."]
        if "nota_ao_ataque_mediana_ms" in a:
            lines.append(f"- Notas vindas de ataques → ataque detectado mais próximo: mediana {a['nota_ao_ataque_mediana_ms']} ms, "
                         f"p95 {a['nota_ao_ataque_p95_ms']} ms.")
        lines.append(f"- Ataques fortes que viraram nota: {a['ataques_fortes_cobertos_pct']}%.")
    an = data["analise"]
    lines += [f"- Eventos com altura detectada: {an['altura_detectada_pct']}%. "
              f"Ataques detectados: {an['ataques']}; notas transcritas: {an['notas_transcritas']}; "
              f"descartados por vazamento de outros instrumentos: {an.get('descartados_por_vazamento', 0)}.",
              f"- Ritmo inferido: {an.get('ritmo', '?')}; erro de quantização mediano {an['quantizacao_erro_mediano_ms']} ms "
              f"(p95 {an['quantizacao_erro_p95_ms']} ms).", ""]
    lines += ["## Dificuldades", "", "| | Notas | NPS médio | NPS pico (2 s) | Acordes | Sustains | HOPO | Consistência de riffs |",
              "|---|---|---|---|---|---|---|---|"]
    for name, s in data["dificuldades"].items():
        if s.get("notas"):
            lines.append(f"| {name} | {s['notas']} | {s['nps_media']} | {s['nps_pico_2s']} | {s['acordes_pct']}% | "
                         f"{s['sustains_pct']}% | {s['hopo_pct']}% | {s.get('consistencia_riffs_pct', '—')}% |")
    lines.append("")
    v = data["violacoes"]
    lines += ["## Jogabilidade", "",
              f"- Violações de regras: **{len(v)}**" + (" (nenhuma)" if not v else ""),
              f"- Densidade crescente Easy < Medium < Hard < Expert: {'sim' if data['densidade_monotonica'] else '**não**'}",
              f"- Frases de star power: {len(data['star_power'])}; seções: {len(data['secoes'])}."]
    for item in v[:30]:
        lines.append(f"  - {item}")
    y = data.get("validacao_yarg")
    lines += ["", "## Validação no YARG.Core (o código do jogo)", ""]
    if y is None:
        lines.append("- Não executada (validador indisponível).")
    elif y.get("ok") is None:
        lines.append(f"- Não executada: {y.get('indisponivel', 'motivo desconhecido')}.")
    else:
        lines.append(f"- Resultado: **{'OK' if y.get('ok') else 'FALHOU'}**"
                     + (f" — {y['erro']}" if y.get("erro") else ""))
        if y.get("executado_em", "Windows") != "Windows":
            lines.append(f"- Executada em: {y['executado_em']}.")
        if y.get("dificuldades_no_jogo"):
            lines.append(f"- Encontrada pelo scanner de músicas do jogo; dificuldades: {', '.join(y['dificuldades_no_jogo'])}.")
        if y.get("por_dificuldade"):
            lines += ["", "| | Notas lidas pelo jogo | Tipos (strum/HOPO/tap) conferem | Jogador perfeito | Humano σ 20 ms | Humano σ 35 ms |",
                      "|---|---|---|---|---|---|"]
            for name, s in y["por_dificuldade"].items():
                lines.append(f"| {name} | {s['notas']} | {'sim' if s['tipos_conferem'] else '**não**'} | "
                             f"{s['perfeito_pct']}% | {s['humano_20ms_pct']}% | {s['humano_35ms_pct']}% |")
    lines += ["", "## Tempos de processamento", ""]
    for k, t in data["tempos_s"].items():
        lines.append(f"- {k}: {t} s")
    (folder / "relatorio.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
