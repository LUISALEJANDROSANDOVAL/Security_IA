"""
tests/ingress/test_ssh_pty.py
Dueño: Programador 1 (P1).
Responsabilidad: Validación del listener AsyncSSH, captura de auth y emulación de terminal PTY.
"""

import pytest
import asyncssh
from honey_agent.vfs.in_memory_tree import VirtualFileSystem
from honey_agent.vfs.skeleton import populate_ubuntu_skeleton
from honey_agent.ingress.auth import HoneyAuthHandler
from honey_agent.ingress.ssh_server import HoneySSHServer

def test_auth_capture():
    """Verifica que el gestor de autenticación registre las credenciales enviadas."""
    auth = HoneyAuthHandler()
    assert auth.authenticate_password("192.168.1.50", 45678, "admin", "p4ssw0rd!") is True
    assert len(auth.captured_log) == 1
    record = auth.captured_log[0]
    assert record.ip == "192.168.1.50"
    assert record.username == "admin"
    assert record.password == "p4ssw0rd!"

@pytest.mark.asyncio
async def test_ssh_server_e2e_interaction():
    """Valida un ciclo completo de conexión SSH, autenticación permisiva y ejecución de comandos."""
    master_vfs = VirtualFileSystem()
    populate_ubuntu_skeleton(master_vfs)
    auth = HoneyAuthHandler()
    host_key = asyncssh.generate_private_key("ssh-rsa", key_size=2048)

    # Iniciar servidor en puerto efímero 22225
    server = await asyncssh.create_server(
        lambda: HoneySSHServer(master_vfs=master_vfs, auth_handler=auth),
        host="127.0.0.1",
        port=22225,
        server_host_keys=[host_key],
        server_version="OpenSSH_8.9p1 Ubuntu-3ubuntu0.4",
        encoding="utf-8"
    )

    try:
        async with asyncssh.connect(
            "127.0.0.1",
            port=22225,
            username="attacker_root",
            password="fake_password_123",
            known_hosts=None
        ) as conn:
            # 1. Comprobar captura de credenciales
            assert len(auth.captured_log) >= 1
            assert auth.captured_log[-1].username == "attacker_root"

            # 2. Ejecutar whoami vía canal interactivo/exec
            res_who = await conn.run("whoami")
            assert res_who.stdout.strip() == "attacker_root"

            # 3. Ejecutar cat de /etc/os-release en VFS
            res_cat = await conn.run("cat /etc/os-release")
            assert "Ubuntu 22.04" in res_cat.stdout
    finally:
        server.close()
        await server.wait_closed()
