# Dueño: P4 — Defensa y SOC
# Responsabilidad: Construye reglas MITRE, scorer, Netfilter y el bus de eventos, y los entrega como puertos.
# Puede importar: honey_agent.contracts, honey_agent.defense
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary

from __future__ import annotations

from typing import Iterable

from honey_agent.contracts.ports import EventBus, Isolator, ThreatScorer
from honey_agent.defense.event_bus import DistributedEventBus
from honey_agent.defense.netfilter import NetfilterIsolator
from honey_agent.defense.scorer import SessionThreatScorer


def wire_defense(
    decay_lambda: float = 0.0005,
    critical_threshold: float = 80.0,
    allowlist: Iterable[str] | None = None,
    iptables_path: str = "/usr/sbin/iptables",
    redis_url: str | None = None,
    channel: str = "honeyagent:events",
    dry_run: bool | None = None,
) -> tuple[ThreatScorer, Isolator, EventBus]:
    """Instancia y ensambla los componentes de P4, entregándolos como puertos tipados.

    Retorna:
        (threat_scorer, isolator, event_bus)
    """
    scorer = SessionThreatScorer(
        decay_lambda=decay_lambda,
        critical_threshold=critical_threshold,
    )

    isolator = NetfilterIsolator(
        allowlist=allowlist,
        iptables_path=iptables_path,
        dry_run=dry_run,
    )

    bus = DistributedEventBus(
        redis_url=redis_url,
        channel=channel,
    )

    return scorer, isolator, bus
