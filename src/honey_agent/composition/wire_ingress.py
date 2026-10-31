# Dueño: Programador 1 (P1).
# Responsabilidad: Ensamble y arranque del servidor SSH con VFS en RAM para la Parte 1.
# Puede importar: honey_agent.ingress, honey_agent.vfs y honey_agent.contracts
# No importar: llamadas directas al LLM

import asyncio
import logging

import asyncssh

from honey_agent.ingress.auth import HoneyAuthHandler
from honey_agent.ingress.ssh_server import HoneySSHServer
from honey_agent.vfs.in_memory_tree import VirtualFileSystem
from honey_agent.vfs.session_state import SessionState
from honey_agent.vfs.skeleton import populate_ubuntu_skeleton

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("HoneyAgent.WireIngress")

def bind_ssh_server(master_vfs: VirtualFileSystem, auth_handler: HoneyAuthHandler, pipeline=None):
    """Una conexión clona el VFS una vez y reutiliza ese árbol en cada canal."""
    shared: dict[str, VirtualFileSystem | None] = {"vfs": None}

    def open_session(username: str, session_id: str) -> SessionState:
        if shared["vfs"] is None:
            shared["vfs"] = master_vfs.clone()
        return SessionState(vfs=shared["vfs"], username=username, session_id=session_id)

    return HoneySSHServer(auth_handler=auth_handler, open_session=open_session, pipeline=pipeline)


async def start_ingress(port: int = 2222, host: str = "0.0.0.0", pipeline=None):
    """Inicializa el VFS maestro y arranca el listener SSH."""
    master_vfs = VirtualFileSystem()
    populate_ubuntu_skeleton(master_vfs)
    logger.info("VFS Maestro en RAM inicializado con plantilla canónica Ubuntu 22.04 LTS.")

    auth_handler = HoneyAuthHandler()
    host_key = asyncssh.generate_private_key("ssh-rsa", key_size=2048)

    server = await asyncssh.create_server(
        lambda: bind_ssh_server(master_vfs, auth_handler, pipeline),
        host=host,
        port=port,
        server_host_keys=[host_key],
        server_version="OpenSSH_8.9p1 Ubuntu-3ubuntu0.4",
        encoding="utf-8"
    )

    logger.info(f"===> [HONEY-AGENT PARTE 1 ACTIVO] <===")
    logger.info(f"Escuchando en {host}:{port} | Banner: OpenSSH_8.9p1 Ubuntu-3ubuntu0.4")
    logger.info(f"Para conectarse: ssh root@127.0.0.1 -p {port}")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(start_ingress(port=2222))
    except (KeyboardInterrupt, SystemExit):
        logger.info("Servidor detenido manualmente.")
