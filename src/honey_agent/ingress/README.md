Dueño: P1 — Ingress y VFS

Capa de entrada SSH. Entrega líneas al pipeline y escribe bytes de vuelta. No emula comandos ni decide bloqueos.

Quien no figura como dueño no edita archivos de esta carpeta.

| Archivo | Responsabilidad |
| --- | --- |
| `ssh_server.py` | Handshake AsyncSSH y banner OpenSSH 8.9p1 Ubuntu. |
| `pty_session.py` | PTY virtual: ANSI, Enter, backspace, Ctrl+C y Ctrl+D. |
| `auth.py` | Acepta cualquier credencial y la deja registrada. |
