"""
src/honey_agent/ingress/pty_session.py
Dueño: Programador 1 (P1).
Responsabilidad: Terminal PTY virtual: ANSI, CRLF, backspace, Ctrl+C y Ctrl+D.
"""

import asyncssh
from typing import Optional
from honey_agent.vfs.session_state import SessionState

class HoneyPTYSession(asyncssh.SSHServerSession):
    """Maneja el canal PTY interactivo entre el atacante y el SessionState."""

    def __init__(self, session_state: SessionState):
        self.state = session_state
        self._chan: Optional[asyncssh.SSHServerChannel] = None
        self._input_buffer: str = ""
        self._exec_command: Optional[str] = None

    def connection_made(self, chan: asyncssh.SSHServerChannel):
        self._chan = chan

    def pty_requested(self, term_type: str, term_size: tuple, term_modes: dict) -> bool:
        return True

    def shell_requested(self) -> bool:
        return True

    def exec_requested(self, command: str) -> bool:
        """Acepta comandos remotos no interactivos (ej. ssh user@host cmd)."""
        self._exec_command = command
        return True

    def session_started(self):
        """Emite el prompt o ejecuta el comando recibido."""
        if not self._chan:
            return

        if self._exec_command is not None:
            # Modo no interactivo (ejecutar y cerrar)
            handled, stdout, stderr, code = self.state.execute_builtin(self._exec_command)
            if not handled:
                cmd_first = self._exec_command.split()[0] if self._exec_command.split() else ""
                self._chan.write_stderr(f"bash: {cmd_first}: command not found\n")
                self._chan.exit(127)
            else:
                if stdout:
                    self._chan.write(stdout)
                if stderr:
                    self._chan.write_stderr(stderr)
                self._chan.exit(code)
            self._chan.close()
        else:
            # Modo interactivo (shell PTY)
            prompt = self.state.get_prompt()
            self._chan.write(prompt)

    def data_received(self, data: str, datatype: asyncssh.DataType):
        """Procesa caracteres entrantes con emulación de terminal VT100."""
        if not self._chan:
            return

        for char in data:
            # 1. Enter (\r o \n)
            if char in ("\r", "\n"):
                self._chan.write("\r\n")
                cmd = self._input_buffer
                self._input_buffer = ""

                handled, stdout, stderr, code = self.state.execute_builtin(cmd)
                if not handled:
                    cmd_first = cmd.split()[0] if cmd.split() else ""
                    self._chan.write(f"bash: {cmd_first}: command not found\r\n")
                else:
                    if stdout:
                        self._chan.write(stdout.replace("\n", "\r\n"))
                    if stderr:
                        self._chan.write(stderr.replace("\n", "\r\n"))

                if cmd.strip() == "exit":
                    self._chan.exit(code)
                    self._chan.close()
                    return

                self._chan.write(self.state.get_prompt())

            # 2. Backspace (\x08 o \x7f)
            elif char in ("\x08", "\x7f"):
                if len(self._input_buffer) > 0:
                    self._input_buffer = self._input_buffer[:-1]
                    self._chan.write("\b \b")

            # 3. Ctrl+C (\x03)
            elif char == "\x03":
                self._input_buffer = ""
                self._chan.write("^C\r\n")
                self._chan.write(self.state.get_prompt())

            # 4. Ctrl+D (\x04)
            elif char == "\x04":
                if not self._input_buffer:
                    self._chan.write("logout\r\n")
                    self._chan.exit(0)
                    self._chan.close()
                    return

            # 5. Caracteres imprimibles estándar
            elif ord(char) >= 32:
                self._input_buffer += char
                self._chan.write(char)
