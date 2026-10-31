"""
src/honey_agent/ingress/ssh_server.py
Dueño: Programador 1 (P1).
Responsabilidad: Servidor AsyncSSH, banner OpenSSH 8.9p1 y aislamiento multi-tenant.
"""

import asyncssh
import logging
from honey_agent.vfs.in_memory_tree import VirtualFileSystem
from honey_agent.vfs.session_state import SessionState
from honey_agent.ingress.auth import HoneyAuthHandler
from honey_agent.ingress.pty_session import HoneyPTYSession

logger = logging.getLogger("HoneyAgent.SSHServer")

class HoneySSHServer(asyncssh.SSHServer):
    """Implementa el servidor SSH señuelo sobre AsyncSSH."""

    def __init__(self, master_vfs: VirtualFileSystem, auth_handler: HoneyAuthHandler):
        self.master_vfs = master_vfs
        self.auth_handler = auth_handler
        self.client_ip = "127.0.0.1"
        self.client_port = 0
        self.username = "root"

    def connection_made(self, conn: asyncssh.SSHServerConnection):
        peer = conn.get_extra_info("peername")
        if peer:
            self.client_ip, self.client_port = peer[0], peer[1]
        logger.info(f"[TCP INGRESS] Conexion establecida desde {self.client_ip}:{self.client_port}")

    def begin_auth(self, username: str) -> bool:
        self.username = username or "root"
        return True

    def password_auth_supported(self) -> bool:
        """Habilita la autenticación por contraseña."""
        return True

    def validate_password(self, username: str, password: str) -> bool:
        """Captura credenciales enviadas y autoriza el acceso."""
        return self.auth_handler.authenticate_password(
            ip=self.client_ip, port=self.client_port, username=username, password=password
        )

    def session_requested(self) -> asyncssh.SSHServerSession:
        """Crea una sesión con VFS clonado en RAM e independiente para cada atacante."""
        isolated_vfs = self.master_vfs.clone()
        session_state = SessionState(vfs=isolated_vfs, username=self.username)
        return HoneyPTYSession(session_state)
