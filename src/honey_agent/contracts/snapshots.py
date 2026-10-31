"""
src/honey_agent/contracts/snapshots.py
Dueño: los cuatro (P1, P2, P3, P4).
Responsabilidad: SessionSnapshot y VfsView inmutables. P2, P3 y P4 leen estas vistas y no la clase mutable del VFS.
Puede importar: biblioteca estándar y pydantic.
No importar: el resto de honey_agent.
"""

from typing import Dict, List
from pydantic import BaseModel, Field

class VfsEntryView(BaseModel):
    name: str
    is_dir: bool
    size: int
    permissions: int

class SessionSnapshot(BaseModel):
    """Vista inmutable del estado de la sesión para consumo del LLM (P2), Tarpit (P3) y Mitre (P4)."""
    session_id: str = "sess-01"
    username: str = "root"
    hostname: str = "prod-srv-app01"
    cwd: str = "/root"
    env: Dict[str, str] = Field(default_factory=dict)
    command_history: List[str] = Field(default_factory=list)
    visible_files: List[str] = Field(default_factory=list)
