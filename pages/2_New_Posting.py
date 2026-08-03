import uuid
import datetime

import streamlit as st

from storage import get_storage
from auth import require_password
from matcher import score_posting
from generator import detect_language
from models import Application

st.set_page_config(page_title="New Posting — Sistema_CV", page_icon="📥", layout="wide")
require_password()


@st.cache_resource
def _storage():
    return get_storage()


storage = _storage()
cv = storage.load_master_cv()

st.title("Nueva vacante")
st.caption("Pega la descripción del puesto para ver qué tan bien calza con tu perfil antes de invertir tiempo tailoreando un CV.")

if cv is None:
    st.error("No hay master_cv.yaml cargado. Ve a la página Master CV primero.")
    st.stop()

with st.form("new_posting_form"):
    c1, c2 = st.columns(2)
    company = c1.text_input("Empresa / institución")
    role_title = c2.text_input("Puesto")
    posting_text = st.text_area("Texto de la vacante (pega la descripción completa)", height=250)
    submitted = st.form_submit_button("Analizar match")

if submitted and posting_text.strip():
    st.session_state["last_posting_text"] = posting_text
    st.session_state["last_posting_company"] = company
    st.session_state["last_posting_role"] = role_title

if st.session_state.get("last_posting_text"):
    posting_text = st.session_state["last_posting_text"]
    company = st.session_state.get("last_posting_company", "")
    role_title = st.session_state.get("last_posting_role", "")

    result = score_posting(cv, posting_text)
    detected_lang = detect_language(posting_text)

    st.subheader(f"Match score: {result.score}/100")
    st.progress(result.score / 100)

    if result.score >= 70:
        st.success("Buen match — probablemente vale la pena tailorear un CV para esta vacante.")
    elif result.score >= 40:
        st.warning("Match parcial — revisa los gaps abajo antes de decidir.")
    else:
        st.error("Match bajo — probablemente no es tu mejor uso del tiempo, salvo que tengas otra razón para aplicar.")

    for line in result.rationale:
        st.write(line)

    language = st.selectbox(
        "Idioma del CV a generar (detectado automáticamente, puedes cambiarlo)",
        options=["es", "en"], index=0 if detected_lang == "es" else 1,
    )

    if st.button("💾 Guardar como borrador de postulación", type="primary"):
        apps = storage.load_applications()
        app = Application(
            id=str(uuid.uuid4())[:8],
            company=company or "(sin nombre)",
            role_title=role_title or "(sin título)",
            posting_text=posting_text,
            language=language,
            date_created=datetime.date.today().isoformat(),
            match_score=result.score,
            match_rationale=result.rationale,
            status="draft",
        )
        apps.append(app)
        storage.save_applications(apps, commit_message=f"Add application draft: {app.company} — {app.role_title}")
        st.success(f"Guardado. Ve a **Generate Documents** para crear el CV y carta para esta postulación (id: {app.id}).")
        for key in ("last_posting_text", "last_posting_company", "last_posting_role"):
            st.session_state.pop(key, None)
