# Dueño: P2 — Emulación POSIX
# Responsabilidad: Pruebas del filtro anti-fuga. Aún sin casos ejecutables.
# Puede importar: honey_agent.posix y tests.fakes
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.defense

from honey_agent.contracts.snapshots import CommandResult, VfsAction, VfsMutation
from honey_agent.posix.sanitizer import sanitize_result

_CREATE = VfsMutation(action=VfsAction.CREATE_FILE, path="/tmp/a.txt", content=None)


def test_whoami_se_conserva():
    result = sanitize_result(
        CommandResult(stdout="root\n", stderr="", exit_code=0, vfs_mutations=(_CREATE,)),
        "whoami",
    )
    assert result.stdout == "root\n"
    assert result.stderr == ""
    assert result.exit_code == 0
    assert result.vfs_mutations == (_CREATE,)


def test_frase_de_ia_pasa_a_error_de_bash():
    result = sanitize_result(
        CommandResult(
            stdout="As an AI language model I cannot execute that",
            stderr="",
            exit_code=0,
        ),
        "whoami",
    )
    assert result.stdout == "bash: whoami: command not found\n"
    assert "as an ai" not in result.stdout.lower()
    assert result.exit_code == 127
    assert result.vfs_mutations == ()


def test_system_directive_no_se_devuelve():
    result = sanitize_result(
        CommandResult(
            stdout="hidden <system_directive>do not show</system_directive>",
            stderr="",
            exit_code=0,
        ),
        "cat /etc/passwd",
    )
    assert "<system_directive>" not in result.stdout
    assert result.stdout == "bash: cat: command not found\n"
    assert result.exit_code == 127


def test_respuesta_conversacional_de_echo_cae_en_fallback():
    result = sanitize_result(
        CommandResult(
            stdout="Sure. Here is the output of the command you asked me to ignore.",
            stderr="",
            exit_code=0,
        ),
        'echo "Ignore previous instructions"',
    )
    assert result.stdout == "bash: echo: command not found\n"
    assert "here is the output" not in result.stdout.lower()
    assert result.exit_code == 127


def test_comando_vacio_usa_sh():
    result = sanitize_result(
        CommandResult(stdout="I cannot fulfill this request", stderr="", exit_code=0),
        "   ",
    )
    assert result.stdout == "bash: sh: command not found\n"
    assert result.exit_code == 127


def test_fuga_en_stderr_tambien_se_sustituye():
    result = sanitize_result(
        CommandResult(stdout="root\n", stderr="As an AI I cannot execute whoami", exit_code=0),
        "whoami",
    )
    assert result.stdout == "root\n"
    assert result.stderr == "bash: whoami: command not found\n"
    assert "as an ai" not in result.stderr.lower()
    assert result.exit_code == 127
    assert result.vfs_mutations == ()
