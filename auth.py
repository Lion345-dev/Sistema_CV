"""Simple password gate for the deployed app. The app URL on Streamlit
Community Cloud's free tier is public to anyone who has it, and it holds
personal data (contact info, application tracker with company names/status).
This is a lightweight PIN check, not real auth — good enough to keep casual
visitors out, not meant to withstand a determined attacker.

Set APP_PASSWORD in Streamlit secrets to activate. If unset (e.g. local dev),
the gate is skipped.
"""
import streamlit as st


def require_password():
    try:
        expected = st.secrets.get("APP_PASSWORD")
    except Exception:
        expected = None

    if not expected:
        return  # no password configured — local dev, gate skipped

    if st.session_state.get("authenticated"):
        return

    st.title("🔒 Acceso restringido")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if pw == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    st.stop()
