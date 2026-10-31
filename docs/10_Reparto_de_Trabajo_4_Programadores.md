# Reparto de carpetas entre 4 programadores

Dueño: los cuatro (P1, P2, P3, P4). Responsabilidad: asignar cada carpeta y fijar la regla de imports.

Cada programador edita solo su paquete. El trabajo se cruza en `src/honey_agent/contracts/` y en `src/honey_agent/composition/pipeline.py`. El dueño y la responsabilidad están en las primeras líneas de cada archivo.

## Camino rápido

1. Abre la carpeta de tu rol en la tabla de abajo.
2. Lee el bloque `Dueño` / `Responsabilidad` al inicio del archivo antes de escribir código.
3. Implementa contra los puertos de `contracts/ports.py`. Tu paquete importa `honey_agent.contracts` y no importa el paquete de otro programador.
4. Deja el ensamble en tu `composition/wire_*.py`. El orden del flujo vive en `pipeline.py` y se cambia con acuerdo de dos programadores.
5. Cierra tu parte cuando se cumple el criterio de la misma tabla.

## Quién se encarga de cada carpeta

| Programador | Carpetas | Criterio de cierre | Documento de la parte |
| --- | --- | --- | --- |
| **P1 — Ingress y VFS** | `src/honey_agent/ingress/`, `src/honey_agent/vfs/`, `tests/ingress/`, `tests/vfs/`, `tests/fakes/filesystem.py` | Un cliente SSH entra, ve `root@prod-srv-app01:~#`, `pwd` / `cd` / `echo` / `cat` persisten en la sesión y el host no escribe en disco | [HA-DEV-09, Parte 1](09_Plan_de_Implementacion_y_Construccion_en_4_Fases.md) |
| **P2 — Emulación POSIX** | `src/honey_agent/posix/`, `tests/posix/`, `tests/fakes/emulator.py` | `uname -a`, `ps -ef`, tuberías y un intento de jailbreak responden como bash, sin delatar al modelo | [HA-DEV-09, Parte 2](09_Plan_de_Implementacion_y_Construccion_en_4_Fases.md) y [HA-PROMPT-05](05_Ingenieria_de_Prompts_y_Seguridad_Adversaria.md) |
| **P3 — Tarpit y Canaries** | `src/honey_agent/tarpit/`, `src/honey_agent/canary/`, `tests/tarpit/`, `tests/canary/`, `tests/fakes/tarpit.py`, `tests/fakes/canary.py` | Un comando trivial responde en menos de 50 ms, una búsqueda pesada retiene la sesión y `cat /var/www/html/.env` muestra un canary firmado y registrado | [HA-DEV-09, Parte 3](09_Plan_de_Implementacion_y_Construccion_en_4_Fases.md) |
| **P4 — Defensa y SOC** | `src/honey_agent/defense/`, `dashboard/`, `tests/defense/`, `tests/fakes/defense.py` | `curl \| bash` lleva el Threat Score a 100, el DROP sale en menos de 5 ms y el panel marca la sesión contenida | [HA-DEV-09, Parte 4](09_Plan_de_Implementacion_y_Construccion_en_4_Fases.md), [HA-MITRE-04](04_Matriz_MITRE_ATTACK_y_Motor_Heuristico.md) y [HA-API-06](06_Especificacion_de_API_y_Modelos_de_Datos.md) |
| **Los cuatro** | `src/honey_agent/contracts/`, `composition/pipeline.py`, `composition/main.py`, `tests/composition/` | Un cambio de firma lleva dos revisores. El flujo acordado no se reescribe desde un paquete concreto | [HA-API-06](06_Especificacion_de_API_y_Modelos_de_Datos.md) |

## Regla para no pisarse

| Paquete | Puede importar | No importa |
| --- | --- | --- |
| `contracts` | Biblioteca estándar y pydantic | El resto de `honey_agent` |
| `ingress`, `vfs`, `posix`, `tarpit`, `canary`, `defense` | `honey_agent.contracts` | El paquete de otro programador y `composition` |
| `composition` | Todos los paquetes concretos | — |
| `dashboard` | Eventos ya publicados (Redis / WebSocket de HA-API-06) | `defense`, `ingress`, `vfs`, `posix` |

P2 recibe un `SessionSnapshot`, no la clase del VFS. P3 devuelve el texto inoculado y el retardo. P4 devuelve el puntaje y, si corresponde, aísla la IP. El estado mutable de la sesión lo guarda P1.

Orden dentro de `pipeline.py`: puntuar, emular, inocular, retardar, aplicar el cambio al VFS, publicar el evento, aislar si el score cruza el umbral.

## Archivos por programador

### P1 — Ingress y VFS

