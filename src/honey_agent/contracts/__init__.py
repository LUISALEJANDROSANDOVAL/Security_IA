# Dueño: los cuatro (P1, P2, P3, P4)
# Responsabilidad: Reexportará ports, events y snapshots cuando existan. Hoy solo marca el paquete.
# Puede importar: biblioteca estándar y pydantic
# No importar: el resto de honey_agent

from honey_agent.contracts.ports import (
    CanarySource,
    EventBus,
    FileSystem,
    Isolator,
    LanguageModel,
    ShellEmulator,
    ShellSession,
    Tarpit,
    ThreatScorer,
)
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
    "CanarySource",
    "CommandResult",
    "EventBus",
    "FileSystem",
    "HistoryEntry",
    "Isolator",
    "LanguageModel",
    "SessionSnapshot",
    "ShellEmulator",
    "ShellSession",
    "Tarpit",
    "ThreatScorer",
    "VfsAction",
    "VfsEntryView",
    "VfsMutation",
    "VfsView",
]
