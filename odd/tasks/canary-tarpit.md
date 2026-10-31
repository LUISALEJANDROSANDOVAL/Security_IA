# Canary y tarpit

Objetivo: implementar el retardo cognitivo y los canary tokens de P3 en `feat/canary-tarpit`.
Entrega: `ask-on-risk`. Pronóstico de líneas de autor: unas 620. El tope orientativo es 400; antes de pasarlo hay que elegir cadena.
Runner: no hay pytest en el repositorio. Cada tarea deja el caso en rojo y luego en verde cuando exista un runner ejecutable. Hasta entonces el chequeo es el de la spec, no un resultado inventado.

## Specs

S1. El usuario fijó el alcance: "mi responsabilidad es el tarpit y canary".

S2. DoD 3, tiempo, texto del plan: "El tiempo de respuesta escala de forma orgánica: comandos iniciales responden en $<50\text{ ms}$, mientras búsquedas masivas retienen al usuario durante varios segundos sin desconectar el socket SSH."

S3. DoD 3, canary, texto del plan: "Al ejecutar `cat /var/www/html/.env`, la terminal muestra credenciales sintéticas que quedan registradas en el almacén de telemetría de Honey-Agent."

S4. Playbook, texto del caso: `assert "AWS_ACCESS_KEY_ID" in output` y `assert "CANARY" in output` para `cat /var/www/html/.env`.

S5. Playbook, texto del caso: `find / -name '*secret*' -type f` cumple `assert elapsed >= 2.5`.

S6. Fórmula del plan: `T_espera = T_base(cmd) + α · log(1 + N_interacciones) + N(0, σ²)`, con `asyncio.sleep`, α = 0.65, σ = 0.20 y tope 12 s. Bases: trivial 0.05 s (`whoami`, `id`, `pwd`), medio 0.35 s (`ps aux`, `netstat`, `ls -la`), pesado 3.50 s a 7.00 s (`find /`, `grep -r`, `tar`, `make`).

S7. Firma del documento de prompts: HMAC-SHA256 del payload `"{attacker_ip}:{session_id}:{timestamp}"`, access key `AKIA` + 12 hex de la firma en mayúsculas + `CANARY`. El secreto sale de `CANARY_SIGNATURE_SECRET`, no del ejemplo del documento.

S8. Inoculación según el archivo leído: `/var/www/html/.env` (PostgreSQL y AWS), `~/.bash_history`, `~/.ssh/id_rsa`, `/etc/mysql/my.cnf`, `/etc/hosts` (`vault-internal.corp.canary.domain`). También `~/.aws/credentials`, `env` y `history`, como dice la arquitectura.

S9. Evento al emitir un canary, tipo `CANARY_TOKEN_INOCULATED`, con `session_id`, `attacker_ip`, `token_type`, `token_identifier`, `injected_in_command` y `destination_asset`.

S10. Orden dentro del flujo ya aceptado: P2 entrega stdout, stderr y exit code; P3 inocula si el comando busca secretos; P3 espera el retardo; después salen los bytes. P3 no abre SSH, no llama al modelo y no ejecuta iptables.

## Tasks

- T1 | S2 S5 S6 | delegated | done | commit: 9934b7c — clasificador y motor de retardo en `tarpit/classifier.py` y `tarpit/engine.py`. Runner local ausente (python y py no están). Revisión GGA del commit: PASSED. Tensión: S6 fija 0.05 s y S2 pide menos de 50 ms; el test afirma 0.05 exacto.
- T2 | S4 S7 | delegated | done | commit: 1732ba3 — fábrica HMAC en `canary/factory.py`. Runner local ausente. Revisión GGA del commit: PASSED.
- T3 | S3 S4 S8 | inline | pending | commit: none — inoculador en `canary/inoculator.py`. Depende de T2.
- T4 | S3 S9 | inline | pending | commit: none — registro en `canary/tracker.py`. Depende de T3.
- T5 | S10 | inline | pending | commit: none — ensamble en `composition/wire_deception.py`. Depende de T1–T4.

## Log

L1. 2026-10-31. "segun los docs que debemos hacer con el canary y tarpit"

L2. 2026-10-31. "ok divive por partes  mi responsabilidad es el tarpit y canary empieza con el analisis de los docs el objetivo del proyecto completo y la parte del tarpit y canary empieza con el flujo completo"

L3. 2026-10-31. "ok crea las tareas para empezar a hacer"

L4. 2026-10-31. Análisis del flujo completo entregado en la conversación, sin cambios de código. Siguiente tarea pendiente: T1.

L6. 2026-10-31. T1 cerrada en 9934b7c. T2 cerrada en 1732ba3. Los unittest no se ejecutaron: no hay intérprete Python. Siguiente tarea: T3.

L5. 2026-10-31. Espejo Engram pendiente. `security_ia` no está registrado; un guardado automático cayó en el proyecto `usuario` (observación 47) y no vale como espejo de este repositorio.
