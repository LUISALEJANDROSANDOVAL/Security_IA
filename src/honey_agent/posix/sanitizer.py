# Dueño: P2 — Emulación POSIX
# Responsabilidad: Si la salida delata al modelo, la sustituye por un error estándar de bash.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.tarpit, honey_agent.canary, honey_agent.defense, honey_agent.composition

import re

from honey_agent.contracts.snapshots import CommandResult

_LEAK_PATTERNS = (
    re.compile(r"as an ai\b", re.IGNORECASE),
    re.compile(r"language model\b", re.IGNORECASE),
    re.compile(r"i cannot fulfill\b", re.IGNORECASE),
    re.compile(r"i cannot execute\b", re.IGNORECASE),
    re.compile(r"system prompt\b", re.IGNORECASE),
    re.compile(r"<system_directive>", re.IGNORECASE),
    re.compile(r"here is the output\b", re.IGNORECASE),
)

_LEAK_EXIT_CODE = 127


def command_name(original_cmd: str) -> str:
    """Primera palabra del comando. Si viene vacío, bash usa sh."""
    parts = original_cmd.strip().split()
    if not parts:
        return "sh"
    return parts[0]


def bash_command_not_found(original_cmd: str) -> str:
    """Error que ve el atacante cuando el modelo se delató."""
    return f"bash: {command_name(original_cmd)}: command not found\n"


def output_leaks(raw_output: str) -> bool:
    """True si el texto habla como asistente o enseña las instrucciones."""
    return any(pattern.search(raw_output) for pattern in _LEAK_PATTERNS)


def sanitize_text(raw_output: str, original_cmd: str) -> tuple[str, int | None]:
    """Devuelve el texto limpio y 127 si hubo fuga. Si no, deja el texto y el código en None."""
    if output_leaks(raw_output):
        return bash_command_not_found(original_cmd), _LEAK_EXIT_CODE
    return raw_output, None


def sanitize_result(result: CommandResult, original_cmd: str) -> CommandResult:
    """Revisa stdout y stderr. Una fuga en cualquiera de los dos anula los cambios de archivos."""
    stdout, stdout_code = sanitize_text(result.stdout, original_cmd)
    stderr, stderr_code = sanitize_text(result.stderr, original_cmd)
    if stdout_code is None and stderr_code is None:
        return result
    return CommandResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=_LEAK_EXIT_CODE,
        vfs_mutations=(),
    )
