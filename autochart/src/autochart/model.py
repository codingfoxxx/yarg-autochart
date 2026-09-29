"""Tipos de dados compartilhados pelo pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field

OPEN = 7  # número da nota aberta no .chart ("N 7")

DIFFICULTIES = ("Expert", "Hard", "Medium", "Easy")
SECTION_NAMES = {"Expert": "ExpertSingle", "Hard": "HardSingle", "Medium": "MediumSingle", "Easy": "EasySingle"}


@dataclass
class Note:
    """Uma nota ou acorde do chart gerado."""
    tick: int
    lanes: tuple[int, ...]            # 0..4 (verde..laranja) ou (OPEN,)
    length: int = 0                   # duração do sustain em ticks (0 = sem sustain)
    hopo: bool | None = None          # intenção: True = HOPO, False = palhetada, None = deixar o natural
    tap: bool = False
    time: float = 0.0                 # tempo (s), informativo
    strength: float = 0.0             # força do ataque (onset), para prioridades
    pitch: float | None = None        # altura MIDI estimada (contorno)
    source_index: int = -1            # índice do evento de origem (para rastrear reduções)

    @property
    def is_chord(self) -> bool:
        return len(self.lanes) > 1


@dataclass
class Event:
    """Um ataque musical detectado no áudio, antes de virar nota."""
    time: float
    strength: float
    pitch: float | None = None        # altura MIDI dominante (fracionária), se houver
    polyphony: int = 1                # quantas notas simultâneas (1 = nota simples)
    duration: float = 0.0             # quanto o som se sustenta (s)
    attack: float = 1.0               # nitidez do ataque relativa aos vizinhos (≈1 normal, <0,6 ligado)
    from_onset: bool = True           # False = só apareceu na transcrição (ataque não detectado)


@dataclass
class SongMeta:
    name: str
    artist: str = "Desconhecido"
    album: str = ""
    genre: str = ""
    year: str = ""
    charter: str = "autochart"
    loading_phrase: str = ""
    preview_start_ms: int = -1
    song_length_ms: int = 0
    diff_guitar: int = -1
    extra: dict[str, str] = field(default_factory=dict)
