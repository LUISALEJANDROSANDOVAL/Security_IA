# Reglas de revisión

## Propiedad

Cada archivo de `src/honey_agent`, `tests` y `dashboard` empieza con `Dueño` y `Responsabilidad`. No edites el paquete de otro programador.

## Imports

`ingress`, `vfs`, `posix`, `tarpit`, `canary` y `defense` solo importan `honey_agent.contracts`. El ensamble vive en `composition`.

## P3 — Tarpit y Canaries

El retardo es `T_base + 0.65 * log(1 + N) + ruido`, recortado entre 0.02 s y 12 s, y se aplica con `asyncio.sleep`. La clave AWS de canary es `AKIA` + 12 hex HMAC-SHA256 + `CANARY`. El secreto entra por argumento o por `CANARY_SIGNATURE_SECRET`. No copies secretos de la documentación al código.

## Pruebas

Los tests de unidad usan `unittest` y no abren sockets, no llaman a un LLM y no ejecutan `iptables`.
