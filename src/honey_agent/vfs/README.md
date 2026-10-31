Dueño: P1 — Ingress y VFS

Sistema de archivos efímero. Todo el árbol vive en RAM y cada sesión tiene su propia copia.

Quien no figura como dueño no edita archivos de esta carpeta.

| Archivo | Responsabilidad |
| --- | --- |
| `in_memory_tree.py` | mkdir, touch, write, read, unlink y cd sobre inodos en memoria. |
| `session_state.py` | $PWD, $USER, $PATH, entorno e historial de la sesión. |
| `skeleton.py` | Plantilla Ubuntu inicial: /etc, /proc, /var/www, /root. |
