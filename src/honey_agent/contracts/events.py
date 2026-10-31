# Dueño: los cuatro (P1, P2, P3, P4)
# Responsabilidad: SessionStartEvent, CommandExecutedEvent, CanaryGeneratedEvent y ContainmentTriggeredEvent (HA-API-06).
# Puede importar: biblioteca estándar y pydantic
# No importar: el resto de honey_agent

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_uuid() -> str:
    return str(uuid4())


class MitreClassificationEvent(BaseModel):
    """Resumen de la clasificación MITRE embebida en eventos."""
    technique_id: str
    tactic: str
    technique_name: str
    confidence: float = 1.0


class TarpitMetricsEvent(BaseModel):
    """Métricas del retardo aplicado por el tarpit."""
    base_delay_ms: float = 0.0
    fatigue_delay_ms: float = 0.0
    jitter_ms: float = 0.0
    total_wait_ms: float = 0.0


class CredentialsUsed(BaseModel):
    username: str
    password: str | None = None
    auth_type: Literal["PASSWORD", "PUBLIC_KEY"] = "PASSWORD"


class GeolocationInfo(BaseModel):
    country: str | None = None
    city: str | None = None
    asn: str | None = None


# --- 1. SessionStartEvent ---
class SessionStartEvent(BaseModel):
    """Emitido por P1 al autenticar una nueva sesión SSH/HTTP."""
    event_id: str = Field(default_factory=_new_uuid)
    event_type: Literal["SESSION_STARTED"] = "SESSION_STARTED"
    timestamp: str = Field(default_factory=_utc_now_iso)
    session_id: str
    protocol: Literal["SSH", "HTTP"] = "SSH"
    attacker_ip: str
    attacker_port: int = 0
    credentials_used: CredentialsUsed
    client_banner: str = ""
    geolocation: GeolocationInfo | None = None


# --- 2. CommandExecutedEvent ---
class CommandExecutedEvent(BaseModel):
    """Emitido tras la ejecución, puntuación y retardo de cada comando."""
    event_id: str = Field(default_factory=_new_uuid)
    event_type: Literal["COMMAND_EXECUTED"] = "COMMAND_EXECUTED"
    timestamp: str = Field(default_factory=_utc_now_iso)
    session_id: str
    attacker_ip: str
    command: str
    working_directory: str = "/root"
    user: str = "root"
    stdout_snippet: str = ""
    exit_code: int = 0
    mitre_classification: MitreClassificationEvent | None = None
    tarpit_metrics: TarpitMetricsEvent | None = None
    threat_score_after_cmd: float = 0.0


# --- 3. CanaryGeneratedEvent ---
class CanaryGeneratedEvent(BaseModel):
    """Emitido por P3 cuando se inocula un token de contra-inteligencia."""
    event_id: str = Field(default_factory=_new_uuid)
    event_type: Literal["CANARY_INJECTED"] = "CANARY_INJECTED"
    timestamp: str = Field(default_factory=_utc_now_iso)
    session_id: str
    attacker_ip: str
    token_type: str
    token_public_id: str
    token_signature_hmac: str
    target_file: str
    alert_destination: str = "SIEM_WEBHOOK_CLOUD_TRAIL"


# --- 4. ContainmentTriggeredEvent ---
class ContainmentTriggeredEvent(BaseModel):
    """Emitido por P4 cuando se despacha el aislamiento en kernel (DROP)."""
    event_id: str = Field(default_factory=_new_uuid)
    event_type: Literal["CONTAINMENT_TRIGGERED"] = "CONTAINMENT_TRIGGERED"
    timestamp: str = Field(default_factory=_utc_now_iso)
    session_id: str
    attacker_ip: str
    trigger_reason: str
    final_threat_score: float = 100.0
    mitigation_action: str = "NETFILTER_IPTABLES_DROP"
    kernel_command: str = ""
    execution_duration_ms: float = 0.0
    status: Literal["CONTAINED_AND_BLOCKED"] = "CONTAINED_AND_BLOCKED"


# Tipo unión para cualquier evento del bus
HoneyAgentEvent = (
    SessionStartEvent
    | CommandExecutedEvent
    | CanaryGeneratedEvent
    | ContainmentTriggeredEvent
)
