# Dueño: P4 — Defensa y SOC
# Responsabilidad: Publica SessionStart, CommandExecuted, CanaryGenerated y ContainmentTriggered. Implementa el puerto EventBus.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary, honey_agent.composition

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Coroutine

from pydantic import BaseModel

from honey_agent.contracts.events import (
    CanaryGeneratedEvent,
    CommandExecutedEvent,
    ContainmentTriggeredEvent,
    HoneyAgentEvent,
    SessionStartEvent,
)
from honey_agent.contracts.ports import EventBus

logger = logging.getLogger("HoneyAgent.Defense.EventBus")

EventCallback = Callable[[HoneyAgentEvent], Coroutine[Any, Any, None] | None]


class DistributedEventBus(EventBus):
    """Bus de eventos asíncrono para telemetría forense (HA-API-06).

    Publica en Redis Pub/Sub (canal por defecto: `honeyagent:events`)
    y mantiene un despachador local en memoria para observadores locales.
    """

    DEFAULT_CHANNEL: str = "honeyagent:events"

    def __init__(
        self,
        redis_url: str | None = None,
        channel: str = DEFAULT_CHANNEL,
    ) -> None:
        self.redis_url = redis_url
        self.channel = channel
        self._local_subscribers: list[EventCallback] = []
        self._event_history: list[HoneyAgentEvent] = []
        self._max_history: int = 500
        self._redis_client: Any = None
        self._redis_checked: bool = False

    def add_subscriber(self, callback: EventCallback) -> None:
        """Registra un receptor local en memoria."""
        if callback not in self._local_subscribers:
            self._local_subscribers.append(callback)

    def remove_subscriber(self, callback: EventCallback) -> None:
        """Elimina un receptor local."""
        if callback in self._local_subscribers:
            self._local_subscribers.remove(callback)

    def get_history(self) -> list[HoneyAgentEvent]:
        """Retorna una copia del historial reciente en memoria."""
        return list(self._event_history)

    async def _get_redis_client(self) -> Any:
        if self._redis_checked:
            return self._redis_client

        self._redis_checked = True
        if not self.redis_url:
            return None

        try:
            import redis.asyncio as aioredis  # type: ignore
            self._redis_client = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
            )
            logger.info(f"Conexión a Redis establecida exitosamente en {self.redis_url}")
        except ImportError:
            logger.warning("Librería 'redis' no instalada. El bus funcionará en modo In-Memory.")
            self._redis_client = None
        except Exception as ex:
            logger.error(f"No fue posible conectar con Redis en {self.redis_url}: {ex}")
            self._redis_client = None

        return self._redis_client

    async def publish(self, event: Any) -> None:
        """Publica el evento en Redis y notifica a los suscriptores locales."""
        # 1. Serializar el evento
        if isinstance(event, BaseModel):
            payload_json = event.model_dump_json()
            typed_event = event
        elif isinstance(event, dict):
            payload_json = json.dumps(event)
            typed_event = event  # type: ignore
        else:
            payload_json = json.dumps(str(event))
            typed_event = event  # type: ignore

        # 2. Guardar en historial local
        if isinstance(typed_event, (SessionStartEvent, CommandExecutedEvent, CanaryGeneratedEvent, ContainmentTriggeredEvent)):
            self._event_history.append(typed_event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

        # 3. Notificar a suscriptores locales en memoria
        for subscriber in list(self._local_subscribers):
            try:
                res = subscriber(typed_event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as ex:
                logger.error(f"Error en callback de suscriptor de eventos: {ex}")

        # 4. Publicar en Redis Pub/Sub si está disponible
        client = await self._get_redis_client()
        if client:
            try:
                await client.publish(self.channel, payload_json)
            except Exception as ex:
                logger.error(f"Fallo al publicar evento en Redis: {ex}")
