# Dueño: P2 — Emulación POSIX
# Responsabilidad: Proveedor Gemini. Implementa el puerto LanguageModel.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.tarpit, honey_agent.canary, honey_agent.defense, honey_agent.composition

import json
import logging
from typing import Any
from urllib.parse import quote

from honey_agent.posix.client import DEFAULT_TIMEOUT_SECONDS, ModelCallError, PostJson, post_json

logger = logging.getLogger("honey_agent.posix")

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiModel:
    """Llama a Gemini una vez. La clave va en una cabecera, no en la URL ni en los errores."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        post: PostJson | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._post = post if post is not None else post_json

    async def complete(self, system: str, user: str) -> str:
        url = _GEMINI_URL.format(model=quote(self._model, safe=""))
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": self._temperature,
                "maxOutputTokens": self._max_tokens,
                "responseMimeType": "application/json",
            },
        }
        headers = {"x-goog-api-key": self._api_key}
        raw = await self._call(url, payload, headers)
        return _candidate_text(raw)

    async def _call(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> str:
        try:
            return await self._post(url, payload, headers, self._timeout)
        except Exception:
            logger.error("la llamada al modelo falló")
            raise ModelCallError() from None

    def __repr__(self) -> str:
        return "GeminiModel()"


def _candidate_text(raw: str) -> str:
    try:
        body = json.loads(raw)
        parts = body["candidates"][0]["content"]["parts"]
        texts = [part["text"] for part in parts if isinstance(part.get("text"), str)]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
        raise ModelCallError() from None
    if not texts:
        raise ModelCallError()
    return "".join(texts)
