# Dueño: los cuatro (P1, P2, P3, P4)
# Responsabilidad: Puertos del sistema. Cambiar una firma exige dos revisores.
# Puede importar: biblioteca estándar y pydantic
# No importar: el resto de honey_agent

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


# =====================================================================
# Puertos asignados a P1 — Ingress y VFS
# =====================================================================

@runtime_checkable
class FileSystem(Protocol):
    """Árbol virtual en RAM efímero e inmutable a nivel de host."""
    def read_file(self, path: str) -> str: ...
    def write_file(self, path: str, content: str) -> None: ...
    def exists(self, path: str) -> bool: ...
    def list_dir(self, path: str) -> list[str]: ...


@runtime_checkable
class ShellSession(Protocol):
    """Sesión interactiva SSH/PTY del atacante."""
    session_id: str
    attacker_ip: str
    working_directory: str
    async def write_output(self, text: str) -> None: ...


# =====================================================================
# Puertos asignados a P2 — Emulación POSIX
# =====================================================================

@runtime_checkable
class LanguageModel(Protocol):
    """Conector agnóstico a LLM (Ollama, Gemini, vLLM)."""
    async def generate_response(self, system_prompt: str, user_prompt: str) -> str: ...


@runtime_checkable
class ShellEmulator(Protocol):
    """Fachada de emulación POSIX con LLM y sanitizador."""
    async def execute(
        self,
        command: str,
        session_snapshot: Any,
    ) -> tuple[str, str, int, list[Any]]: ...


# =====================================================================
# Puertos asignados a P3 — Tarpit y Canaries
# =====================================================================

@runtime_checkable
class Tarpit(Protocol):
    """Motor de fatiga cognitiva y retardo no bloqueante."""
    async def delay(self, command: str, interaction_count: int) -> float: ...


@runtime_checkable
class CanarySource(Protocol):
    """Generador y rastreador de señuelos con firma HMAC."""
    def inject_if_targeted(self, file_path: str, session_id: str, attacker_ip: str) -> str | None: ...


# =====================================================================
# Puertos asignados a P4 — Defensa y SOC
# =====================================================================

@runtime_checkable
class ThreatScorer(Protocol):
    """Calculador de amenaza acumulada con decaimiento y reglas MITRE."""
    def score_command(
        self,
        session_id: str,
        command: str,
        timestamp: float | None = None,
    ) -> tuple[float, Any | None, bool]:
        """Evalúa un comando y devuelve (threat_score, mitre_classification, is_critical)."""
        ...

    def get_score(self, session_id: str) -> float:
        """Devuelve el score actual de la sesión (0.0 a 100.0)."""
        ...


@runtime_checkable
class Isolator(Protocol):
    """Controlador atómico de aislamiento perimetral en kernel Linux."""
    async def isolate_ip(self, ip: str, reason: str) -> bool:
        """Aplica regla DROP en el kernel. Devuelve True si fue aplicada."""
        ...

    async def unisolate_ip(self, ip: str) -> bool:
        """Remueve la regla DROP del kernel."""
        ...

    def is_isolated(self, ip: str) -> bool:
        """Verifica si la IP está contenida."""
        ...


@runtime_checkable
class EventBus(Protocol):
    """Publicador asíncrono de telemetría hacia Redis/MQ."""
    async def publish(self, event: Any) -> None:
        """Publica un evento serializable en el canal."""
        ...
