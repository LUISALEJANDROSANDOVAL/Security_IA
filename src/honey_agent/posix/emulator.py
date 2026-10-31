# Dueño: P2 — Emulación POSIX
# Responsabilidad: Fachada: SessionSnapshot + comando → stdout, stderr y exit code. Implementa el puerto ShellEmulator.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.tarpit, honey_agent.canary, honey_agent.defense, honey_agent.composition

import json
import logging
from datetime import datetime

from honey_agent.contracts.snapshots import CommandResult, SessionSnapshot, VfsAction, VfsMutation
from honey_agent.posix.client import ModelCallError, ModelOutputError
from honey_agent.posix.context_manager import build_context
from honey_agent.posix.prompts import build_prompts
from honey_agent.posix.sanitizer import bash_command_not_found, sanitize_result

logger = logging.getLogger("honey_agent.posix")

_PROMPT_MARKERS = (
    "<system_directive>",
    "You are the kernel and userland shell parser",
    "MANDATORY JSON OUTPUT SCHEMA",
)
_ACTIONS = {item.value for item in VfsAction}


class PosixEmulator:
    """Une resumen, instrucciones, modelo y filtro. No abre la red del comando atacante."""

    def __init__(self, model, now: datetime | None = None) -> None:
        self._model = model
        self._now = now

    async def execute(self, snapshot: SessionSnapshot, command: str) -> CommandResult:
        if not command.strip():
            return CommandResult(stdout="", stderr="", exit_code=0)
        context = build_context(snapshot, now=self._now)
        prompts = build_prompts(context.environment_text, context.history_text, command)
        try:
            raw = await self._model.complete(prompts.system, prompts.user)
        except (ModelCallError, ModelOutputError):
            logger.error("la llamada al modelo falló")
            return _bash_result(command)
        result = _from_model_text(raw, command)
        result = _drop_system_prompt(result, command)
        return sanitize_result(result, command)


def _bash_result(command: str) -> CommandResult:
    return CommandResult(stdout=bash_command_not_found(command), stderr="", exit_code=127)


def _from_model_text(raw: str, command: str) -> CommandResult:
    try:
        body = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return _bash_result(command)
    if not isinstance(body, dict):
        return _bash_result(command)
    return CommandResult(
        stdout=_text(body.get("stdout", "")),
        stderr=_text(body.get("stderr", "")),
        exit_code=_exit_code(body.get("exit_code", 0), "exit_code" in body),
        vfs_mutations=_mutations(body.get("vfs_mutations", [])),
    )


def _drop_system_prompt(result: CommandResult, command: str) -> CommandResult:
    stdout_leaks = _echoes_prompt(result.stdout)
    stderr_leaks = _echoes_prompt(result.stderr)
    if not stdout_leaks and not stderr_leaks:
        return result
    fallback = bash_command_not_found(command)
    return CommandResult(
        stdout=fallback if stdout_leaks else result.stdout,
        stderr=fallback if stderr_leaks else result.stderr,
        exit_code=127,
        vfs_mutations=(),
    )


def _echoes_prompt(text: str) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in _PROMPT_MARKERS)


def _text(value: object) -> str:
    if isinstance(value, str):
        return value
    return ""


def _exit_code(value: object, present: bool) -> int:
    if not present or value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return 1
    return 1


def _mutations(value: object) -> tuple[VfsMutation, ...]:
    if not isinstance(value, list):
        return ()
    found: list[VfsMutation] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        action = item.get("action")
        path = item.get("path")
        if action not in _ACTIONS or not isinstance(path, str) or not path:
            continue
        content = item.get("content")
        if content is not None and not isinstance(content, str):
            content = None
        found.append(VfsMutation(action=VfsAction(action), path=path, content=content))
    return tuple(found)
