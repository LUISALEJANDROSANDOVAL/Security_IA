# Dueño: P2 — Emulación POSIX
# Responsabilidad: Añade src al path para que pytest importe honey_agent.
# Puede importar: honey_agent.posix y tests.fakes
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.defense

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
