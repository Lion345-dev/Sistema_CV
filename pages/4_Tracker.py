import datetime

import streamlit as st
import pandas as pd

from storage import get_storage
from auth import require_password
from interview_prep import generate_prep_content

st.set_page_config(page_title="Tracker — Sistema_CV", page_icon="📋", layout="wide")
require_password()


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text).strip("_") or "doc"


@st.cache_resource
def _storage():
    return get_storage()


storage = _storage()

st.title("Tracker de postulaciones")
st.caption("A quién le mandaste qué, cuándo, y en qué status va.")

apps = storage.load_applications()

if not apps:
    st.info("Todavía no hay postulaciones. Ve a **New Posting** para crear la primera.")
    st.stop()

df = pd.DataFrame([
    {
        "id": a.id,
        "company": a.company,
        "role_title": a.role_title,
        "language": a.language,
        "match_score": a.match_score,
        "status": a.status,
        "date_created": a.date_created,
        "date_applied": a.date_applied or "",
        "cv_version_id": a.cv_version_id or "",
        "notes": a.notes,
    }
    for a in apps
])

edited = st.data_editor(
    df,
    use_container_width=True,
    disabled=["id", "company", "role_title", "language", "match_score", "date_created", "cv_version_id"],
    column_config={
        "status": st.column_config.SelectboxColumn(options=["draft", "applied", "interview", "rejected", "offer"]),
        "date_applied": st.column_config.TextColumn(help="YYYY-MM-DD"),
    },
    key="tracker_editor",
)

if st.button("💾 Guardar cambios", type="primary"):
    by_id = {a.id: a for a in apps}
    newly_applied = []
    for _, row in edited.iterrows():
        a = by_id.get(row["id"])
        if a:
            became_applied = row["status"] == "applied" and a.status != "applied"
            a.status = row["status"]
            a.date_applied = row["date_applied"] or None
            a.notes = row["notes"] or ""
            if became_applied and not a.interview_prep_path:
                newly_applied.append(a)

    storage.save_applications(list(by_id.values()), commit_message="Update application tracker")
    st.success("Guardado.")

    if newly_applied:
        cv = storage.load_master_cv()
        for a in newly_applied:
            with st.spinner(f"Generando preparación de entrevista para {a.company}..."):
                prep_text = generate_prep_content(cv, a)
                path = f"interview_prep/{slugify(a.company)}_{slugify(a.role_title)}_{a.id}/prep.md"
                storage.save_generated_document(
                    path, prep_text.encode("utf-8"),
                    commit_message=f"Generate interview prep for {a.company} — {a.role_title}",
                )
                a.interview_prep_path = path
        storage.save_applications(list(by_id.values()), commit_message="Link interview prep files")
        st.info(f"Preparación de entrevista generada para: {', '.join(a.company for a in newly_applied)}. Ve a **Interview Prep** para verla.")

st.divider()
st.subheader("Resumen por status")
st.bar_chart(df["status"].value_counts())
