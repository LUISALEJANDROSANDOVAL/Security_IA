# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Prueba de que el ensamble inocula y registra antes de esperar.
# Puede importar: honey_agent.composition.wire_deception
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.defense

import asyncio
import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from honey_agent.composition.wire_deception import DeceptionFlow
from honey_agent.tarpit.classifier import CommandClassifier
from honey_agent.tarpit.engine import CognitiveTarpit
from honey_agent.canary.tracker import CanaryTracker

_SECRET = b"t5-wire-unit-secret"
_IP = "203.0.113.10"
_SESSION = "sess-unit-1"
_TIMESTAMP = 1700000000


class DeceptionFlowTests(unittest.TestCase):
    def test_secret_read_is_recorded_before_the_delay(self):
        order = []
        sink = []

        async def fake_sleep(delay):
            order.append("sleep")
            self.assertEqual(len(sink), 1)
            self.assertEqual(delay, 0.35)

        async def scenario():
            flow = DeceptionFlow(
                CommandClassifier(),
                CognitiveTarpit(noise=lambda: 0.0, sleep=fake_sleep),
                CanaryTracker(sink=sink),
                _SECRET,
            )
            text = await flow.apply(
                "cat /var/www/html/.env",
                "stdout-from-posix",
                attacker_ip=_IP,
                session_id=_SESSION,
                interaction_count=0,
                timestamp=_TIMESTAMP,
            )
            return text

        text = asyncio.run(scenario())
        self.assertEqual(order, ["sleep"])
        self.assertNotIn("stdout-from-posix", text)
        self.assertIn("AWS_ACCESS_KEY_ID", text)
        self.assertIn("CANARY", text)
        event = sink[0]
        self.assertEqual(event["event_type"], "CANARY_TOKEN_INOCULATED")
        self.assertEqual(event["injected_in_command"], "cat /var/www/html/.env")
        self.assertEqual(event["destination_asset"], "/var/www/html/.env")
        self.assertEqual(event["attacker_ip"], _IP)
        self.assertEqual(event["session_id"], _SESSION)

    def test_ordinary_command_keeps_stdout_and_still_waits(self):
        seen = []

        async def fake_sleep(delay):
            seen.append(delay)

        async def scenario():
            flow = DeceptionFlow(
                CommandClassifier(),
                CognitiveTarpit(noise=lambda: 0.0, sleep=fake_sleep),
                CanaryTracker(),
                _SECRET,
            )
            return await flow.apply(
                "whoami",
                "stdout-from-posix\n",
                attacker_ip=_IP,
                session_id=_SESSION,
                interaction_count=0,
                timestamp=_TIMESTAMP,
            )

        text = asyncio.run(scenario())
        self.assertEqual(text, "stdout-from-posix\n")
        self.assertEqual(seen, [0.05])


if __name__ == "__main__":
    unittest.main()
