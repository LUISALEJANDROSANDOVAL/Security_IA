# Dueño: P4 — Defensa y SOC
# Responsabilidad: Componente visual de velocímetro (Gauge) para el Threat Score (0-100%).
# Puede importar: librerías de UI (streamlit, plotly)
# No importar: honey_agent.defense, honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary

from __future__ import annotations

import streamlit as st


def render_score_gauge(score: float, status_label: str = "NORMAL") -> None:
    """Renderiza un indicador visual tipo velocímetro para el Threat Score."""
    clamped_score = min(100.0, max(0.0, float(score)))

    # Determinar color según severidad
    if clamped_score < 40.0:
        bar_color = "#10B981"  # Verde esmeralda
        glow_color = "rgba(16, 185, 129, 0.4)"
        level_text = "NORMAL (BAJO RIESGO)"
    elif clamped_score < 80.0:
        bar_color = "#F59E0B"  # Ámbar
        glow_color = "rgba(245, 158, 11, 0.4)"
        level_text = "SOSPECHOSO (RECONOCIMIENTO AVANZADO)"
    else:
        bar_color = "#EF4444"  # Rojo carmesí
        glow_color = "rgba(239, 68, 68, 0.6)"
        level_text = "CRÍTICO (AMENAZA ACTIVA / CONTENCIÓN)"

    html_code = f"""
    <div style="
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 20px {glow_color};
        margin-bottom: 20px;
    ">
        <div style="font-size: 13px; letter-spacing: 1.5px; text-transform: uppercase; color: #94a3b8; margin-bottom: 8px;">
            THREAT SCORE EN TIEMPO REAL
        </div>
        <div style="font-size: 54px; font-weight: 800; font-family: monospace; color: {bar_color}; text-shadow: 0 0 15px {glow_color};">
            {clamped_score:.1f}%
        </div>
        <div style="
            width: 100%;
            height: 12px;
            background: #334155;
            border-radius: 6px;
            overflow: hidden;
            margin: 14px 0 10px 0;
        ">
            <div style="
                width: {clamped_score}%;
                height: 100%;
                background: linear-gradient(90deg, #10B981, #F59E0B 50%, #EF4444 80%);
                border-radius: 6px;
                transition: width 0.5s ease-in-out;
            "></div>
        </div>
        <div style="font-size: 14px; font-weight: 600; color: {bar_color}; letter-spacing: 0.5px;">
            ESTADO: {level_text}
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
