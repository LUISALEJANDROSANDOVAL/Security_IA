# Dueño: P4 — Defensa y SOC
# Responsabilidad: Aislamiento iptables DROP en menos de 5 ms. Ignora IPs de la lista blanca. Implementa el puerto Isolator.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary, honey_agent.composition

from __future__ import annotations

import asyncio
import logging
import sys
import time
from typing import Iterable

from honey_agent.contracts.ports import Isolator

logger = logging.getLogger("HoneyAgent.Defense.Netfilter")


class NetfilterIsolator(Isolator):
    """Controlador atómico de mitigación en kernel Linux mediante iptables (HA-TDD-02, HA-DEV-09).

    Despacha reglas `iptables -I INPUT -s <IP> -j DROP` en menos de 5 milisegundos.
    Garantiza que ninguna IP perteneciente a la lista blanca sea bloqueada.
    """

    DEFAULT_ALLOWLIST: frozenset[str] = frozenset({
        "127.0.0.1",
        "::1",
        "localhost",
        "0.0.0.0",
    })

    def __init__(
        self,
        allowlist: Iterable[str] | None = None,
        iptables_path: str = "/usr/sbin/iptables",
        dry_run: bool | None = None,
    ) -> None:
        self.allowlist: set[str] = set(self.DEFAULT_ALLOWLIST)
        if allowlist:
            self.allowlist.update(allowlist)

        self.iptables_path = iptables_path
        # En sistemas no-Linux (ej. Windows durante desarrollo), activamos dry_run automáticamente
        self.dry_run = dry_run if dry_run is not None else (sys.platform != "linux")
        self._isolated_ips: set[str] = set()

    def is_isolated(self, ip: str) -> bool:
        """Indica si una IP se encuentra actualmente en la lista de aisladas."""
        return ip in self._isolated_ips

    async def isolate_ip(self, ip: str, reason: str) -> bool:
        """Aplica aislamiento atómico en el kernel mediante iptables en < 5 ms.

        Retorna True si el aislamiento fue aplicado exitosamente,
        False si la IP está en allowlist o si ya estaba bloqueada.
        """
        clean_ip = ip.strip()

        # 1. Verificación estricta de lista blanca
        if clean_ip in self.allowlist:
            logger.warning(
                f"[ALLOWLIST HIT] Intento de bloqueo ignorado para IP protegida: {clean_ip}. Motivo: {reason}"
            )
            return False

        if clean_ip in self._isolated_ips:
            logger.info(f"La IP {clean_ip} ya se encuentra aislada previamente.")
            return True

        start_time = time.perf_counter()
        cmd = ["sudo", self.iptables_path, "-I", "INPUT", "-s", clean_ip, "-j", "DROP"]

        if self.dry_run:
            # Modo simulación para entornos de desarrollo / CI
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self._isolated_ips.add(clean_ip)
            logger.critical(
                f"[CONTAINMENT ACTIVATED (DRY-RUN)] IP {clean_ip} aislada en {elapsed_ms:.2f} ms. Motivo: {reason}"
            )
            return True

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if proc.returncode == 0:
                self._isolated_ips.add(clean_ip)
                logger.critical(
                    f"[CONTAINMENT ACTIVATED] IP {clean_ip} aislada via Netfilter en {elapsed_ms:.2f} ms. Motivo: {reason}"
                )
                return True
            else:
                logger.error(
                    f"Fallo al invocar iptables para {clean_ip} (código {proc.returncode}): {stderr.decode().strip()}"
                )
                return False
        except Exception as ex:
            logger.error(f"Excepción al ejecutar iptables para {clean_ip}: {ex}")
            return False

    async def unisolate_ip(self, ip: str) -> bool:
        """Remueve la regla DROP del kernel para permitir acceso nuevamente."""
        clean_ip = ip.strip()
        if clean_ip not in self._isolated_ips:
            return False

        cmd = ["sudo", self.iptables_path, "-D", "INPUT", "-s", clean_ip, "-j", "DROP"]

        if self.dry_run:
            self._isolated_ips.discard(clean_ip)
            logger.info(f"[CONTAINMENT REMOVED (DRY-RUN)] IP {clean_ip} desbloqueada.")
            return True

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                self._isolated_ips.discard(clean_ip)
                logger.info(f"[CONTAINMENT REMOVED] IP {clean_ip} desbloqueada en iptables.")
                return True
            else:
                logger.error(f"Error al desbloquear {clean_ip}: {stderr.decode().strip()}")
                return False
        except Exception as ex:
            logger.error(f"Excepción al desbloquear {clean_ip}: {ex}")
            return False
