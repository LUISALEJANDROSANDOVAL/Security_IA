# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Registra cada canary emitido y deja el aviso listo para el bus de eventos.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.defense, honey_agent.composition

_EVENT_TYPE = "CANARY_TOKEN_INOCULATED"


class CanaryTracker:
    """Append each inoculated canary and, when configured, hand the same event to a webhook."""

    def __init__(self, sink=None, post_webhook=None):
        self._sink = [] if sink is None else sink
        self._post_webhook = post_webhook

    async def record(
        self,
        *,
        session_id: str,
        attacker_ip: str,
        token_type: str,
        token_identifier: str,
        injected_in_command: str,
        destination_asset: str,
        timestamp: str,
    ) -> dict:
        event = {
            "event_type": _EVENT_TYPE,
            "timestamp": timestamp,
            "session_id": session_id,
            "attacker_ip": attacker_ip,
            "token_type": token_type,
            "token_identifier": token_identifier,
            "injected_in_command": injected_in_command,
            "destination_asset": destination_asset,
        }
        self._sink.append(event)
        if self._post_webhook is not None:
            await self._post_webhook(event)
        return event
