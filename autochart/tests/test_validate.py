import unittest
from unittest import mock

from autochart import validate


class WindowsBlockDetection(unittest.TestCase):
    """Saídas reais do `dotnet test` quando o Smart App Control barra a DLL do validador."""

    def test_detects_blocked_test_assembly(self):
        saida = ("NUnit.Engine.NUnitEngineException: Failed to load the test assembly "
                 r"C:\Dev\GuitarHero\tools\validator\bin\Debug\net10.0\Validator.dll")
        self.assertTrue(validate._bloqueado_pelo_windows(saida))

    def test_detects_code_integrity_message_in_portuguese(self):
        saida = "Uma política de Controle de Aplicativo bloqueou este arquivo. (0x800711C7)"
        self.assertTrue(validate._bloqueado_pelo_windows(saida))

    def test_ordinary_failure_is_not_a_block(self):
        self.assertFalse(validate._bloqueado_pelo_windows("error CS0246: The type or namespace name 'X' could not be found"))

    def test_container_fallback_reports_missing_docker(self):
        with mock.patch.object(validate.shutil, "which", return_value=None):
            motivo = validate._validar_no_conteiner(mock.MagicMock(), mock.MagicMock(), timeout=10)
        self.assertEqual(motivo, "Docker não encontrado")


if __name__ == "__main__":
    unittest.main()
