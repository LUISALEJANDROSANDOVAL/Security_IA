# Dueño: Programador 1 (P1).
# Responsabilidad: Terminal PTY virtual: ANSI, CRLF, backspace, Ctrl+C y Ctrl+D.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary, honey_agent.defense

import asyncio
import logging
from typing import Optional

import asyncssh

from honey_agent.contracts.ports import ShellSession

logger = logging.getLogger("HoneyAgent.PTY")

class HoneyPTYSession(asyncssh.SSHServerSession):
    """Maneja el canal PTY interactivo entre el atacante y el SessionState."""

    def __init__(self, session_state: ShellSession, runner=None, attacker_ip: str = "127.0.0.1"):
        self.state = session_state
        self.runner = runner
        self.attacker_ip = attacker_ip
        self._chan: Optional[asyncssh.SSHServerChannel] = None
        self._input_buffer: str = ""
        self._exec_command: Optional[str] = None
        self._lock = asyncio.Lock()

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

        if self._exec_command is not None and self.runner is not None:
            asyncio.get_running_loop().create_task(self._exec_and_close(self._exec_command))
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

    async def _exec_and_close(self, command: str) -> None:
        try:
            outcome = await self.runner(self.state, command, self.attacker_ip)
            self._write_outcome(outcome.stdout, outcome.stderr, crlf=False)
            self._chan.exit(outcome.exit_code)
        except Exception:
            logger.exception("el comando no interactivo falló")
            self._chan.write_stderr("bash: error\n")
            self._chan.exit(1)
        finally:
            self._chan.close()

    async def _run_interactive(self, command: str) -> None:
        async with self._lock:
            if not self._chan:
                return
            try:
                outcome = await self.runner(self.state, command, self.attacker_ip)
            except Exception:
                logger.exception("el comando interactivo falló")
                self._chan.write("bash: error\r\n")
                self._chan.write(self.state.get_prompt())
                return
            self._write_outcome(outcome.stdout, outcome.stderr, crlf=True)
            if command.strip() == "exit":
                self._chan.exit(outcome.exit_code)
                self._chan.close()
                return
            self._chan.write(self.state.get_prompt())

    def _write_outcome(self, stdout: str, stderr: str, *, crlf: bool) -> None:
        if stdout:
            text = stdout.replace("\n", "\r\n") if crlf else stdout
            self._chan.write(text)
        if stderr:
            text = stderr.replace("\n", "\r\n") if crlf else stderr
            self._chan.write_stderr(text)

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

                if self.runner is not None:
                    asyncio.get_running_loop().create_task(self._run_interactive(cmd))
                    continue

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
