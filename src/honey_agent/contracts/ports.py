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

from typing import Protocol

from honey_agent.contracts.snapshots import CommandResult, SessionSnapshot


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
