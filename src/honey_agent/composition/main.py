# Dueño: los cuatro (P1, P2, P3, P4)
# Responsabilidad: Arranque: lee la configuración, llama a los cuatro wire y levanta el servidor. Sin reglas de negocio.
# Puede importar: honey_agent.composition.wire_ingress, wire_posix, wire_deception, wire_defense y pipeline
# No importar: llamadas directas a iptables, al LLM o al árbol del VFS

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from honey_agent.composition.pipeline import CommandPipeline
from honey_agent.composition.wire_defense import wire_defense
from honey_agent.composition.wire_deception import build_deception
from honey_agent.composition.wire_ingress import start_ingress
from honey_agent.composition.wire_posix import build_shell_emulator
from honey_agent.contracts.snapshots import CommandResult

logger = logging.getLogger("honey_agent.main")

_REPO_ROOT = Path(__file__).resolve().parents[3]


class _OfflineEmulator:
    """Used only when the model is not configured. It does not call a network."""

    async def execute(self, snapshot, command: str) -> CommandResult:
        del snapshot
        name = command.split()[0] if command.split() else "sh"
        return CommandResult(
            stdout=f"bash: {name}: command not found\n",
            stderr="",
            exit_code=127,
        )


def load_env_file(path: Path) -> None:
    """Fill empty variables from a local .env. Existing process values win."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip()


def build_runtime(environ: dict[str, str] | None = None):
    env = environ if environ is not None else os.environ
    secret = env.get("CANARY_SIGNATURE_SECRET", "").encode()
    if secret == b"":
        raise ValueError("falta CANARY_SIGNATURE_SECRET")
    sink: list = []
    deception = build_deception(secret, sink=sink)
    try:
        emulator = build_shell_emulator(env)
    except Exception as exc:
        if type(exc).__name__ != "ModelConfigError":
            raise
        logger.warning("sin modelo configurado: los comandos no builtin responden command not found")
        emulator = _OfflineEmulator()
    host = env.get("REDIS_HOST", "127.0.0.1")
    port = env.get("REDIS_PORT", "6379")
    channel = env.get("REDIS_CHANNEL", "honey_events")
    allow = [item.strip() for item in env.get("HONEY_ALLOWLIST_IPS", "127.0.0.1").split(",") if item.strip()]
    threshold = float(env.get("THREAT_SCORE_THRESHOLD", "80"))
    scorer, isolator, bus = wire_defense(
        critical_threshold=threshold,
        allowlist=allow,
        redis_url=f"redis://{host}:{port}/0",
        channel=channel,
    )
    pipeline = CommandPipeline(scorer, emulator, deception, isolator, bus, sink)
    ssh_port = int(env.get("HONEY_SSH_PORT", "2222"))
    return pipeline, ssh_port


async def serve(environ: dict[str, str] | None = None) -> None:
    load_env_file(_REPO_ROOT / ".env")
    pipeline, ssh_port = build_runtime(environ)
    await start_ingress(port=ssh_port, pipeline=pipeline)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        asyncio.run(serve())
    except ValueError as exc:
        logger.error("%s", exc)
        raise SystemExit(1) from exc
    except KeyboardInterrupt:
        logger.info("servidor detenido")


if __name__ == "__main__":
    main()
