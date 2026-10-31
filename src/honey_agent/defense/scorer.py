# Dueño: P4 — Defensa y SOC
# Responsabilidad: Threat Score de la sesión con decaimiento temporal y tope 100. Implementa el puerto ThreatScorer.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary, honey_agent.composition

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

from honey_agent.contracts.ports import ThreatScorer
from honey_agent.defense.rules import MitreClassification, classify_command


@dataclass
class _CommandScoreRecord:
    timestamp: float
    base_severity: int
    tactical_weight: float
    tactical_name: str
    is_critical: bool


@dataclass
class _SessionScoreState:
    session_id: str
    records: list[_CommandScoreRecord] = field(default_factory=list)
    has_critical_trigger: bool = False
    last_evaluated_score: float = 0.0
    profile_multiplier: float = 1.0  # 1.0 botnet/script, 1.35 APT/humano


class SessionThreatScorer(ThreatScorer):
    """Calculador de amenaza con decaimiento temporal exponencial (HA-MITRE-04).

    Fórmula:
        S(t) = min(100, sum(w_i * Severity_i * mu * exp(-lambda * (t - t_i))))
    """

    def __init__(
        self,
        decay_lambda: float = 0.0005,
        critical_threshold: float = 80.0,
    ) -> None:
        self.decay_lambda = decay_lambda
        self.critical_threshold = critical_threshold
        self._sessions: dict[str, _SessionScoreState] = {}

    def _get_or_create_session(self, session_id: str) -> _SessionScoreState:
        if session_id not in self._sessions:
            self._sessions[session_id] = _SessionScoreState(session_id=session_id)
        return self._sessions[session_id]

    def score_command(
        self,
        session_id: str,
        command: str,
        timestamp: float | None = None,
    ) -> tuple[float, MitreClassification | None, bool]:
        """Evalúa un comando contra las reglas MITRE y actualiza el score acumulado.

        Retorna:
            (threat_score_actual, mitre_classification, should_isolate)
        """
        now = timestamp if timestamp is not None else time.time()
        session = self._get_or_create_session(session_id)

        # 1. Clasificación heurística (< 1 ms)
        classification = classify_command(command)

        if classification is None:
            # Comando normal (ej: cd, pwd, echo sin riesgo aparente)
            current_score = self.get_score(session_id, now)
            should_isolate = (
                session.has_critical_trigger
                or current_score >= self.critical_threshold
            )
            return current_score, None, should_isolate

        # 2. Registrar comando táctico
        record = _CommandScoreRecord(
            timestamp=now,
            base_severity=classification.base_severity,
            tactical_weight=classification.tactical_weight,
            tactical_name=classification.technique_name,
            is_critical=classification.is_critical,
        )
        session.records.append(record)

        # 3. Trigger crítico directo (ej: curl|bash, /etc/shadow)
        if classification.is_critical:
            session.has_critical_trigger = True
            session.last_evaluated_score = 100.0
            return 100.0, classification, True

        # 4. Cálculo con decaimiento temporal acumulado
        current_score = self.get_score(session_id, now)
        session.last_evaluated_score = current_score
        should_isolate = current_score >= self.critical_threshold

        return current_score, classification, should_isolate

    def get_score(self, session_id: str, current_time: float | None = None) -> float:
        """Calcula el score actual de una sesión aplicando decaimiento."""
        if session_id not in self._sessions:
            return 0.0

        session = self._sessions[session_id]
        if session.has_critical_trigger:
            return 100.0

        now = current_time if current_time is not None else time.time()
        accumulated = 0.0

        for rec in session.records:
            delta_t = max(0.0, now - rec.timestamp)
            # e^(-lambda * delta_t)
            decay = math.exp(-self.decay_lambda * delta_t)
            score_contribution = (
                rec.tactical_weight
                * rec.base_severity
                * session.profile_multiplier
                * decay
            )
            accumulated += score_contribution

        final_score = min(100.0, max(0.0, round(accumulated, 2)))
        session.last_evaluated_score = final_score
        return final_score

    def reset_session(self, session_id: str) -> None:
        """Reinicia el historial de una sesión."""
        self._sessions.pop(session_id, None)
