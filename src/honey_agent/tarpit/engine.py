# Dueño: P3 — Tarpit y Canaries
# Responsabilidad: Retardo T_base + α·log(1+N) + ruido gaussiano, aplicado con asyncio.sleep. Implementa el puerto Tarpit.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.canary, honey_agent.defense, honey_agent.composition

import asyncio
import math
import random


class CognitiveTarpit:
    def __init__(self, alpha=0.65, sigma=0.20, max_delay=12.0, sleep=None, noise=None):
        self.alpha = alpha
        self.sigma = sigma
        self.max_delay = max_delay
        self._sleep = asyncio.sleep if sleep is None else sleep
        self._noise = noise

    def compute_delay(self, base_delay, interaction_count) -> float:
        fatigue = self.alpha * math.log(1 + interaction_count)
        noise_value = self._noise() if self._noise else random.gauss(0, self.sigma)
        total = base_delay + fatigue + noise_value
        return max(0.02, min(self.max_delay, total))

    async def apply_delay(self, base_delay, interaction_count) -> float:
        delay = self.compute_delay(base_delay, interaction_count)
        await self._sleep(delay)
        return delay
