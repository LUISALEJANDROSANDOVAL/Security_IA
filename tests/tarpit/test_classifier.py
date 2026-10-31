# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Pruebas de T_base por primer token: trivial, medio, pesado y no listado.
# Puede importar: honey_agent.tarpit y tests.fakes
# No importar: honey_agent.ingress, honey_agent.posix, honey_agent.defense

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from honey_agent.tarpit.classifier import CommandClassifier


class CommandClassifierTests(unittest.TestCase):
    def setUp(self):
        self.classifier = CommandClassifier()

    def test_trivial_commands_are_fifty_milliseconds(self):
        # S6 fija 0.05 s. S2 dice "< 50 ms"; se afirma 0.05 exacto.
        for command in ("whoami", "id", "pwd", "  WHOAMI  ", "Id", "PWD"):
            with self.subTest(command=command):
                self.assertEqual(self.classifier.base_delay(command), 0.05)

    def test_medium_commands_include_ps_aux_and_ls_la(self):
        for command in ("ps", "ps aux", "netstat", "ls", "ls -la", "  LS -LA  "):
            with self.subTest(command=command):
                self.assertEqual(self.classifier.base_delay(command), 0.35)

    def test_heavy_commands_are_three_point_five_seconds(self):
        commands = (
            "find / -name '*secret*' -type f",
            "grep -r secret /",
            "grep -R password /etc",
            "grep -rn token /var",
            "tar czf backup.tgz /etc",
            "make",
            "MAKE -j4",
            "cat /var/log/syslog",
            "  CAT /VAR/LOG/SYSLOG  ",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(self.classifier.base_delay(command), 3.50)

    def test_unlisted_commands_use_medium_base(self):
        # Supuesto T1: lo que no está en las listas usa 0.35 s.
        for command in ("uname -a", "echo hello", "grep secret /etc/passwd", "cat /etc/hostname"):
            with self.subTest(command=command):
                self.assertEqual(self.classifier.base_delay(command), 0.35)


if __name__ == "__main__":
    unittest.main()
