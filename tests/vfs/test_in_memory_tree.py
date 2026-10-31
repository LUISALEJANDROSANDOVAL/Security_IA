"""
tests/vfs/test_in_memory_tree.py
Dueño: Programador 1 (P1).
Responsabilidad: Validación unitaria del árbol VFS en RAM y del SessionState.
"""

import pytest
from honey_agent.vfs.in_memory_tree import VirtualFileSystem
from honey_agent.vfs.skeleton import populate_ubuntu_skeleton
from honey_agent.vfs.session_state import SessionState

@pytest.fixture
def vfs():
    fs = VirtualFileSystem()
    populate_ubuntu_skeleton(fs)
    return fs

@pytest.fixture
def session(vfs):
    return SessionState(vfs, username="root")

def test_ubuntu_skeleton_files_present(vfs):
    """Comprueba que los archivos canónicos de Ubuntu 22.04 existan en RAM."""
    os_release = vfs.read_file("/etc/os-release")
    assert os_release is not None
    assert b"Ubuntu 22.04" in os_release

    passwd = vfs.read_file("/etc/passwd")
    assert passwd is not None
    assert b"root:x:0:0" in passwd

    hostname = vfs.read_file("/etc/hostname")
    assert hostname == b"prod-srv-app01\n"

    proc_ver = vfs.read_file("/proc/version")
    assert proc_ver is not None
    assert b"Linux version 5.15" in proc_ver

    nginx_page = vfs.read_file("/var/www/html/index.nginx-debian.html")
    assert nginx_page is not None
    assert b"Welcome to nginx!" in nginx_page

def test_vfs_write_and_read_isolation(vfs):
    """Verifica que dos sesiones independientes tengan aislamiento absoluto."""
    ses_a = vfs.clone()
    ses_b = vfs.clone()

    ses_a.write_file("/tmp/payload.sh", b"#!/bin/bash\necho pwned")
    assert ses_a.read_file("/tmp/payload.sh") == b"#!/bin/bash\necho pwned"

    # La sesión B jamás debe tener acceso al archivo creado por A en RAM
    assert ses_b.read_file("/tmp/payload.sh") is None

def test_vfs_path_normalization(vfs):
    """Verifica la resolución correcta de rutas relativas con . y .."""
    assert vfs.normalize_path("html", "/var/www") == "/var/www/html"
    assert vfs.normalize_path("../etc", "/var/www") == "/var/etc"
    assert vfs.normalize_path("/var/www/../../etc/passwd") == "/etc/passwd"
    assert vfs.normalize_path("..", "/") == "/"

def test_session_navigation_and_builtins(session):
    """Prueba comandos builtin interactivos (pwd, cd, mkdir, echo, cat)."""
    # 1. PWD inicial
    handled, out, _, code = session.execute_builtin("pwd")
    assert handled is True
    assert code == 0
    assert out.strip() == "/root"

    # 2. CD a /var/www/html
    handled, _, _, code = session.execute_builtin("cd /var/www/html")
    assert handled is True
    assert code == 0
    assert session.cwd == "/var/www/html"

    # 3. Echo y redirección a archivo
    handled, _, _, code = session.execute_builtin("echo 'database_pass=secret123' > config.env")
    assert handled is True
    assert code == 0
    assert session.vfs.read_file("/var/www/html/config.env") == b"database_pass=secret123\n"

    # 4. Echo append (>>)
    handled, _, _, code = session.execute_builtin("echo 'api_key=xyz' >> config.env")
    assert handled is True
    assert code == 0
    content = session.vfs.read_file("/var/www/html/config.env").decode("utf-8")
    assert "database_pass=secret123" in content
    assert "api_key=xyz" in content

    # 5. Cat del archivo creado
    handled, out, _, code = session.execute_builtin("cat config.env")
    assert handled is True
    assert code == 0
    assert "database_pass=secret123" in out

    # 6. LS en el directorio actual
    handled, out, _, code = session.execute_builtin("ls -la")
    assert handled is True
    assert code == 0
    assert "config.env" in out
    assert "index.nginx-debian.html" in out

    # 7. Whoami e ID
    _, out_whoami, _, _ = session.execute_builtin("whoami")
    assert out_whoami.strip() == "root"

    _, out_id, _, _ = session.execute_builtin("id")
    assert "uid=0(root)" in out_id

def test_non_builtin_delegation(session):
    """Comandos externos complejos deben retornar handled=False para que el LLM los asuma."""
    handled, _, _, _ = session.execute_builtin("ps aux | grep root")
    assert handled is False

    handled, _, _, _ = session.execute_builtin("uname -a")
    assert handled is False
