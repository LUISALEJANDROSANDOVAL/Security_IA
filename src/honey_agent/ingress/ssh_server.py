# Dueño: Programador 1 (P1).
# Responsabilidad: Servidor AsyncSSH, banner OpenSSH 8.9p1 y aislamiento multi-tenant.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary, honey_agent.defense

import asyncio
import logging
import uuid
from collections.abc import Callable

import asyncssh

from honey_agent.contracts.ports import ShellSession
from honey_agent.ingress.auth import HoneyAuthHandler
from honey_agent.ingress.pty_session import HoneyPTYSession

logger = logging.getLogger("HoneyAgent.SSHServer")

class HoneySSHServer(asyncssh.SSHServer):
    """Implementa el servidor SSH señuelo sobre AsyncSSH."""

    def __init__(
        self,
        auth_handler: HoneyAuthHandler,
        open_session: Callable[[str, str], ShellSession],
        pipeline=None,
    ):
        self.auth_handler = auth_handler
        self.open_session = open_session
        self.pipeline = pipeline
        self.client_ip = "127.0.0.1"
        self.client_port = 0
        self.username = "root"
        self._connection_session_id = None

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
        """Una conexión comparte la sesión que arma composition. Cada atacante sigue aislado."""
        if self._connection_session_id is None:
            self._connection_session_id = (
                str(uuid.uuid4()) if self.pipeline is not None else "sess-01"
            )
            if self.pipeline is not None:
                password = _password_for(self.auth_handler, self.client_ip, self.username)
                asyncio.get_running_loop().create_task(
                    self.pipeline.note_session(
                        session_id=self._connection_session_id,
                        attacker_ip=self.client_ip,
                        attacker_port=self.client_port,
                        username=self.username,
                        password=password,
                    )
                )
        session_state = self.open_session(self.username, self._connection_session_id)
        if self.pipeline is None:
            return HoneyPTYSession(session_state)
        return HoneyPTYSession(
            session_state,
            runner=self.pipeline.run,
            attacker_ip=self.client_ip,
        )


def _password_for(auth_handler: HoneyAuthHandler, ip: str, username: str) -> str:
    for record in reversed(auth_handler.captured_log):
        if record.ip == ip and record.username == username:
            return record.password or ""
    return ""