| Archivo | Responsabilidad |
| --- | --- |
| `ingress/ssh_server.py` | Servidor AsyncSSH, banner `SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.4` |
| `ingress/pty_session.py` | PTY virtual: ANSI, Enter, backspace, Ctrl+C y Ctrl+D |
| `ingress/auth.py` | Aceptar cualquier credencial y dejarla registrada |
| `vfs/in_memory_tree.py` | Árbol en RAM: mkdir, touch, write, read, unlink, cd, copia por sesión |
| `vfs/session_state.py` | `$PWD`, `$USER`, `$PATH`, entorno e historial |
| `vfs/skeleton.py` | Plantilla Ubuntu (`/etc`, `/proc`, `/var/www`) sin tocar el disco del host |
| `composition/wire_ingress.py` | Construye el servidor y el VFS e inyecta los puertos |

### P2 — Emulación POSIX

| Archivo | Responsabilidad |
| --- | --- |
| `posix/emulator.py` | Fachada: snapshot + comando → stdout, stderr y exit code |
| `posix/client.py` | Conector agnóstico (Ollama, Gemini, vLLM) |
| `posix/prompts.py` | Prompt maestro POSIX y salida JSON estricta |
| `posix/sanitizer.py` | Encapsula la entrada y cambia una fuga del modelo por un error de bash |
| `posix/context_manager.py` | Poda el historial y serializa el VFS para el prompt |
| `posix/providers/ollama.py` | Proveedor local |
| `posix/providers/gemini.py` | Proveedor Gemini |
| `composition/wire_posix.py` | Elige el proveedor e inyecta el emulador |

### P3 — Tarpit y Canaries

| Archivo | Responsabilidad |
| --- | --- |
| `tarpit/engine.py` | Retardo `T_base + α·log(1+N) + ruido`, con `asyncio.sleep` |
| `tarpit/classifier.py` | Clasifica el comando en trivial, medio o pesado |
| `canary/factory.py` | Tokens HMAC: AWS, PostgreSQL, JWT y claves SSH |
| `canary/inoculator.py` | Intercepta lecturas de `.env` y `~/.aws/credentials` |
| `canary/tracker.py` | Registra el canary y avisa al SOC |
| `composition/wire_deception.py` | Inyecta tarpit e inoculador |

### P4 — Defensa y SOC

| Archivo | Responsabilidad |
| --- | --- |
| `defense/rules.py` | Reglas que mapean el comando a técnicas ATT&CK en menos de 1 ms |
| `defense/scorer.py` | Threat Score con decaimiento temporal, tope 100 |
| `defense/netfilter.py` | `iptables DROP` con lista blanca, en menos de 5 ms |
| `defense/event_bus.py` | Publica los cuatro eventos del contrato |
| `dashboard/app.py` | Panel Streamlit: score, matriz y feed en vivo |
| `dashboard/components/` | Piezas visuales del panel |
| `composition/wire_defense.py` | Inyecta scorer, aislador y bus |

### Los cuatro — contrato y ensamble

| Archivo | Responsabilidad |
| --- | --- |
| `contracts/ports.py` | Puertos: `FileSystem`, `ShellSession`, `ShellEmulator`, `LanguageModel`, `Tarpit`, `CanarySource`, `ThreatScorer`, `Isolator`, `EventBus` |
| `contracts/events.py` | `SessionStartEvent`, `CommandExecutedEvent`, `CanaryGeneratedEvent`, `ContainmentTriggeredEvent` |
| `contracts/snapshots.py` | `SessionSnapshot` y `VfsView`, inmutables |
| `composition/pipeline.py` | Único flujo de un comando |
| `composition/main.py` | Arranque del proceso |
| `.env.example` | Plantilla de secretos y puertos. Cada quien completa las variables de su bloque; `.env` no se versiona |

## Encabezado de un archivo nuevo

Las cuatro primeras líneas se mantienen. Ejemplo:

```python
# Dueño: P2 — Emulación POSIX
# Responsabilidad: una frase con el resultado que produce este archivo.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.tarpit, honey_agent.canary, honey_agent.defense, honey_agent.composition
```

Una carpeta nueva lleva un `README.md` cuya primera línea es `Dueño: ...`.

## Checklist de integración

- [ ] Tu paquete no importa el paquete de otro programador.
- [ ] Tu `wire_*.py` es el único archivo de ensamble que tocaste.
- [ ] Tus pruebas viven en `tests/<tu-paquete>/` y usan `tests/fakes/`.
- [ ] Un cambio en `contracts/` o en `pipeline.py` tiene dos revisores.
- [ ] El recorrido de [HA-TEST-07](07_Playbook_de_Pruebas_y_Simulacion_Red_Team.md) pasa cuando las cuatro partes están ensambladas.

## Siguiente paso

Implementar la Parte 1, 2, 3 o 4 del [plan de construcción](09_Plan_de_Implementacion_y_Construccion_en_4_Fases.md) dentro de la carpeta asignada, sin mover módulos de sitio.
