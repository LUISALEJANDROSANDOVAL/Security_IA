"""
src/honey_agent/ingress/auth.py
Dueño: Programador 1 (P1).
Responsabilidad: Captura y auditoría de credenciales del atacante.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger("HoneyAgent.Auth")

@dataclass
class CapturedCredentials:
    ip: str
    port: int
    username: str
    password: Optional[str] = None
    auth_type: str = "password"

class HoneyAuthHandler:
    """Gestiona la política permisiva de autenticación de Honey-Agent."""

    def __init__(self):
        self.captured_log: List[CapturedCredentials] = []

    def authenticate_password(self, ip: str, port: int, username: str, password: str) -> bool:
        """Registra las credenciales enviadas y siempre retorna True (permisivo)."""
        record = CapturedCredentials(
            ip=ip, port=port, username=username, password=password, auth_type="password"
        )
        self.captured_log.append(record)
        logger.warning(
            f"[CREDENCIAL CAPTURADA] Host: {ip}:{port} | User: '{username}' | Pass: '{password}'"
        )
        return True
