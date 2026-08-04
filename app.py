import streamlit as st

from storage import get_storage
from auth import require_password

st.set_page_config(page_title="Sistema_CV", page_icon="📄", layout="wide")
require_password()


@st.cache_resource
def _storage():
    return get_storage()


def load_data():
    storage = _storage()
    cv = storage.load_master_cv()
    apps = storage.load_applications()
    return storage, cv, apps


storage, cv, applications = load_data()

st.title("📄 Sistema_CV")
st.caption("CV maestro → versiones tailored por vacante → tracker de postulaciones")

if cv is None:
    st.error(
        "No se encontró data/master_cv.yaml. Corre `python scripts/seed_master_cv.py` "
        "para inicializarlo, o créalo desde la página **Master CV**."
    )
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Postulaciones registradas", len(applications))
col2.metric("En borrador", sum(1 for a in applications if a.status == "draft"))
col3.metric("Enviadas", sum(1 for a in applications if a.status == "applied"))
col4.metric("En entrevista", sum(1 for a in applications if a.status == "interview"))

st.markdown(
    """
### Flujo de trabajo
1. **Master CV** — revisa o edita tus datos maestros (experiencia, certificaciones, proyectos).
2. **New Posting** — pega el texto de una vacante y obtén un match score explicado.
3. **Generate Documents** — genera un CV y carta de intención únicos para esa vacante.
4. **Tracker** — lleva registro de a quién le mandaste qué versión y en qué status va. Al marcar una postulación como **applied**, se genera automáticamente su preparación de entrevista.
5. **Email Draft** — arma el correo de postulación (nunca se envía automáticamente — lo revisas tú).
6. **Interview Prep** — briefing de la empresa, preguntas probables, y cómo conectar tu experiencia — listo para cuando te hablen para una entrevista.

Usa el menú de la izquierda para navegar entre páginas.
"""
)

st.info(
    "Cada CV/carta generado varía estructuralmente entre vacantes (orden de secciones, "
    "frases de apertura/cierre, selección de contenido) — es una regla del sistema, no un ajuste manual.",
    icon="🔀",
)
