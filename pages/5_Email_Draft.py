import streamlit as st

from storage import get_storage
from email_draft import build_email_draft

st.set_page_config(page_title="Email Draft — Sistema_CV", page_icon="✉️", layout="wide")


@st.cache_resource
def _storage():
    return get_storage()


storage = _storage()
cv = storage.load_master_cv()

st.title("Borrador de correo")
st.caption("Esto arma el correo — nunca lo envía. Cópialo a tu cliente de correo, adjunta los .docx que descargaste en Generate Documents, y revísalo antes de mandarlo.")

if cv is None:
    st.error("No hay master_cv.yaml cargado.")
    st.stop()

apps = storage.load_applications()
if not apps:
    st.info("Todavía no hay postulaciones. Ve a **New Posting** primero.")
    st.stop()

options = {f"{a.company} — {a.role_title} ({a.status})": a.id for a in apps}
selected_label = st.selectbox("Postulación", options=list(options.keys()))
app = next(a for a in apps if a.id == options[selected_label])

to_email = st.text_input("Correo del destinatario (si lo conoces)")

if st.button("Armar borrador", type="primary"):
    draft = build_email_draft(
        cv, app.role_title, app.company, app.language,
        to_email=to_email,
        cv_filename=f"CV_{app.company}.docx" if app.cv_version_id else "",
        cover_letter_filename=f"CoverLetter_{app.company}.docx" if app.cover_letter_version_id else "",
    )
    st.session_state["email_draft"] = draft

if "email_draft" in st.session_state:
    draft = st.session_state["email_draft"]
    st.text_input("Para", value=draft.to, disabled=True)
    st.text_input("Asunto", value=draft.subject, disabled=True)
    st.text_area("Cuerpo", value=draft.body, height=200)
    st.warning(draft.attachments_note, icon="📎")
    if draft.to:
        st.link_button("Abrir en tu cliente de correo", draft.mailto_url)
    else:
        st.caption("Agrega el correo del destinatario para habilitar el link mailto.")

    if not app.cv_version_id or not app.cover_letter_version_id:
        st.info("Todavía no has generado documentos para esta postulación — ve a **Generate Documents** primero.")
