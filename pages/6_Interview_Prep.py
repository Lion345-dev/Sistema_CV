import streamlit as st

from storage import get_storage
from auth import require_password
from interview_prep import generate_prep_content

st.set_page_config(page_title="Interview Prep — Sistema_CV", page_icon="🎤", layout="wide")
require_password()


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text).strip("_") or "doc"


@st.cache_resource
def _storage():
    return get_storage()


storage = _storage()
cv = storage.load_master_cv()
apps = storage.load_applications()

st.title("Preparación de entrevistas")
st.caption(
    "Se genera automáticamente cuando marcas una postulación como 'applied' en el Tracker. "
    "Es un punto de partida con lo que el modelo sabe de la empresa — verifica noticias "
    "recientes antes de una entrevista real."
)

ready = [a for a in apps if a.interview_prep_path]
pending = [a for a in apps if a.status == "applied" and not a.interview_prep_path]

if not ready and not pending:
    st.info("Todavía no hay ninguna postulación marcada como 'applied'. Márcala en el Tracker para generar su preparación automáticamente.")
    st.stop()

if pending:
    st.warning(
        f"{len(pending)} postulación(es) marcadas como 'applied' sin preparación generada: "
        + ", ".join(f"{a.company} — {a.role_title}" for a in pending)
    )

if ready:
    options = {f"{a.company} — {a.role_title}": a.id for a in ready}
    selected_label = st.selectbox("Postulación", options=list(options.keys()))
    app = next(a for a in ready if a.id == options[selected_label])

    content = storage.load_generated_document(app.interview_prep_path)
    if content is None:
        st.error("No se encontró el archivo guardado. Intenta regenerarlo.")
    else:
        st.markdown(content.decode("utf-8"))

    if st.button("🔄 Regenerar"):
        with st.spinner("Regenerando..."):
            prep_text = generate_prep_content(cv, app)
            storage.save_generated_document(
                app.interview_prep_path, prep_text.encode("utf-8"),
                commit_message=f"Regenerate interview prep for {app.company} — {app.role_title}",
            )
        st.success("Regenerado.")
        st.rerun()

for a in pending:
    if st.button(f"🎲 Generar ahora para {a.company}", key=f"gen_{a.id}"):
        with st.spinner("Generando..."):
            prep_text = generate_prep_content(cv, a)
            path = f"interview_prep/{slugify(a.company)}_{slugify(a.role_title)}_{a.id}/prep.md"
            storage.save_generated_document(
                path, prep_text.encode("utf-8"),
                commit_message=f"Generate interview prep for {a.company} — {a.role_title}",
            )
            a.interview_prep_path = path
            all_apps = storage.load_applications()
            for existing in all_apps:
                if existing.id == a.id:
                    existing.interview_prep_path = path
            storage.save_applications(all_apps, commit_message="Link interview prep file")
        st.success("Generado.")
        st.rerun()
