# Dueño: P4 — Defensa y SOC
# Responsabilidad: Componente visual de matriz táctica MITRE ATT&CK con técnicas activas.
# Puede importar: librerías de UI (streamlit)
# No importar: honey_agent.defense, honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary

from __future__ import annotations

import streamlit as st


ALL_TECHNIQUES: list[dict[str, str]] = [
    {"id": "T1082", "name": "System Info Discovery", "tactic": "Discovery"},
    {"id": "T1033", "name": "User Discovery", "tactic": "Discovery"},
    {"id": "T1057", "name": "Process Discovery", "tactic": "Discovery"},
    {"id": "T1083", "name": "File Discovery", "tactic": "Discovery"},
    {"id": "T1049", "name": "Network Conn Discovery", "tactic": "Discovery"},
    {"id": "T1016", "name": "Network Conf Discovery", "tactic": "Discovery"},
    {"id": "T1552.001", "name": "Credentials in Files", "tactic": "Credential Access"},
    {"id": "T1552.004", "name": "Private Keys Discovery", "tactic": "Credential Access"},
    {"id": "T1003", "name": "OS Credential Dumping", "tactic": "Credential Access"},
    {"id": "T1059.001", "name": "Unix Shell Scripting", "tactic": "Execution"},
    {"id": "T1105", "name": "Ingress Tool Transfer", "tactic": "C2"},
    {"id": "T1053.003", "name": "Cron Persistence", "tactic": "Persistence"},
    {"id": "T1136.001", "name": "Local Account Creation", "tactic": "Persistence"},
    {"id": "T1548.003", "name": "Sudo Caching", "tactic": "Privilege Escalation"},
    {"id": "T1070.004", "name": "Indicator Removal", "tactic": "Defense Evasion"},
    {"id": "T1027", "name": "Obfuscated Commands", "tactic": "Defense Evasion"},
]


def render_mitre_matrix(active_technique_ids: set[str] | list[str]) -> None:
    """Renderiza una cuadrícula con las técnicas MITRE iluminando las detectadas."""
    active_set = set(active_technique_ids)

    st.markdown("### 🛡️ Matriz MITRE ATT&CK Activa")

    cards_html = []
    for item in ALL_TECHNIQUES:
        t_id = item["id"]
        is_active = t_id in active_set

        if is_active:
            bg = "rgba(239, 68, 68, 0.25)"
            border = "#ef4444"
            text_color = "#fca5a5"
            glow = "0 0 10px rgba(239, 68, 68, 0.4)"
            badge = "🔥 ACTIVA"
        else:
            bg = "rgba(30, 41, 59, 0.5)"
            border = "rgba(148, 163, 184, 0.2)"
            text_color = "#94a3b8"
            glow = "none"
            badge = "—"

        cards_html.append(f"""
        <div style="
            background: {bg};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 8px 10px;
            box-shadow: {glow};
            font-family: sans-serif;
            margin-bottom: 6px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 700; color: #f8fafc; font-size: 13px;">{t_id}</span>
                <span style="font-size: 10px; font-weight: 600; color: {text_color};">{badge}</span>
            </div>
            <div style="font-size: 11px; color: #cbd5e1; margin-top: 2px;">{item['name']}</div>
            <div style="font-size: 9px; color: #64748b; text-transform: uppercase;">{item['tactic']}</div>
        </div>
        """)

    col1, col2 = st.columns(2)
    half = (len(cards_html) + 1) // 2

    with col1:
        st.markdown("".join(cards_html[:half]), unsafe_allow_html=True)
    with col2:
        st.markdown("".join(cards_html[half:]), unsafe_allow_html=True)
