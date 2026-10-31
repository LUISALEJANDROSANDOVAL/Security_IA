Dueño: los cuatro (P1, P2, P3, P4)

Dobles de los puertos. Quien prueba otro paquete los importa y no los modifica.

Quien no figura como dueño no edita archivos de esta carpeta.

| Archivo | Responsabilidad |
| --- | --- |
| `filesystem.py` | P1 — Ingress y VFS. Doble de FileSystem. |
| `emulator.py` | P2 — Emulación POSIX. Doble de ShellEmulator y LanguageModel. |
| `tarpit.py` | P3 — Tarpit y Canaries. Doble de Tarpit. |
| `canary.py` | P3 — Tarpit y Canaries. Doble de CanarySource. |
| `defense.py` | P4 — Defensa y SOC. Dobles de ThreatScorer, Isolator y EventBus. |
