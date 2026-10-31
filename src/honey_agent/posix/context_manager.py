# Dueño: P2 — Emulación POSIX
# Responsabilidad: Recorta el historial a la ventana reciente y serializa el snapshot del VFS para el prompt.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.tarpit, honey_agent.canary, honey_agent.defense, honey_agent.composition

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from honey_agent.contracts.snapshots import SessionSnapshot

HISTORY_LIMIT = 10
OUTPUT_LIMIT = 200

_SECRET_NAME = re.compile(
    r"(KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|PRIVATE)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SessionContext:
    """Dos textos listos para pegar en el prompt. No incluye la llamada al modelo."""

    history_text: str
    environment_text: str


def build_context(snapshot: SessionSnapshot, now: datetime | None = None) -> SessionContext:
    """Recorta la sesión a lo que el modelo puede leer sin perder el hilo."""
    moment = now if now is not None else datetime.now(timezone.utc)
    return SessionContext(
        history_text=_history_text(snapshot),
        environment_text=_environment_text(snapshot, moment),
    )


def _history_text(snapshot: SessionSnapshot) -> str:
    blocks: list[str] = []
    for entry in snapshot.history[-HISTORY_LIMIT:]:
        output = _clip(entry.output)
        if output:
            blocks.append(f"$ {entry.command}\n{output}")
        else:
            blocks.append(f"$ {entry.command}")
    return "\n".join(blocks)


def _environment_text(snapshot: SessionSnapshot, now: datetime) -> str:
    lines = [
        f"CURRENT_USER: {snapshot.user}",
        f"HOSTNAME: {snapshot.hostname}",
        f"CURRENT_WORKING_DIR: {snapshot.cwd}",
        f"CURRENT_TIME_UTC: {_utc_stamp(now)}",
    ]
    safe_env = {
        name: value
        for name, value in snapshot.env.items()
        if not _looks_like_host_secret(name, value)
    }
    if safe_env:
        lines.append("ENVIRONMENT:")
        for name in sorted(safe_env):
            lines.append(f"  {name}={safe_env[name]}")
    names = _files_in_cwd(snapshot.cwd, snapshot.vfs.listing)
    lines.append("FILES_IN_CWD: " + _format_names(names))
    return "\n".join(lines)


def _clip(text: str) -> str:
    compact = text.strip("\n")
    if len(compact) <= OUTPUT_LIMIT:
        return compact
    return compact[: OUTPUT_LIMIT - 3] + "..."


def _looks_like_host_secret(name: str, value: str) -> bool:
    if _SECRET_NAME.search(name):
        return True
    if "PRIVATE KEY" in value.upper():
        return True
    return value.startswith("AKIA") or value.startswith("sk-")


def _files_in_cwd(cwd: str, listing: dict[str, str]) -> list[str]:
    directory = _normalize(cwd)
    names: set[str] = set()
    for raw in listing:
        path = raw.strip()
        if not path:
            continue
        if not path.startswith("/"):
            path = f"{directory.rstrip('/')}/{path}" if directory != "/" else f"/{path}"
        parent, name = _split(_normalize(path))
        if parent == directory and name:
            names.add(name)
    return sorted(names)


def _format_names(names: list[str]) -> str:
    if not names:
        return "[]"
    quoted = ", ".join(f'"{name}"' for name in names)
    return f"[{quoted}]"


def _normalize(path: str) -> str:
    parts: list[str] = []
    for piece in path.split("/"):
        if piece == "" or piece == ".":
            continue
        if piece == "..":
            if parts:
                parts.pop()
            continue
        parts.append(piece)
    if not parts:
        return "/"
    return "/" + "/".join(parts)


def _split(path: str) -> tuple[str, str]:
    if path == "/":
        return "/", ""
    parent, _, name = path.rpartition("/")
    if parent == "":
        parent = "/"
    return parent, name


def _utc_stamp(now: datetime) -> str:
    if now.tzinfo is None:
        moment = now.replace(tzinfo=timezone.utc)
    else:
        moment = now.astimezone(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
