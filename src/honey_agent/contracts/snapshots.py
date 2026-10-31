# Dueño: los cuatro (P1, P2, P3, P4)
# Responsabilidad: SessionSnapshot y VfsView inmutables. P2, P3 y P4 leen estas vistas y no la clase mutable del VFS.
# Puede importar: biblioteca estándar y pydantic
# No importar: el resto de honey_agent

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VfsEntryView(BaseModel):
    """Ficha de un archivo visible. La usa P1 al describir una carpeta."""

    name: str
    is_dir: bool
    size: int
    permissions: int


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
    """Foto de la sesión. P1 la rellena. P2, P3 y P4 la leen y no la modifican.

    P1 escribe username, command_history y visible_files.
    P2 lee user, history y vfs. Si solo llega un lado, el otro se completa.
    """

    model_config = ConfigDict(frozen=True)

    session_id: str = "sess-01"
    username: str = "root"
    user: str = ""
    hostname: str = "prod-srv-app01"
    cwd: str = "/root"
    env: dict[str, str] = Field(default_factory=dict)
    command_history: list[str] = Field(default_factory=list)
    visible_files: list[str] = Field(default_factory=list)
    history: tuple[HistoryEntry, ...] = ()
    vfs: VfsView = Field(default_factory=VfsView)

    @model_validator(mode="before")
    @classmethod
    def _align_both_sides(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        merged = dict(data)
        if "user" not in merged and "username" not in merged:
            merged["user"] = "root"
        elif "user" not in merged:
            merged["user"] = merged["username"]
        elif "username" not in merged:
            merged["username"] = merged["user"]

        history = merged.get("history")
        if "history" not in merged and merged.get("command_history"):
            merged["history"] = [
                {"command": command, "output": ""} for command in merged["command_history"]
            ]
        elif "command_history" not in merged and history:
            merged["command_history"] = [_command_of(entry) for entry in history]

        visible = merged.get("visible_files")
        cwd = str(merged.get("cwd", "/root"))
        if "vfs" not in merged and visible:
            merged["vfs"] = {"listing": _listing_from_names(cwd, list(visible))}
        elif "visible_files" not in merged and "vfs" in merged:
            merged["visible_files"] = _names_in_cwd(cwd, _listing_of(merged["vfs"]))
        return merged


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


def _command_of(entry: object) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        command = entry.get("command", "")
        return command if isinstance(command, str) else ""
    command = getattr(entry, "command", "")
    return command if isinstance(command, str) else ""


def _listing_of(vfs: object) -> dict[str, str]:
    if isinstance(vfs, VfsView):
        return vfs.listing
    if isinstance(vfs, dict):
        listing = vfs.get("listing", {})
        if isinstance(listing, dict):
            return {str(path): str(content) for path, content in listing.items()}
    return {}


def _listing_from_names(cwd: str, names: list[str]) -> dict[str, str]:
    directory = cwd.rstrip("/") or "/"
    listing: dict[str, str] = {}
    for name in names:
        if directory == "/":
            listing[f"/{name}"] = ""
        else:
            listing[f"{directory}/{name}"] = ""
    return listing


def _names_in_cwd(cwd: str, listing: dict[str, str]) -> list[str]:
    directory = cwd.rstrip("/") or "/"
    names: set[str] = set()
    for raw in listing:
        path = raw.strip()
        if not path:
            continue
        if not path.startswith("/"):
            path = f"/{path}" if directory == "/" else f"{directory}/{path}"
        parent, _, name = path.rstrip("/").rpartition("/")
        parent = parent or "/"
        if parent == directory and name:
            names.add(name)
    return sorted(names)
