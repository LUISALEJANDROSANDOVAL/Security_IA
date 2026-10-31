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

from typing import Any, Optional, Protocol

from honey_agent.contracts.snapshots import CommandResult, SessionSnapshot


class FileSystem(Protocol):
    """Puerto de sistema de archivos implementado por P1 (VFS)."""

    def normalize_path(self, path: str, cwd: str = "/") -> str: ...
    def write_file(self, canonical_path: str, content: bytes, permissions: int = 0o644) -> bool: ...
    def read_file(self, canonical_path: str) -> Optional[bytes]: ...
    def listdir(self, canonical_path: str) -> Optional[list[tuple[str, Any]]]: ...
    def mkdir(self, canonical_path: str, permissions: int = 0o755) -> bool: ...
    def unlink(self, canonical_path: str) -> bool: ...


class ShellSession(Protocol):
    """Puerto de sesión interactiva implementado por P1 (SessionState)."""

    def get_prompt(self) -> str: ...
    def to_snapshot(self) -> SessionSnapshot: ...
    def execute_builtin(self, cmd_line: str) -> tuple[bool, str, str, int]: ...


class LanguageModel(Protocol):
    """Llama al modelo. Lo implementan Gemini y Ollama."""

    async def complete(self, system: str, user: str) -> str:
        """Devuelve el texto crudo del modelo, todavía sin filtrar."""
        ...


class ShellEmulator(Protocol):
    """Terminal falsa. La implementa el emulador de P2."""

    async def execute(self, snapshot: SessionSnapshot, command: str) -> CommandResult:
        """Convierte el comando en stdout, stderr, código de salida y cambios."""
        ...
