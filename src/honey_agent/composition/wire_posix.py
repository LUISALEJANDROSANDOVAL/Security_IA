# Dueño: P2 — Emulación POSIX
# Responsabilidad: Construye el cliente LLM, el proveedor elegido, el sanitizador y el emulador, y los entrega como puertos.
# Puede importar: honey_agent.contracts, honey_agent.posix
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.tarpit, honey_agent.canary, honey_agent.defense

from collections.abc import Mapping

from honey_agent.posix.client import build_language_model
from honey_agent.posix.emulator import PosixEmulator


def build_shell_emulator(environ: Mapping[str, str] | None = None) -> PosixEmulator:
    """Arma el emulador con el proveedor del entorno. No abre SSH ni llama al modelo todavía."""
    return PosixEmulator(build_language_model(environ))
