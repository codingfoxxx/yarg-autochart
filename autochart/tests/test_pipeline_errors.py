import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np

from autochart import pipeline
from autochart.model import SongMeta


class NoRhythm(unittest.TestCase):
    """Áudio sem pulso (ruído, fala): erro claro, sem traceback e sem criar pasta."""

    def test_raises_clear_error_and_creates_nothing(self):
        silence = np.zeros((44100 * 5, 2), dtype=np.float32)
        no_beats = SimpleNamespace(beats=np.array([]), downbeats=np.array([]))
        with tempfile.TemporaryDirectory() as out, \
                mock.patch.object(pipeline.audio, "decode", return_value=silence), \
                mock.patch.object(pipeline.analysis, "track_beats", return_value=no_beats):
            with self.assertRaises(pipeline.SemRitmoError) as ctx:
                pipeline.generate(Path("ruido.wav"), Path(out), SongMeta(name="x", artist="y"),
                                  pipeline.Options(validar=False))
            self.assertIn("pulso rítmico", str(ctx.exception))
            self.assertEqual(list(Path(out).iterdir()), [])

    def test_cli_returns_code_3(self):
        from autochart import cli
        with tempfile.NamedTemporaryFile(suffix=".wav") as f, \
                mock.patch.object(pipeline, "generate", side_effect=pipeline.SemRitmoError("sem batidas")):
            code = cli.main(["gerar", f.name, "--titulo", "x", "--artista", "y", "--sem-validacao"])
        self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
