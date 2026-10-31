# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Inocula, registra el canary y después aplica el retardo. No abre SSH ni llama al modelo.
# Puede importar: honey_agent.contracts, honey_agent.tarpit, honey_agent.canary
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.defense

from honey_agent.canary.inoculator import inoculate
from honey_agent.canary.tracker import CanaryTracker
from honey_agent.tarpit.classifier import CommandClassifier
from honey_agent.tarpit.engine import CognitiveTarpit


class DeceptionFlow:
    """P3 step: replace secret output, record it, then wait."""

    def __init__(self, classifier, tarpit, tracker, secret: bytes):
        self._classifier = classifier
        self._tarpit = tarpit
        self._tracker = tracker
        self._secret = secret
        self.last_delay = 0.0

    async def apply(
        self,
        command: str,
        stdout: str,
        *,
        attacker_ip: str,
        session_id: str,
        interaction_count: int,
        timestamp: int,
    ) -> str:
        inoculation = inoculate(
            command,
            attacker_ip=attacker_ip,
            session_id=session_id,
            secret=self._secret,
            timestamp=timestamp,
        )
        text = stdout
        if inoculation is not None:
            text = inoculation.output
            await self._tracker.record(
                session_id=session_id,
                attacker_ip=attacker_ip,
                token_type=inoculation.token_type,
                token_identifier=inoculation.token_identifier,
                injected_in_command=command,
                destination_asset=inoculation.destination_asset,
                timestamp=str(timestamp),
            )
        base = self._classifier.base_delay(command)
        self.last_delay = await self._tarpit.apply_delay(base, interaction_count)
        return text


def build_deception(secret: bytes, sink=None, post_webhook=None) -> DeceptionFlow:
    """Wire the P3 objects. The HMAC secret comes from the caller."""
    return DeceptionFlow(
        CommandClassifier(),
        CognitiveTarpit(),
        CanaryTracker(sink=sink, post_webhook=post_webhook),
        secret,
    )
