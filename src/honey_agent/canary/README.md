Dueño: P3 — Tarpit y Canaries

Contra-inteligencia. Produce credenciales falsas firmadas y registra que se mostraron.

Quien no figura como dueño no edita archivos de esta carpeta.

| Archivo | Responsabilidad |
| --- | --- |
| `factory.py` | Genera AWS, PostgreSQL, JWT y claves SSH con sello HMAC. |
| `inoculator.py` | Inserta el canary al leer .env o ~/.aws/credentials. |
| `tracker.py` | Guarda el token emitido y avisa al SOC. |
