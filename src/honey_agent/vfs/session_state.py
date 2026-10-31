"""
src/honey_agent/vfs/session_state.py
Dueño: Programador 1 (P1).
Responsabilidad: Estado mutable de sesión ($PWD, variables), builtins de la Parte 1 y exportación de SessionSnapshot.
"""

from typing import Dict, List, Tuple
from honey_agent.vfs.in_memory_tree import VirtualFileSystem
from honey_agent.contracts.snapshots import SessionSnapshot

class SessionState:
    """Mantiene el estado y variables de una sesión interactiva."""

    def __init__(self, vfs: VirtualFileSystem, username: str = "root", session_id: str = "sess-01"):
        self.vfs = vfs
        self.username = username
        self.session_id = session_id
        self.hostname = "prod-srv-app01"
        self.cwd = "/root" if username == "root" else f"/home/{username}"
        self.env: Dict[str, str] = {
            "USER": username,
            "HOME": self.cwd,
            "PWD": self.cwd,
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "SHELL": "/bin/bash",
            "HOSTNAME": self.hostname,
            "TERM": "xterm-256color",
            "SHLVL": "1",
        }
        self.command_history: List[str] = []

    def get_prompt(self) -> str:
        """Retorna el prompt clásico de bash: root@prod-srv-app01:~# """
        symbol = "#" if self.username == "root" else "$"
        display_cwd = "~" if self.cwd == self.env.get("HOME") else self.cwd
        return f"{self.username}@{self.hostname}:{display_cwd}{symbol} "

    def to_snapshot(self) -> SessionSnapshot:
        """Genera una vista inmutable para que P2 (LLM), P3 (Tarpit) y P4 (Mitre) lean el contexto."""
        entries = self.vfs.listdir(self.cwd) or []
        visible = [name for name, _ in entries]
        return SessionSnapshot(
            session_id=self.session_id,
            username=self.username,
            hostname=self.hostname,
            cwd=self.cwd,
            env=dict(self.env),
            command_history=list(self.command_history),
            visible_files=visible
        )

    def execute_builtin(self, cmd_line: str) -> Tuple[bool, str, str, int]:
        """
        Ejecuta comandos builtin directos de la Parte 1.
        Retorna: (is_handled, stdout, stderr, exit_code)
        """
        raw = cmd_line.strip()
        if not raw:
            return True, "", "", 0

        self.command_history.append(raw)
        tokens = raw.split()
        cmd = tokens[0]
        args = tokens[1:]

        if cmd == "pwd":
            return True, f"{self.cwd}\n", "", 0

        elif cmd == "cd":
            target = args[0] if args else self.env.get("HOME", "/root")
            new_path = self.vfs.normalize_path(target, self.cwd)
            node = self.vfs.get_node(new_path)
            if not node:
                return True, "", f"bash: cd: {target}: No such file or directory\n", 1
            if not node.is_dir:
                return True, "", f"bash: cd: {target}: Not a directory\n", 1
            self.cwd = new_path
            self.env["PWD"] = self.cwd
            return True, "", "", 0

        elif cmd == "ls":
            show_all = any(arg in ("-a", "-la", "-al") for arg in args)
            show_long = any(arg in ("-l", "-la", "-al") for arg in args)
            target = next((a for a in args if not a.startswith("-")), ".")
            norm_path = self.vfs.normalize_path(target, self.cwd)
            node = self.vfs.get_node(norm_path)

            if not node:
                return True, "", f"ls: cannot access '{target}': No such file or directory\n", 2
            if not node.is_dir:
                return True, f"{node.name}\n", "", 0

            entries = self.vfs.listdir(norm_path) or []
            if show_long:
                lines = [f"total {len(entries) * 4}"]
                if show_all:
                    lines.append(f"drwxr-xr-x 2 {node.owner} {node.group} 4096 Oct 31 04:00 .")
                    lines.append(f"drwxr-xr-x 2 {node.owner} {node.group} 4096 Oct 31 04:00 ..")
                for name, child in entries:
                    if name.startswith(".") and not show_all:
                        continue
                    prefix = "d" if child.is_dir else "-"
                    perm = "rwxr-xr-x" if child.is_dir else "rw-r--r--"
                    lines.append(
                        f"{prefix}{perm} 1 {child.owner} {child.group} {child.size:>6} Oct 31 04:00 {name}"
                    )
                return True, "\n".join(lines) + "\n", "", 0
            else:
                names = [".", ".."] if show_all else []
                for name, _ in entries:
                    if name.startswith(".") and not show_all:
                        continue
                    names.append(name)
                return True, "  ".join(names) + ("\n" if names else ""), "", 0

        elif cmd == "cat":
            if not args:
                return True, "", "", 0
            out, err = [], []
            for f in args:
                p = self.vfs.normalize_path(f, self.cwd)
                content = self.vfs.read_file(p)
                if content is None:
                    node = self.vfs.get_node(p)
                    if node and node.is_dir:
                        err.append(f"cat: {f}: Is a directory\n")
                    else:
                        err.append(f"cat: {f}: No such file or directory\n")
                else:
                    out.append(content.decode("utf-8", errors="replace"))
            return True, "".join(out), "".join(err), (1 if err else 0)

        elif cmd == "echo":
            joined = " ".join(args)
            if ">>" in joined:
                parts = joined.split(">>", 1)
                text = parts[0].strip().strip('"').strip("'") + "\n"
                dest_path = self.vfs.normalize_path(parts[1].strip(), self.cwd)
                existing = self.vfs.read_file(dest_path) or b""
                self.vfs.write_file(dest_path, existing + text.encode("utf-8"))
                return True, "", "", 0
            elif ">" in joined:
                parts = joined.split(">", 1)
                text = parts[0].strip().strip('"').strip("'") + "\n"
                dest_path = self.vfs.normalize_path(parts[1].strip(), self.cwd)
                self.vfs.write_file(dest_path, text.encode("utf-8"))
                return True, "", "", 0
            clean = joined.strip('"').strip("'") + "\n"
            return True, clean, "", 0

        elif cmd == "touch":
            for f in args:
                p = self.vfs.normalize_path(f, self.cwd)
                if not self.vfs.get_node(p):
                    self.vfs.write_file(p, b"")
            return True, "", "", 0

        elif cmd == "mkdir":
            for d in args:
                p = self.vfs.normalize_path(d, self.cwd)
                self.vfs.mkdir(p)
            return True, "", "", 0

        elif cmd == "whoami":
            return True, f"{self.username}\n", "", 0

        elif cmd == "id":
            uid = 0 if self.username == "root" else 1000
            return True, f"uid={uid}({self.username}) gid={uid}({self.username}) groups={uid}({self.username})\n", "", 0

        elif cmd == "exit":
            return True, "logout\n", "", 0

        # No es builtin: en la Parte 2 se derivará al LLM
        return False, "", "", 0
