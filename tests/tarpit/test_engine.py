# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Pruebas deterministas de la fatiga, el clamp y apply_delay.
# Puede importar: honey_agent.tarpit y tests.fakes
# No importar: honey_agent.ingress, honey_agent.posix, honey_agent.defense

import asyncio
import math
import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from honey_agent.tarpit.classifier import CommandClassifier
from honey_agent.tarpit.engine import CognitiveTarpit


class CognitiveTarpitTests(unittest.TestCase):
    def test_whoami_with_zero_interactions_and_zero_noise_is_base(self):
        # S6 fija 0.05 s (50 ms). No se reduce para cumplir la prosa "< 50 ms" de S2.
        classifier = CommandClassifier()
        tarpit = CognitiveTarpit(noise=lambda: 0.0)
        base = classifier.base_delay("whoami")
        self.assertEqual(base, 0.05)
        self.assertEqual(tarpit.compute_delay(base, 0), 0.05)

    def test_find_secret_base_is_heavy_and_delay_holds_at_least_2_5(self):
        classifier = CommandClassifier()
        tarpit = CognitiveTarpit(noise=lambda: 0.0)
        command = "find / -name '*secret*' -type f"
        base = classifier.base_delay(command)
        self.assertEqual(base, 3.50)
        self.assertGreaterEqual(tarpit.compute_delay(base, 0), 2.5)

    def test_one_interaction_adds_alpha_log_two(self):
        tarpit = CognitiveTarpit(noise=lambda: 0.0)
        expected = 0.05 + 0.65 * math.log(2)
        self.assertEqual(tarpit.compute_delay(0.05, 1), expected)

    def test_delay_clamps_high_to_12_and_low_to_0_02(self):
        tarpit = CognitiveTarpit(noise=lambda: 0.0)
        self.assertEqual(tarpit.compute_delay(100.0, 0), 12.0)
        self.assertEqual(tarpit.compute_delay(-1.0, 0), 0.02)

    def test_apply_delay_awaits_injected_sleep_with_computed_value(self):
        seen = []

        async def fake_sleep(delay):
            seen.append(delay)

        tarpit = CognitiveTarpit(noise=lambda: 0.0, sleep=fake_sleep)
        expected = 0.05 + 0.65 * math.log(2)
        result = asyncio.run(tarpit.apply_delay(0.05, 1))
        self.assertEqual(result, expected)
        self.assertEqual(seen, [expected])


if __name__ == "__main__":
    unittest.main()
