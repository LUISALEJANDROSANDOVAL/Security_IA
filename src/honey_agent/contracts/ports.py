# Dueño: los cuatro (P1, P2, P3, P4)
# Responsabilidad: Puertos del sistema. Cambiar una firma exige dos revisores.
# Puede importar: biblioteca estándar y pydantic
# No importar: el resto de honey_agent

# Implementa cada puerto solo el dueño indicado. Los demás dependen de este archivo.
# - FileSystem       P1 — Ingress y VFS
# - ShellSession     P1 — Ingress y VFS
# - ShellEmulator    P2 — Emulación POSIX
# - LanguageModel    P2 — Emulación POSIX
# - Tarpit           P3 — Tarpit y Canaries
# - CanarySource     P3 — Tarpit y Canaries
# - ThreatScorer     P4 — Defensa y SOC
# - Isolator         P4 — Defensa y SOC
# - EventBus         P4 — Defensa y SOC

from typing import Any, Optional, Protocol, runtime_checkable

from honey_agent.contracts.snapshots import CommandResult, SessionSnapshot


@runtime_checkable
class FileSystem(Protocol):
    """Puerto de sistema de archivos implementado por P1 (VFS)."""

    def normalize_path(self, path: str, cwd: str = "/") -> str: ...
    def write_file(self, canonical_path: str, content: bytes, permissions: int = 0o644) -> bool: ...
    def read_file(self, canonical_path: str) -> Optional[bytes]: ...
    def listdir(self, canonical_path: str) -> Optional[list[tuple[str, Any]]]: ...
    def mkdir(self, canonical_path: str, permissions: int = 0o755) -> bool: ...
    def unlink(self, canonical_path: str) -> bool: ...


@runtime_checkable
class ShellSession(Protocol):
    """Puerto de sesión interactiva implementado por P1 (SessionState)."""

    def get_prompt(self) -> str: ...
    def to_snapshot(self) -> SessionSnapshot: ...
    def execute_builtin(self, cmd_line: str) -> tuple[bool, str, str, int]: ...


@runtime_checkable
class LanguageModel(Protocol):
    """Llama al modelo. Lo implementan Gemini y Ollama."""

    async def complete(self, system: str, user: str) -> str:
        """Devuelve el texto crudo del modelo, todavía sin filtrar."""
        ...


@runtime_checkable
class ShellEmulator(Protocol):
    """Terminal falsa. La implementa el emulador de P2."""

    async def execute(self, snapshot: SessionSnapshot, command: str) -> CommandResult:
        """Convierte el comando en stdout, stderr, código de salida y cambios."""
        ...


@runtime_checkable
class Tarpit(Protocol):
    """Motor de fatiga cognitiva y retardo no bloqueante."""

    async def delay(self, command: str, interaction_count: int) -> float: ...


@runtime_checkable
class CanarySource(Protocol):
    """Generador y rastreador de señuelos con firma HMAC."""

    def inject_if_targeted(self, file_path: str, session_id: str, attacker_ip: str) -> str | None: ...


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
