# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Pruebas de que el registro deja el evento CANARY_TOKEN_INOCULATED en el sumidero.
# Puede importar: honey_agent.canary
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.defense, honey_agent.composition

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from honey_agent.canary.tracker import CanaryTracker

_TIMESTAMP = "2026-10-31T04:15:35.120Z"
_SESSION = "sess-unit-1"
_IP = "203.0.113.10"
_TOKEN_TYPE = "AWS_IAM_CREDENTIAL"
_TOKEN_ID = "AKIAEXAMPLE000CANARY"
_COMMAND = "cat /var/www/html/.env"
_ASSET = "/var/www/html/.env"

_EXPECTED = {
    "event_type": "CANARY_TOKEN_INOCULATED",
    "timestamp": _TIMESTAMP,
    "session_id": _SESSION,
    "attacker_ip": _IP,
    "token_type": _TOKEN_TYPE,
    "token_identifier": _TOKEN_ID,
    "injected_in_command": _COMMAND,
    "destination_asset": _ASSET,
}


def _record(tracker: CanaryTracker):
    return tracker.record(
        session_id=_SESSION,
        attacker_ip=_IP,
        token_type=_TOKEN_TYPE,
        token_identifier=_TOKEN_ID,
        injected_in_command=_COMMAND,
        destination_asset=_ASSET,
        timestamp=_TIMESTAMP,
    )


class CanaryTrackerTests(unittest.IsolatedAsyncioTestCase):
    async def test_record_returns_inoculated_event_with_s9_fields(self) -> None:
        event = await _record(CanaryTracker())
        self.assertEqual(event, _EXPECTED)
        self.assertEqual(event["event_type"], "CANARY_TOKEN_INOCULATED")
        self.assertEqual(event["session_id"], _SESSION)
        self.assertEqual(event["attacker_ip"], _IP)
        self.assertEqual(event["token_type"], _TOKEN_TYPE)
        self.assertEqual(event["token_identifier"], _TOKEN_ID)
        self.assertEqual(event["injected_in_command"], _COMMAND)
        self.assertEqual(event["destination_asset"], _ASSET)
        self.assertEqual(event["timestamp"], _TIMESTAMP)

    async def test_sink_receives_the_same_dict(self) -> None:
        sink = []
        event = await _record(CanaryTracker(sink=sink))
        self.assertEqual(len(sink), 1)
        self.assertIs(sink[0], event)

    async def test_webhook_is_awaited_once_with_the_event(self) -> None:
        sink = []
        calls = []

        async def post_webhook(event: dict) -> None:
            calls.append(event)

        event = await _record(CanaryTracker(sink=sink, post_webhook=post_webhook))
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0], event)
        self.assertIs(sink[0], event)

    async def test_without_webhook_record_still_stores_the_event(self) -> None:
        sink = []
        event = await _record(CanaryTracker(sink=sink, post_webhook=None))
        self.assertEqual(sink, [event])

    async def test_webhook_error_keeps_the_event_and_propagates(self) -> None:
        sink = []

        async def post_webhook(event: dict) -> None:
            raise RuntimeError("webhook down")

        with self.assertRaises(RuntimeError):
            await _record(CanaryTracker(sink=sink, post_webhook=post_webhook))
        self.assertEqual(len(sink), 1)
        self.assertEqual(sink[0], _EXPECTED)
