# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Clasifica el comando: trivial (whoami, pwd), medio (ps, ls) o pesado (find /, grep -r).
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.canary, honey_agent.defense, honey_agent.composition

_TRIVIAL = 0.05
_MEDIUM = 0.35
_HEAVY = 3.50

_TRIVIAL_COMMANDS = frozenset({"whoami", "id", "pwd"})
_MEDIUM_COMMANDS = frozenset({"ps", "netstat", "ls"})
_HEAVY_COMMANDS = frozenset({"find", "tar", "make"})
_SYSLOG_PATH = "/var/log/syslog"


def _grep_is_recursive(tokens):
    for token in tokens[1:]:
        if token == "--recursive" or token.startswith("--recursive="):
            return True
        if token.startswith("-") and not token.startswith("--") and "r" in token[1:]:
            return True
    return False


class CommandClassifier:
    def base_delay(self, command: str) -> float:
        """T_base del primer token. Un comando no listado usa la base media, 0.35 s."""
        text = command.strip().lower()
        if not text:
            return _MEDIUM
        tokens = text.split()
        name = tokens[0]
        if name == "cat" and _SYSLOG_PATH in tokens:
            return _HEAVY
        if name == "grep" and _grep_is_recursive(tokens):
            return _HEAVY
        if name in _TRIVIAL_COMMANDS:
            return _TRIVIAL
        if name in _HEAVY_COMMANDS:
            return _HEAVY
        if name in _MEDIUM_COMMANDS:
            return _MEDIUM
        return _MEDIUM
