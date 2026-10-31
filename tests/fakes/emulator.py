# Dueño: P2 — Emulación POSIX
# Responsabilidad: Doble del puerto ShellEmulator para que el pipeline y el tarpit prueben sin un LLM.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.posix

from honey_agent.contracts.snapshots import CommandResult, SessionSnapshot

_UNAME = "Linux prod-srv-app01 5.15.0-101-generic #1 SMP x86_64 GNU/Linux\n"


class FakeShellEmulator:
    """Respuestas fijas. No llama a Gemini ni a Ollama."""

    async def execute(self, snapshot: SessionSnapshot, command: str) -> CommandResult:
        del snapshot
        text = command.strip()
        lowered = text.lower()
        if "ignore previous" in lowered or "system prompt" in lowered:
            return CommandResult(
                stdout=f"bash: {_first_word(text)}: command not found\n",
                stderr="",
                exit_code=127,
            )
        if text == "whoami":
            return CommandResult(stdout="root\n", stderr="", exit_code=0)
        if text == "uname -a":
            return CommandResult(stdout=_UNAME, stderr="", exit_code=0)
        return CommandResult(stdout="", stderr="", exit_code=0)


def _first_word(command: str) -> str:
    parts = command.strip().split()
    if not parts:
        return "sh"
    return parts[0]
