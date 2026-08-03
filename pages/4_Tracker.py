import streamlit as st
import pandas as pd

from storage import get_storage

st.set_page_config(page_title="Tracker — Sistema_CV", page_icon="📋", layout="wide")


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
    for _, row in edited.iterrows():
        a = by_id.get(row["id"])
        if a:
            a.status = row["status"]
            a.date_applied = row["date_applied"] or None
            a.notes = row["notes"] or ""
    storage.save_applications(list(by_id.values()), commit_message="Update application tracker")
    st.success("Guardado.")

st.divider()
st.subheader("Resumen por status")
st.bar_chart(df["status"].value_counts())
