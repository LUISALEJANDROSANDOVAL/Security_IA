# Dueño: P2 — Emulación POSIX
# Responsabilidad: Pruebas del resumen de sesión. Comprueban el recorte, sin llamar al modelo.
# Puede importar: honey_agent.posix y tests.fakes
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.defense

from datetime import datetime, timezone

from honey_agent.contracts.snapshots import HistoryEntry, SessionSnapshot, VfsView
from honey_agent.posix.context_manager import OUTPUT_LIMIT, build_context

_NOW = datetime(2026, 10, 31, 18, 44, 0, tzinfo=timezone.utc)


def _snapshot(**overrides) -> SessionSnapshot:
    data = {
        "session_id": "sess-1",
        "user": "root",
        "hostname": "prod-srv-app01",
        "cwd": "/root",
        "env": {"PATH": "/usr/bin", "HOME": "/root"},
        "history": (),
        "vfs": VfsView(listing={}),
    }
    data.update(overrides)
    return SessionSnapshot(**data)


def test_historial_corto_se_conserva_entero():
    context = build_context(
        _snapshot(
            history=(
                HistoryEntry(command="whoami", output="root\n"),
                HistoryEntry(command="pwd", output="/root\n"),
            )
        ),
        now=_NOW,
    )
    assert context.history_text == "$ whoami\nroot\n$ pwd\n/root"


def test_solo_entran_los_ultimos_diez_comandos():
    history = tuple(
        HistoryEntry(command=f"cmd-{index}", output=f"out-{index}")
        for index in range(12)
    )
    context = build_context(_snapshot(history=history), now=_NOW)
    assert "$ cmd-0\n" not in context.history_text
    assert "$ cmd-1\n" not in context.history_text
    assert "$ cmd-2\n" in context.history_text
    assert context.history_text.endswith("$ cmd-11\nout-11")
    assert context.history_text.count("$ cmd-") == 10


def test_la_salida_larga_se_corta_a_doscientos_caracteres():
    context = build_context(
        _snapshot(history=(HistoryEntry(command="ls", output="x" * 500),)),
        now=_NOW,
    )
    output = context.history_text.split("\n", 1)[1]
    assert len(output) == OUTPUT_LIMIT
    assert output.endswith("...")


def test_el_entorno_lleva_usuario_carpeta_hora_y_archivos():
    context = build_context(
        _snapshot(
            cwd="/var/www/html",
            vfs=VfsView(
                listing={
                    "/var/www/html/index.html": "<html>",
                    "/var/www/html/.env": "secreto",
                    "/etc/passwd": "root:x:0:0",
                    "/var/www/html/assets/app.js": "js",
                }
            ),
        ),
        now=_NOW,
    )
    text = context.environment_text
    assert "CURRENT_USER: root" in text
    assert "HOSTNAME: prod-srv-app01" in text
    assert "CURRENT_WORKING_DIR: /var/www/html" in text
    assert "CURRENT_TIME_UTC: 2026-10-31T18:44:00Z" in text
    assert "PATH=/usr/bin" in text
    assert '"index.html"' in text
    assert '".env"' in text
    assert "passwd" not in text
    assert "app.js" not in text


def test_no_copia_variables_que_parecen_claves_del_host():
    context = build_context(
        _snapshot(
            env={
                "PATH": "/usr/bin",
                "GEMINI_API_KEY": "sk-real-host-key",
                "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI",
                "NOTE": "AKIAIOSFODNN7EXAMPLE",
            }
        ),
        now=_NOW,
    )
    text = context.environment_text
    assert "PATH=/usr/bin" in text
    assert "GEMINI_API_KEY" not in text
    assert "sk-real-host-key" not in text
    assert "AWS_SECRET_ACCESS_KEY" not in text
    assert "AKIAIOSFODNN7EXAMPLE" not in text
