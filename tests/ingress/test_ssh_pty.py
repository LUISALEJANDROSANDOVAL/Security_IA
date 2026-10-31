# Dueño: Programador 1 (P1).
# Responsabilidad: Validación de la captura de auth y del ensamble de sesión, sin red.
# Puede importar: honey_agent.composition.wire_ingress y honey_agent.ingress
# No importar: sockets, un LLM real o iptables

import unittest

from honey_agent.composition.wire_ingress import bind_ssh_server
from honey_agent.ingress.auth import HoneyAuthHandler
from honey_agent.ingress.pty_session import HoneyPTYSession
from honey_agent.ingress.ssh_server import HoneySSHServer
from honey_agent.vfs.in_memory_tree import VirtualFileSystem
from honey_agent.vfs.skeleton import populate_ubuntu_skeleton


class _FakeSession:
    def __init__(self) -> None:
        self.vfs = object()

    def get_prompt(self) -> str:
        return "root@prod-srv-app01:~# "

    def execute_builtin(self, cmd_line: str) -> tuple[bool, str, str, int]:
        return True, cmd_line, "", 0

    def to_snapshot(self):
        raise AssertionError("esta prueba no exporta snapshot")


class AuthCaptureTests(unittest.TestCase):
    def test_password_is_recorded(self) -> None:
        auth = HoneyAuthHandler()
        self.assertTrue(auth.authenticate_password("192.168.1.50", 45678, "admin", "p4ssw0rd!"))
        self.assertEqual(len(auth.captured_log), 1)
        record = auth.captured_log[0]
        self.assertEqual(record.ip, "192.168.1.50")
        self.assertEqual(record.username, "admin")
        self.assertEqual(record.password, "p4ssw0rd!")


class SSHServerAssemblyTests(unittest.TestCase):
    def test_session_requested_uses_the_injected_opener(self) -> None:
        opened: list[tuple[str, str]] = []

        def open_session(username: str, session_id: str) -> _FakeSession:
            opened.append((username, session_id))
            return _FakeSession()

        server = HoneySSHServer(HoneyAuthHandler(), open_session)
        server.username = "root"
        session = server.session_requested()
        self.assertEqual(opened, [("root", "sess-01")])
        self.assertIsInstance(session, HoneyPTYSession)

    def test_one_connection_reuses_the_cloned_tree(self) -> None:
        master = VirtualFileSystem()
        populate_ubuntu_skeleton(master)
        server = bind_ssh_server(master, HoneyAuthHandler())
        server.username = "root"
        first = server.session_requested()
        second = server.session_requested()
        self.assertIs(first.state.vfs, second.state.vfs)
        self.assertIsNot(first.state.vfs, master)


if __name__ == "__main__":
    unittest.main()
