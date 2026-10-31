Dueño: los cuatro (P1, P2, P3, P4)

Único lugar que instancia clases concretas. Cada programador edita solo su wire_*.py. pipeline.py y main.py se cambian con dos revisores.

Quien no figura como dueño no edita archivos de esta carpeta.

| Archivo | Responsabilidad |
| --- | --- |
| `pipeline.py` | los cuatro (P1, P2, P3, P4). Orden: puntuar, emular, inocular, retardar, actualizar VFS, publicar, aislar. |
| `main.py` | los cuatro (P1, P2, P3, P4). Arranque del proceso. |
| `wire_ingress.py` | P1 — Ingress y VFS. Construye SSH, PTY y VFS. |
| `wire_posix.py` | P2 — Emulación POSIX. Construye el emulador y el proveedor. |
| `wire_deception.py` | P3 — Tarpit y Canaries. Construye tarpit, fábrica y tracker. |
| `wire_defense.py` | P4 — Defensa y SOC. Construye reglas, score, Netfilter y bus. |
