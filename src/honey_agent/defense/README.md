Dueño: P4 — Defensa y SOC

Detección, puntaje, aislamiento y publicación de eventos. El panel visual está en dashboard/.

Quien no figura como dueño no edita archivos de esta carpeta.

| Archivo | Responsabilidad |
| --- | --- |
| `rules.py` | Mapeo del comando a técnicas MITRE ATT&CK. |
| `scorer.py` | Threat Score acumulado con decaimiento temporal. |
| `netfilter.py` | DROP de la IP en el kernel, con lista blanca. |
| `event_bus.py` | Publica los cuatro eventos del contrato. |
