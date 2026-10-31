Dueño: P2 — Emulación POSIX

Emulación de la salida de comandos Linux. Recibe un snapshot inmutable y devuelve stdout, stderr y exit code.

Quien no figura como dueño no edita archivos de esta carpeta.

| Archivo | Responsabilidad |
| --- | --- |
| `emulator.py` | Fachada POSIX que usan el pipeline y las pruebas. |
| `client.py` | Conector agnóstico hacia Ollama, Gemini o vLLM. |
| `prompts.py` | Prompt maestro, sandwich de directivas y salida JSON estricta. |
| `sanitizer.py` | Tapa fugas del modelo con un error de bash. |
| `context_manager.py` | Poda el historial y serializa el snapshot del VFS. |
| `providers/` | Un archivo por proveedor. Añadir un proveedor no modifica el emulador. |
