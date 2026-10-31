# Dueño: P4 — Defensa y SOC
# Responsabilidad: Feed forense de comandos en vivo y eventos del atacante.
# Puede importar: librerías de UI (streamlit)
# No importar: honey_agent.defense, honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary

from __future__ import annotations

import streamlit as st


def render_terminal_feed(commands_history: list[dict[str, str | float | int]]) -> None:
    """Renderiza la consola terminal con el feed forense en vivo."""
    st.markdown("### 🖥️ Terminal Forense en Vivo (PTY Stream)")

    if not commands_history:
        st.info("Esperando interacciones de atacantes...")
        return

    lines = []
    for item in commands_history[-15:]:  # Mostrar últimos 15
        cmd = item.get("command", "")
        mitre = item.get("mitre", "None")
        score = item.get("score", 0.0)
        delay = item.get("delay_ms", 0)

        lines.append(f"""
        <div style="
            background: #090d16;
            border-left: 3px solid #38bdf8;
            padding: 8px 12px;
            margin-bottom: 6px;
            border-radius: 0 6px 6px 0;
            font-family: 'Courier New', Courier, monospace;
            font-size: 13px;
        ">
            <div style="color: #4ade80;">root@prod-srv-app01:~# <span style="color: #f8fafc; font-weight: bold;">{cmd}</span></div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 3px;">
                <span style="color: #fb923c;">MITRE: {mitre}</span> | 
                <span style="color: #f43f5e;">Score: {score}%</span> | 
                <span style="color: #a78bfa;">Tarpit: {delay}ms</span>
            </div>
        </div>
        """)

    st.markdown("".join(lines), unsafe_allow_html=True)
