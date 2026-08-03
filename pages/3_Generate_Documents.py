import datetime
import uuid

import streamlit as st

from storage import get_storage
from variation import build_varied_cv_content, build_varied_cover_letter_content
from docx_export import cv_to_bytes, cover_letter_to_bytes
from models import GeneratedVersion

st.set_page_config(page_title="Generate Documents — Sistema_CV", page_icon="🛠️", layout="wide")

MONTHS_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


@st.cache_resource
def _storage():
    return get_storage()


def format_date_line(location: str, language: str) -> str:
    today = datetime.date.today()
    if language == "es":
        return f"{location} — {today.day} de {MONTHS_ES[today.month]} de {today.year}"
    return f"{location} — {today.strftime('%B')} {today.day}, {today.year}"


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text).strip("_") or "doc"


storage = _storage()
cv = storage.load_master_cv()

st.title("Generar documentos")
st.caption("Genera un CV y carta de intención únicos para una postulación guardada. Cada generación se registra para garantizar que la estructura no se repita entre vacantes.")

if cv is None:
    st.error("No hay master_cv.yaml cargado.")
    st.stop()

apps = storage.load_applications()
if not apps:
    st.info("Todavía no hay postulaciones guardadas. Ve a **New Posting** primero.")
    st.stop()

options = {f"{a.company} — {a.role_title} ({a.status}, score {a.match_score})": a.id for a in apps}
selected_label = st.selectbox("Postulación", options=list(options.keys()))
app = next(a for a in apps if a.id == options[selected_label])

with st.expander("Texto de la vacante"):
    st.write(app.posting_text)

language = st.radio("Idioma", options=["es", "en"], index=0 if app.language == "es" else 1, horizontal=True)

if st.button("🎲 Generar CV y carta de intención", type="primary"):
    history = storage.load_generated_versions()

    cv_content, cv_choices = build_varied_cv_content(cv, app.posting_text, language, app.id, history)
    date_line = format_date_line(cv.contact.location, language)
    cover_content, cover_choices = build_varied_cover_letter_content(
        cv, app.posting_text, language, app.id, app.role_title, app.company, date_line, history
    )

    cv_bytes = cv_to_bytes(cv_content)
    cover_bytes = cover_letter_to_bytes(cover_content)

    now = datetime.datetime.now().isoformat()
    cv_version_id = f"{app.id}_cv_{uuid.uuid4().hex[:6]}"
    cover_version_id = f"{app.id}_cover_{uuid.uuid4().hex[:6]}"

    history.append(GeneratedVersion(id=cv_version_id, posting_id=app.id, doc_type="cv", language=language, template_choices=cv_choices.as_template_choices(), timestamp=now))
    history.append(GeneratedVersion(id=cover_version_id, posting_id=app.id, doc_type="cover_letter", language=language, template_choices=cover_choices, timestamp=now))
    storage.save_generated_versions(history, commit_message=f"Log generated versions for {app.id}")

    apps = storage.load_applications()
    for a in apps:
        if a.id == app.id:
            a.cv_version_id = cv_version_id
            a.cover_letter_version_id = cover_version_id
            a.language = language
    storage.save_applications(apps, commit_message=f"Link generated versions to application {app.id}")

    st.session_state[f"cv_bytes_{app.id}"] = cv_bytes
    st.session_state[f"cover_bytes_{app.id}"] = cover_bytes
    st.session_state[f"cv_preview_{app.id}"] = cv_content
    st.session_state[f"cover_preview_{app.id}"] = cover_content
    st.success("Documentos generados.")

if f"cv_bytes_{app.id}" in st.session_state:
    name_slug = slugify(cv.contact.name)
    role_slug = slugify(app.role_title)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Descargar CV (.docx)",
            data=st.session_state[f"cv_bytes_{app.id}"],
            file_name=f"CV_{name_slug}_{role_slug}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    with col2:
        st.download_button(
            "⬇️ Descargar carta de intención (.docx)",
            data=st.session_state[f"cover_bytes_{app.id}"],
            file_name=f"CoverLetter_{name_slug}_{role_slug}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    with st.expander("Vista previa — resumen del CV"):
        cv_preview = st.session_state[f"cv_preview_{app.id}"]
        st.write(cv_preview.summary)
        st.write("Orden de secciones:", " → ".join(cv_preview.section_order))

    with st.expander("Vista previa — carta de intención"):
        cover_preview = st.session_state[f"cover_preview_{app.id}"]
        st.write(cover_preview.salutation)
        for p in cover_preview.paragraphs:
            st.write(p)
        st.write(cover_preview.closing)

    st.caption("Revisa siempre el .docx descargado antes de enviarlo — este es un primer borrador, no un documento final.")
