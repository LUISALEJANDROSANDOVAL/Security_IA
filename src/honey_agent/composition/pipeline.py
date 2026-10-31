# Dueño: los cuatro (P1, P2, P3, P4)
# Responsabilidad: Flujo de un comando: puntuar, emular, inocular, retardar, aplicar el cambio al VFS, publicar el evento y aislar si el score cruza el umbral. Solo llama puertos.
# Puede importar: honey_agent.contracts
# No importar: clases concretas; esas entran por el constructor desde los wire_*.py

from __future__ import annotations

import base64
import time
from dataclasses import dataclass

from honey_agent.contracts.events import (
    CanaryGeneratedEvent,
    CommandExecutedEvent,
    ContainmentTriggeredEvent,
    CredentialsUsed,
    MitreClassificationEvent,
    SessionStartEvent,
    TarpitMetricsEvent,
)
from honey_agent.contracts.snapshots import VfsAction


@dataclass(frozen=True)
class CommandOutcome:
    stdout: str
    stderr: str
    exit_code: int


class CommandPipeline:
    """One command: score, emulate or builtin, inoculate, delay, mutate, publish, isolate."""

    def __init__(self, scorer, emulator, deception, isolator, bus, canary_sink):
        self._scorer = scorer
        self._emulator = emulator
        self._deception = deception
        self._isolator = isolator
        self._bus = bus
        self._canary_sink = canary_sink
        self._counts: dict[str, int] = {}

    async def note_session(
        self,
        *,
        session_id: str,
        attacker_ip: str,
        attacker_port: int,
        username: str,
        password: str,
    ) -> None:
        await self._bus.publish(
            SessionStartEvent(
                session_id=session_id,
                attacker_ip=attacker_ip,
                attacker_port=attacker_port,
                credentials_used=CredentialsUsed(username=username, password=password or None),
            )
        )

    async def run(self, session, command: str, attacker_ip: str) -> CommandOutcome:
        text = command.strip()
        if not text:
            return CommandOutcome("", "", 0)

        score, classification, should_isolate = self._scorer.score_command(session.session_id, text)
        snapshot = session.to_snapshot()
        handled, stdout, stderr, code = session.execute_builtin(text)
        mutations = ()
        if not handled:
            result = await self._emulator.execute(snapshot, text)
            stdout, stderr, code = result.stdout, result.stderr, result.exit_code
            mutations = result.vfs_mutations

        count = self._counts.get(session.session_id, 0)
        before = len(self._canary_sink)
        stdout = await self._deception.apply(
            text,
            stdout,
            attacker_ip=attacker_ip,
            session_id=session.session_id,
            interaction_count=count,
            timestamp=int(time.time()),
        )
        self._counts[session.session_id] = count + 1
        inoculated = len(self._canary_sink) > before
        if inoculated:
            stderr = ""
            await self._publish_canary(self._canary_sink[-1])
        else:
            self._apply_mutations(session, mutations)

        delay = float(getattr(self._deception, "last_delay", 0.0))
        await self._bus.publish(
            CommandExecutedEvent(
                session_id=session.session_id,
                attacker_ip=attacker_ip,
                command=text,
                working_directory=getattr(session, "cwd", "/root"),
                user=getattr(session, "username", "root"),
                stdout_snippet=stdout[:500],
                exit_code=code,
                mitre_classification=_mitre_event(classification),
                tarpit_metrics=TarpitMetricsEvent(total_wait_ms=delay * 1000.0),
                threat_score_after_cmd=float(score),
            )
        )
        if should_isolate:
            reason = _isolate_reason(classification, score)
            isolated = await self._isolator.isolate_ip(attacker_ip, reason)
            if isolated:
                await self._bus.publish(
                    ContainmentTriggeredEvent(
                        session_id=session.session_id,
                        attacker_ip=attacker_ip,
                        trigger_reason=reason,
                        final_threat_score=float(score),
                    )
                )
        return CommandOutcome(stdout, stderr, code)

    async def _publish_canary(self, record: dict) -> None:
        identifier = str(record.get("token_identifier", ""))
        await self._bus.publish(
            CanaryGeneratedEvent(
                session_id=str(record.get("session_id", "")),
                attacker_ip=str(record.get("attacker_ip", "")),
                token_type=str(record.get("token_type", "")),
                token_public_id=identifier,
                token_signature_hmac=identifier,
                target_file=str(record.get("destination_asset", "")),
            )
        )

    def _apply_mutations(self, session, mutations) -> None:
        vfs = getattr(session, "vfs", None)
        for mutation in mutations:
            if mutation.action == VfsAction.CHANGE_DIR:
                session.cwd = mutation.path
                env = getattr(session, "env", None)
                if isinstance(env, dict):
                    env["PWD"] = mutation.path
                continue
            if vfs is None:
                continue
            if mutation.action == VfsAction.DELETE_FILE:
                vfs.unlink(mutation.path)
            elif mutation.action == VfsAction.CREATE_FILE:
                vfs.write_file(mutation.path, _decode_content(mutation.content))


def _decode_content(content: str | None) -> bytes:
    if not content:
        return b""
    try:
        return base64.b64decode(content, validate=True)
    except Exception:
        return content.encode()


def _mitre_event(classification):
    if classification is None:
        return None
    technique_id = getattr(classification, "technique_id", None)
    if not technique_id:
        return None
    return MitreClassificationEvent(
        technique_id=technique_id,
        tactic=getattr(classification, "tactic", ""),
        technique_name=getattr(classification, "technique_name", ""),
    )


def _isolate_reason(classification, score: float) -> str:
    technique_id = getattr(classification, "technique_id", None)
    if technique_id:
        return f"CRITICAL_TECHNIQUE: {technique_id}"
    return f"THREAT_THRESHOLD_EXCEEDED: Score={score}"
