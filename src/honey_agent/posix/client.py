# Dueño: P2 — Emulación POSIX
# Responsabilidad: Conector agnóstico de LLM (Ollama, Gemini, vLLM) con temperatura baja para salidas estables.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.tarpit, honey_agent.canary, honey_agent.defense, honey_agent.composition

import asyncio
import json
import urllib.request
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

PostJson = Callable[[str, dict[str, Any], dict[str, str], float], Awaitable[str]]

DEFAULT_TIMEOUT_SECONDS = 2.0


class ModelCallError(Exception):
    """La llamada no llegó a completarse. El mensaje no lleva clave, URL ni prompt."""

    def __init__(self) -> None:
        super().__init__("el modelo no respondió")


class ModelOutputError(Exception):
    """El texto del modelo no es JSON. No guarda el prompt ni la respuesta."""

    def __init__(self) -> None:
        super().__init__("la respuesta del modelo no es JSON")


class ModelConfigError(Exception):
    """Falta un dato para arrancar. El mensaje no incluye el valor secreto."""


async def post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> str:
    """Un solo POST. Si falla, no reintenta y no devuelve la URL."""

    def _send() -> str:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={**headers, "Content-Type": "application/json"},
            method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except Exception:
            raise ModelCallError() from None

    return await asyncio.to_thread(_send)


class LanguageModelClient:
    """Pide el texto al proveedor elegido y rechaza lo que no sea JSON."""

    def __init__(self, model: Any) -> None:
        self._model = model

    async def complete(self, system: str, user: str) -> str:
        text = await self._model.complete(system, user)
        try:
            json.loads(text)
        except (json.JSONDecodeError, TypeError):
            raise ModelOutputError() from None
        return text

    def __repr__(self) -> str:
        return "LanguageModelClient()"


def build_language_model(environ: Mapping[str, str] | None = None) -> LanguageModelClient:
    """Elige Gemini u Ollama al arrancar. Una clave ausente falla aquí, no en plena sesión."""
    from honey_agent.posix.providers.gemini import GeminiModel
    from honey_agent.posix.providers.ollama import OllamaModel

    env = environ if environ is not None else _os_environ()
    provider = env.get("LLM_PROVIDER", "gemini").strip().lower()
    temperature = _read_temperature(env)
    max_tokens = _read_max_tokens(env)
    timeout = _read_timeout(env)
    if provider == "ollama":
        model = OllamaModel(
            base_url=env.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            model=env.get("OLLAMA_MODEL", "llama3:8b-instruct-q4_K_M"),
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    elif provider == "gemini":
        api_key = env.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ModelConfigError("falta GEMINI_API_KEY")
        model = GeminiModel(
            api_key=api_key,
            model=env.get("GEMINI_MODEL", "gemini-3.5-flash"),
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    else:
        raise ModelConfigError("LLM_PROVIDER debe ser gemini u ollama")
    return LanguageModelClient(model)


def _os_environ() -> Mapping[str, str]:
    import os

    return os.environ


def _read_timeout(env: Mapping[str, str]) -> float:
    raw = env.get("LLM_TIMEOUT", "30")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ModelConfigError("LLM_TIMEOUT no es un número") from None
    if value <= 0:
        raise ModelConfigError("LLM_TIMEOUT no es un número")
    return value


def _read_temperature(env: Mapping[str, str]) -> float:
    raw = env.get("LLM_TEMPERATURE", "0.2")
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise ModelConfigError("LLM_TEMPERATURE no es un número") from None


def _read_max_tokens(env: Mapping[str, str]) -> int:
    raw = env.get("LLM_MAX_TOKENS", "512")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ModelConfigError("LLM_MAX_TOKENS no es un entero") from None
    if value <= 0:
        raise ModelConfigError("LLM_MAX_TOKENS no es un entero")
    return value
