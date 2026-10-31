# Dueño: los cuatro (P1, P2, P3, P4)
# Responsabilidad: Reexportará ports, events y snapshots cuando existan. Hoy solo marca el paquete.
# Puede importar: biblioteca estándar y pydantic
# No importar: el resto de honey_agent

from honey_agent.contracts.ports import FileSystem, LanguageModel, ShellEmulator, ShellSession
from honey_agent.contracts.snapshots import (
    CommandResult,
    HistoryEntry,
    SessionSnapshot,
    VfsAction,
    VfsEntryView,
    VfsMutation,
    VfsView,
)

__all__ = [
    "CommandResult",
    "FileSystem",
    "HistoryEntry",
    "LanguageModel",
    "SessionSnapshot",
    "ShellEmulator",
    "ShellSession",
    "VfsAction",
    "VfsEntryView",
    "VfsMutation",
    "VfsView",
]
