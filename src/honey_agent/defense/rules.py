# Dueño: P4 — Defensa y SOC
# Responsabilidad: Reglas que clasifican cada comando en técnicas ATT&CK (T1082, T1033, T1003, T1059 y las de HA-MITRE-04) en menos de 1 ms.
# Puede importar: honey_agent.contracts
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary, honey_agent.composition

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass(frozen=True)
class MitreClassification:
    """Resultado estructurado del análisis heurístico de un comando."""
    rule_id: str
    technique_id: str
    tactic: str
    technique_name: str
    base_severity: int          # 1 a 100
    tactical_weight: float      # Multiplicador táctico (1.0 a 4.0)
    is_critical: bool           # Dispara contención/aislamiento inmediato
    tarpit_base_delay: float    # Retardo sugerido en segundos


@dataclass(frozen=True)
class _RuleDefinition:
    rule_id: str
    technique_id: str
    tactic: str
    technique_name: str
    pattern: Pattern[str]
    base_severity: int
    tactical_weight: float
    is_critical: bool
    tarpit_base_delay: float


# Compilación de las 17 reglas heurísticas MITRE ATT&CK Enterprise (HA-MITRE-04)
# Optimizadas para evaluación determinística de sub-milisegundo (< 1 ms).
RULES: tuple[_RuleDefinition, ...] = (
    # --- Triggers Críticos de Ejecución y Ofuscación (Evaluados primero) ---
    _RuleDefinition(
        rule_id="RULE_EXECUTION_PIPE_BASH",
        technique_id="T1059.001",
        tactic="Execution",
        technique_name="Command & Scripting: Unix Shell",
        pattern=re.compile(
            r"(curl|wget)\s+[^|]+\|\s*(ba|z)?sh\b|"
            r"(python(\d(\.\d+)?)?|perl|ruby)\s+-c\s+.*(socket|pty|subprocess|exec)\b|"
            r"(bash|sh)\s+-i\s+>&?\s*/dev/tcp/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d+\b|"
            r"nc(\.traditional|\.openbsd)?\s+-[a-zA-Z]*e\s+/bin/(ba)?sh\b",
            re.IGNORECASE,
        ),
        base_severity=100,
        tactical_weight=4.0,
        is_critical=True,
        tarpit_base_delay=4.00,
    ),
    _RuleDefinition(
        rule_id="RULE_OBFUSCATION_BASE64",
        technique_id="T1027",
        tactic="Defense Evasion",
        technique_name="Obfuscated / Encoded Commands",
        pattern=re.compile(
            r"(base64\s+-[a-zA-Z]*d|openssl\s+enc\s+-[a-zA-Z]*d|xxd\s+-[a-zA-Z]*r).*\|\s*(ba|z)?sh\b",
            re.IGNORECASE,
        ),
        base_severity=95,
        tactical_weight=3.8,
        is_critical=True,
        tarpit_base_delay=3.00,
    ),
    _RuleDefinition(
        rule_id="RULE_CREDENTIAL_SHADOW",
        technique_id="T1003",
        tactic="Credential Access",
        technique_name="OS Credential Dumping",
        pattern=re.compile(
            r"\b(cat|less|more|head|tail|grep|awk|strings|unshadow)\s+.*(/etc/shadow|/etc/gshadow|/dev/mem)\b",
            re.IGNORECASE,
        ),
        base_severity=95,
        tactical_weight=3.5,
        is_critical=True,
        tarpit_base_delay=2.50,
    ),

    # --- Acceso a Credenciales & Archivos Sensibles ---
    _RuleDefinition(
        rule_id="RULE_CREDENTIAL_SSH_KEYS",
        technique_id="T1552.004",
        tactic="Credential Access",
        technique_name="Private Keys Discovery",
        pattern=re.compile(
            r"\b(cat|cp|scp|find|grep|head|tail)\b.*((\.ssh/)?id_rsa|(\.ssh/)?id_ed25519|\.pem|\.key|\.ppk)\b",
            re.IGNORECASE,
        ),
        base_severity=85,
        tactical_weight=3.0,
        is_critical=False,
        tarpit_base_delay=1.50,
    ),
    _RuleDefinition(
        rule_id="RULE_CREDENTIAL_ENV",
        technique_id="T1552.001",
        tactic="Credential Access",
        technique_name="Credentials in Files",
        pattern=re.compile(
            r"\b(cat|grep|strings|tail|head)\b.*(\.env|\.credentials|wp-config\.php|database\.yml|settings\.py)\b",
            re.IGNORECASE,
        ),
        base_severity=70,
        tactical_weight=2.5,
        is_critical=False,
        tarpit_base_delay=1.20,
    ),

    # --- Persistencia y Creación de Cuentas ---
    _RuleDefinition(
        rule_id="RULE_PERSISTENCE_CRON",
        technique_id="T1053.003",
        tactic="Persistence",
        technique_name="Scheduled Task: Cron",
        pattern=re.compile(
            r"\b(crontab\s+-[eul]|/etc/cron\.(d|daily|hourly|monthly|weekly)|/etc/crontab)\b",
            re.IGNORECASE,
        ),
        base_severity=85,
        tactical_weight=3.2,
        is_critical=False,
        tarpit_base_delay=1.50,
    ),
    _RuleDefinition(
        rule_id="RULE_PERSISTENCE_ACCOUNT",
        technique_id="T1136.001",
        tactic="Persistence",
        technique_name="Create Account: Local Account",
        pattern=re.compile(
            r"\b(useradd|adduser|usermod\s+-[a-zA-Z]*G\s+(sudo|wheel|admin))\b",
            re.IGNORECASE,
        ),
        base_severity=85,
        tactical_weight=3.2,
        is_critical=False,
        tarpit_base_delay=1.50,
    ),

    # --- Escalada de Privilegios & Evasión ---
    _RuleDefinition(
        rule_id="RULE_PRIVILEGE_SUDO",
        technique_id="T1548.003",
        tactic="Privilege Escalation",
        technique_name="Sudo and Sudo Caching",
        pattern=re.compile(
            r"^\s*sudo\s+(-[ls]|su\b|/bin/(ba)?sh|passwd\b)",
            re.IGNORECASE,
        ),
        base_severity=75,
        tactical_weight=2.5,
        is_critical=False,
        tarpit_base_delay=1.20,
    ),
    _RuleDefinition(
        rule_id="RULE_DEFENSE_EVASION_LOGS",
        technique_id="T1070.004",
        tactic="Defense Evasion",
        technique_name="File Deletion / Indicator Removal",
        pattern=re.compile(
            r"\b(rm|shred|truncate)\s+(-[rf]+\s+)?(/var/log/|~/\.bash_history)\b|"
            r"history\s+-[a-zA-Z]*c\b|unset\s+HISTFILE\b",
            re.IGNORECASE,
        ),
        base_severity=80,
        tactical_weight=3.0,
        is_critical=False,
        tarpit_base_delay=0.80,
    ),

    # --- Movimiento Lateral & Transferencia C2 ---
    _RuleDefinition(
        rule_id="RULE_LATERAL_SSH",
        technique_id="T1021.004",
        tactic="Lateral Movement",
        technique_name="SSH Pivot / Remote Services",
        pattern=re.compile(
            r"^\s*(ssh(\s+-[a-zA-Z0-9]+)*\s+[a-zA-Z0-9_\-]+@|scp\s+|rsync\s+.*@)",
            re.IGNORECASE,
        ),
        base_severity=80,
        tactical_weight=3.0,
        is_critical=False,
        tarpit_base_delay=2.00,
    ),
    _RuleDefinition(
        rule_id="RULE_INGRESS_TRANSFER",
        technique_id="T1105",
        tactic="Command & Control",
        technique_name="Ingress Tool Transfer",
        pattern=re.compile(
            r"\b(curl\s+(-[a-zA-Z0-9]+\s+)*https?://|wget\s+https?://|tftp|ftp\s+-[a-zA-Z]*s)\b",
            re.IGNORECASE,
        ),
        base_severity=75,
        tactical_weight=2.8,
        is_critical=False,
        tarpit_base_delay=1.80,
    ),

    # --- Descubrimiento de Red ---
    _RuleDefinition(
        rule_id="RULE_DISCOVERY_NET_CONN",
        technique_id="T1049",
        tactic="Discovery",
        technique_name="System Network Connections Discovery",
        pattern=re.compile(
            r"^\s*(netstat\s+-[a-zA-Z0-9]+|ss\s+-[a-zA-Z0-9]+|lsof\s+-i|arp(\s+-[a-zA-Z]+)?)\b",
            re.IGNORECASE,
        ),
        base_severity=20,
        tactical_weight=1.2,
        is_critical=False,
        tarpit_base_delay=0.15,
    ),
    _RuleDefinition(
        rule_id="RULE_DISCOVERY_NET_CONF",
        technique_id="T1016",
        tactic="Discovery",
        technique_name="System Network Configuration Discovery",
        pattern=re.compile(
            r"^\s*(ifconfig|ip\s+(addr|a|route|r)|route(\s+-[a-zA-Z]+)?|cat\s+/etc/resolv\.conf)\b",
            re.IGNORECASE,
        ),
        base_severity=20,
        tactical_weight=1.2,
        is_critical=False,
        tarpit_base_delay=0.15,
    ),

    # --- Descubrimiento de Sistema, Procesos y Archivos ---
    _RuleDefinition(
        rule_id="RULE_DISCOVERY_PROCESS",
        technique_id="T1057",
        tactic="Discovery",
        technique_name="Process Discovery",
        pattern=re.compile(
            r"^\s*(ps(\s+-[a-zA-Z]+|\s+aux|\s+-ef)?|top\s+-[a-zA-Z0-9]+|pstree|pgrep)\b",
            re.IGNORECASE,
        ),
        base_severity=15,
        tactical_weight=1.0,
        is_critical=False,
        tarpit_base_delay=0.10,
    ),
    _RuleDefinition(
        rule_id="RULE_DISCOVERY_FILES",
        technique_id="T1083",
        tactic="Discovery",
        technique_name="File and Directory Discovery",
        pattern=re.compile(
            r"^\s*(find\s+[/~.]\s+|locate\s+|tree(\s+-[a-zA-Z]+)?)\b",
            re.IGNORECASE,
        ),
        base_severity=15,
        tactical_weight=1.0,
        is_critical=False,
        tarpit_base_delay=0.10,
    ),
    _RuleDefinition(
        rule_id="RULE_DISCOVERY_SYSINFO",
        technique_id="T1082",
        tactic="Discovery",
        technique_name="System Information Discovery",
        pattern=re.compile(
            r"^\s*(uname(\s+-[a-zA-Z]+)?|cat\s+/etc/(os-release|issue|redhat-release)|cat\s+/proc/version|hostnamectl|lscpu)\b",
            re.IGNORECASE,
        ),
        base_severity=10,
        tactical_weight=1.0,
        is_critical=False,
        tarpit_base_delay=0.05,
    ),
    _RuleDefinition(
        rule_id="RULE_DISCOVERY_USER",
        technique_id="T1033",
        tactic="Discovery",
        technique_name="System Owner/User Discovery",
        pattern=re.compile(
            r"^\s*(whoami|id|w|who|last|logname)\b",
            re.IGNORECASE,
        ),
        base_severity=10,
        tactical_weight=1.0,
        is_critical=False,
        tarpit_base_delay=0.05,
    ),
)


def classify_command(raw_command: str) -> MitreClassification | None:
    """Clasifica un comando contra las reglas heurísticas MITRE ATT&CK.

    Normaliza la entrada y evalúa en orden de severidad/criticidad.
    Garantiza retorno en menos de 1 milisegundo.
    """
    if not raw_command:
        return None

    # Normalización rápida
    normalized = raw_command.strip()
    if not normalized:
        return None

    # Búsqueda determinística de primer coincidencia priorizada
    for rule in RULES:
        if rule.pattern.search(normalized):
            return MitreClassification(
                rule_id=rule.rule_id,
                technique_id=rule.technique_id,
                tactic=rule.tactic,
                technique_name=rule.technique_name,
                base_severity=rule.base_severity,
                tactical_weight=rule.tactical_weight,
                is_critical=rule.is_critical,
                tarpit_base_delay=rule.tarpit_base_delay,
            )

    return None
