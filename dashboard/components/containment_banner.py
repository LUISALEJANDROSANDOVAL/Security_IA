# Dueño: P4 — Defensa y SOC
# Responsabilidad: Banner prominente de alerta cuando se activa la contención perimetral (DROP).
# Puede importar: librerías de UI (streamlit)
# No importar: honey_agent.defense, honey_agent.ingress, honey_agent.vfs, honey_agent.posix, honey_agent.tarpit, honey_agent.canary

from __future__ import annotations

import streamlit as st


def render_containment_banner(
    attacker_ip: str,
    reason: str,
    kernel_cmd: str = "iptables -I INPUT -s IP -j DROP",
    duration_ms: float = 3.2,
) -> None:
    """Renderiza el banner crítico de IP bloqueada y sesión neutralizada."""
    html = f"""
    <div style="
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(185, 28, 28, 0.4));
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 24px;
        animation: pulse 2s infinite;
        box-shadow: 0 0 25px rgba(239, 68, 68, 0.5);
    ">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span style="
                    background: #ef4444;
                    color: white;
                    padding: 4px 10px;
                    border-radius: 6px;
                    font-weight: 800;
                    font-size: 13px;
                    letter-spacing: 1px;
                ">🚨 CONTAINED & BLOCKED</span>
                <span style="color: #fca5a5; font-weight: 700; margin-left: 12px; font-size: 16px;">
                    IP HOSTIL AISLADA EN KERNEL
                </span>
            </div>
            <div style="color: #cbd5e1; font-family: monospace; font-size: 13px;">
                Despacho: <b>{duration_ms:.1f} ms</b>
            </div>
        </div>
        <div style="margin-top: 12px; color: #f1f5f9; font-size: 14px;">
            <b>IP Atacante:</b> <code style="background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #f87171;">{attacker_ip}</code><br/>
            <b>Motivo de Cuarentena:</b> <span style="color: #fed7aa;">{reason}</span><br/>
            <b>Regla Netfilter:</b> <code style="background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #a5f3fc;">{kernel_cmd}</code>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
