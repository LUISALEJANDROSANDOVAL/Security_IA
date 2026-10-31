# Dueño: P2 — Emulación POSIX
# Responsabilidad: Proveedor Ollama. Implementa el puerto LanguageModel.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.tarpit, honey_agent.canary, honey_agent.defense, honey_agent.composition

import json
import logging
from typing import Any

from honey_agent.posix.client import DEFAULT_TIMEOUT_SECONDS, ModelCallError, PostJson, post_json

logger = logging.getLogger("honey_agent.posix")


class OllamaModel:
    """Llama a Ollama una vez. Si no responde, no entrega la URL ni el prompt."""

    def __init__(
        self,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        post: PostJson | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._post = post if post is not None else post_json

    async def complete(self, system: str, user: str) -> str:
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self._temperature,
                "num_predict": self._max_tokens,
            },
        }
        raw = await self._call(url, payload, {})
        return _message_content(raw)

    async def _call(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> str:
        try:
            return await self._post(url, payload, headers, self._timeout)
        except Exception:
            logger.error("la llamada al modelo falló")
            raise ModelCallError() from None

    def __repr__(self) -> str:
        return "OllamaModel()"


def _message_content(raw: str) -> str:
    try:
        body = json.loads(raw)
        content = body["message"]["content"]
    except (json.JSONDecodeError, KeyError, TypeError):
        raise ModelCallError() from None
    if not isinstance(content, str):
        raise ModelCallError()
    return content
