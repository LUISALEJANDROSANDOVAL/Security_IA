Dueño: los cuatro (P1, P2, P3, P4)

Mapa del paquete. Cada subcarpeta tiene un solo dueño. La regla de imports está en docs/10_Reparto_de_Trabajo_4_Programadores.md.

Quien no figura como dueño no edita archivos de esta carpeta.

| Archivo | Responsabilidad |
| --- | --- |
| `contracts/` | los cuatro (P1, P2, P3, P4). Puertos, eventos y snapshots. |
| `ingress/` | P1 — Ingress y VFS. SSH y PTY. |
| `vfs/` | P1 — Ingress y VFS. Sistema de archivos en RAM. |
| `posix/` | P2 — Emulación POSIX. Emulación de comandos. |
| `tarpit/` | P3 — Tarpit y Canaries. Retardo probabilístico. |
| `canary/` | P3 — Tarpit y Canaries. Tokens firmados. |
| `defense/` | P4 — Defensa y SOC. MITRE, score, Netfilter y bus. |
| `composition/` | Ensamble. Cada wire_*.py tiene un dueño; pipeline.py y main.py son de los cuatro. |
