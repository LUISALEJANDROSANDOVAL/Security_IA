# Dueño: los cuatro (P1, P2, P3, P4)
# Responsabilidad: SessionSnapshot y VfsView inmutables. P2, P3 y P4 leen estas vistas y no la clase mutable del VFS.
# Puede importar: biblioteca estándar y pydantic
# No importar: el resto de honey_agent

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class VfsAction(str, Enum):
    """Cambio que el emulador anota y P1 aplica en la memoria de la sesión."""

    CREATE_FILE = "CREATE_FILE"
    DELETE_FILE = "DELETE_FILE"
    CHANGE_DIR = "CHANGE_DIR"


class HistoryEntry(BaseModel):
    """Un comando ya ejecutado y un recorte de su salida."""

    model_config = ConfigDict(frozen=True)

    command: str
    output: str


class VfsView(BaseModel):
    """Rutas visibles y un resumen del contenido. No es el árbol de archivos de P1."""

    model_config = ConfigDict(frozen=True)

    listing: dict[str, str] = Field(default_factory=dict)


class SessionSnapshot(BaseModel):
    """Foto de la sesión. La rellena P1. P2 la lee y no la modifica."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    user: str
    hostname: str
    cwd: str
    env: dict[str, str] = Field(default_factory=dict)
    history: tuple[HistoryEntry, ...] = ()
    vfs: VfsView = Field(default_factory=VfsView)


class VfsMutation(BaseModel):
    """Nota de un cambio. content va en base64, o null si el cambio no tiene cuerpo."""

    model_config = ConfigDict(frozen=True)

    action: VfsAction
    path: str
    content: str | None = None


class CommandResult(BaseModel):
    """Lo que el emulador devuelve: texto de la terminal y los cambios a aplicar."""

    model_config = ConfigDict(frozen=True)

    stdout: str
    stderr: str
    exit_code: int
    vfs_mutations: tuple[VfsMutation, ...] = ()
