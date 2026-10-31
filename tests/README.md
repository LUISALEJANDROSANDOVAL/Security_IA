Dueño: los cuatro (P1, P2, P3, P4)

Las pruebas de cada paquete las escribe su dueño. Los dobles compartidos están en fakes/ y los mantiene quien implementa ese puerto.

Quien no figura como dueño no edita archivos de esta carpeta.

| Archivo | Responsabilidad |
| --- | --- |
| `ingress/` | P1 — Ingress y VFS |
| `vfs/` | P1 — Ingress y VFS |
| `posix/` | P2 — Emulación POSIX |
| `tarpit/` | P3 — Tarpit y Canaries |
| `canary/` | P3 — Tarpit y Canaries |
| `defense/` | P4 — Defensa y SOC |
| `composition/` | los cuatro (P1, P2, P3, P4). Prueba de punta a punta cuando las cuatro partes existen. |
| `fakes/` | Un doble por puerto. Lo edita el dueño de la implementación real. |
