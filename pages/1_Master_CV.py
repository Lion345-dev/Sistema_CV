import streamlit as st
import pandas as pd

from storage import get_storage
from auth import require_password
from models import (
    MasterCV, Contact, SummaryVariant, ExperienceEntry, Bullet,
    EducationEntry, Certification, Project, ProjectBullet, SkillGroup,
    LanguageSkill, Anecdote,
)

st.set_page_config(page_title="Master CV — Sistema_CV", page_icon="📄", layout="wide")
require_password()


@st.cache_resource
def _storage():
    return get_storage()


storage = _storage()
cv = storage.load_master_cv() or MasterCV(contact=Contact("", "", "", "", ""))

st.title("Master CV")
st.caption("Esta es la fuente de verdad. Cada CV/carta generado se arma seleccionando y reordenando piezas de aquí — no edites los .docx directamente.")


def tags_to_str(tags: list[str]) -> str:
    return ", ".join(tags)


def str_to_tags(s: str) -> list[str]:
    return [t.strip() for t in s.split(",") if t.strip()]


# --- Contact ---
with st.expander("Contacto", expanded=True):
    c1, c2 = st.columns(2)
    cv.contact.name = c1.text_input("Nombre", cv.contact.name)
    cv.contact.location = c2.text_input("Ubicación", cv.contact.location)
    c3, c4 = st.columns(2)
    cv.contact.email = c3.text_input("Email", cv.contact.email)
    cv.contact.phone = c4.text_input("Teléfono", cv.contact.phone)
    cv.contact.linkedin_url = st.text_input("LinkedIn URL", cv.contact.linkedin_url)

# --- Summary bank ---
with st.expander("Perfil Profesional / Professional Summary (banco de variantes)"):
    st.caption("Cada fila es una variante que el generador puede elegir según idioma y enfoque de la vacante (focus_tags). Ten al menos 2 variantes por (idioma, enfoque) para que haya variación real.")
    df = pd.DataFrame([
        {"id": s.id, "language": s.language, "focus_tags": tags_to_str(s.focus_tags), "text": s.text}
        for s in cv.summary_bank
    ])
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="summary_editor",
                             column_config={"text": st.column_config.TextColumn(width="large")})
    cv.summary_bank = [
        SummaryVariant(id=r["id"], language=r["language"], focus_tags=str_to_tags(r["focus_tags"]), text=r["text"])
        for _, r in edited.iterrows() if r["id"]
    ]

# --- Experience ---
with st.expander("Experiencia Profesional"):
    if st.button("+ Agregar experiencia"):
        cv.experience.append(ExperienceEntry(id=f"exp_new_{len(cv.experience)}", company="", role_es="", role_en="", location="", start="", end="", bullets=[]))

    for i, e in enumerate(cv.experience):
        st.markdown(f"**{e.company or '(nueva entrada)'}**")
        c1, c2, c3 = st.columns(3)
        e.company = c1.text_input("Empresa", e.company, key=f"exp_company_{i}")
        e.location = c2.text_input("Ubicación", e.location, key=f"exp_loc_{i}")
        e.id = c3.text_input("ID interno", e.id, key=f"exp_id_{i}")
        c4, c5, c6 = st.columns(3)
        e.role_es = c4.text_input("Puesto (ES)", e.role_es, key=f"exp_role_es_{i}")
        e.role_en = c5.text_input("Puesto (EN)", e.role_en, key=f"exp_role_en_{i}")
        c6a, c6b = c6.columns(2)
        e.start = c6a.text_input("Inicio", e.start, key=f"exp_start_{i}")
        e.end = c6b.text_input("Fin", e.end, key=f"exp_end_{i}")
        e.tags = str_to_tags(st.text_input("Tags (coma)", tags_to_str(e.tags), key=f"exp_tags_{i}"))

        bdf = pd.DataFrame([
            {"text_es": b.text_es, "text_en": b.text_en, "tags": tags_to_str(b.tags), "metric": b.metric or ""}
            for b in e.bullets
        ])
        b_edited = st.data_editor(bdf, num_rows="dynamic", use_container_width=True, key=f"exp_bullets_{i}")
        e.bullets = [
            Bullet(text_es=r["text_es"], text_en=r["text_en"], tags=str_to_tags(r["tags"]), metric=r["metric"] or None)
            for _, r in b_edited.iterrows() if r["text_es"] or r["text_en"]
        ]
        if st.button(f"🗑 Eliminar {e.company or 'entrada'}", key=f"exp_delete_{i}"):
            cv.experience.pop(i)
            st.rerun()
        st.divider()

# --- Education ---
with st.expander("Educación"):
    if st.button("+ Agregar educación"):
        cv.education.append(EducationEntry(institution="", degree_es="", degree_en="", location="", start="", end=""))
    for i, ed in enumerate(cv.education):
        c1, c2 = st.columns(2)
        ed.institution = c1.text_input("Institución", ed.institution, key=f"edu_inst_{i}")
        ed.location = c2.text_input("Ubicación", ed.location, key=f"edu_loc_{i}")
        c3, c4 = st.columns(2)
        ed.degree_es = c3.text_input("Título (ES)", ed.degree_es, key=f"edu_deg_es_{i}")
        ed.degree_en = c4.text_input("Título (EN)", ed.degree_en, key=f"edu_deg_en_{i}")
        c5, c6 = st.columns(2)
        ed.start = c5.text_input("Inicio", ed.start, key=f"edu_start_{i}")
        ed.end = c6.text_input("Fin", ed.end, key=f"edu_end_{i}")
        ed.notes_es = st.text_input("Notas (ES) — opcional, se omiten si no caben en una página", ed.notes_es, key=f"edu_notes_es_{i}")
        ed.notes_en = st.text_input("Notas (EN)", ed.notes_en, key=f"edu_notes_en_{i}")
        if st.button(f"🗑 Eliminar {ed.institution or 'entrada'}", key=f"edu_delete_{i}"):
            cv.education.pop(i)
            st.rerun()
        st.divider()

# --- Certifications ---
with st.expander("Certificaciones"):
    cdf = pd.DataFrame([
        {"id": c.id, "name": c.name, "issuer": c.issuer, "status": c.status, "date": c.date, "tags": tags_to_str(c.tags)}
        for c in cv.certifications
    ])
    c_edited = st.data_editor(
        cdf, num_rows="dynamic", use_container_width=True, key="cert_editor",
        column_config={"status": st.column_config.SelectboxColumn(options=["completed", "in_progress"])},
    )
    cv.certifications = [
        Certification(id=r["id"], name=r["name"], issuer=r["issuer"], status=r["status"], date=str(r["date"]), tags=str_to_tags(r["tags"]))
        for _, r in c_edited.iterrows() if r["name"]
    ]

# --- Projects ---
with st.expander("Proyectos (AutoInvest Pro, etc.)"):
    if st.button("+ Agregar proyecto"):
        cv.projects.append(Project(id=f"proj_new_{len(cv.projects)}", name="", bullets=[]))
    for i, p in enumerate(cv.projects):
        c1, c2 = st.columns(2)
        p.name = c1.text_input("Nombre", p.name, key=f"proj_name_{i}")
        p.id = c2.text_input("ID interno", p.id, key=f"proj_id_{i}")
        p.tags = str_to_tags(st.text_input("Tags (coma)", tags_to_str(p.tags), key=f"proj_tags_{i}"))
        pdf = pd.DataFrame([
            {"text_es": b.text_es, "text_en": b.text_en, "length": b.length} for b in p.bullets
        ])
        p_edited = st.data_editor(
            pdf, num_rows="dynamic", use_container_width=True, key=f"proj_bullets_{i}",
            column_config={"length": st.column_config.SelectboxColumn(options=["short", "medium", "long"])},
        )
        p.bullets = [
            ProjectBullet(text_es=r["text_es"], text_en=r["text_en"], length=r["length"] or "medium")
            for _, r in p_edited.iterrows() if r["text_es"] or r["text_en"]
        ]
        if st.button(f"🗑 Eliminar {p.name or 'proyecto'}", key=f"proj_delete_{i}"):
            cv.projects.pop(i)
            st.rerun()
        st.divider()

# --- Skills ---
with st.expander("Habilidades"):
    sdf = pd.DataFrame([
        {"category": sg.category, "items_es": ", ".join(sg.items_es), "items_en": ", ".join(sg.items_en), "tags": tags_to_str(sg.tags)}
        for sg in cv.skills
    ])
    s_edited = st.data_editor(sdf, num_rows="dynamic", use_container_width=True, key="skills_editor")
    cv.skills = [
        SkillGroup(category=r["category"], items_es=str_to_tags(r["items_es"]), items_en=str_to_tags(r["items_en"]), tags=str_to_tags(r["tags"]))
        for _, r in s_edited.iterrows() if r["category"]
    ]

# --- Languages ---
with st.expander("Idiomas"):
    ldf = pd.DataFrame([
        {"name_es": l.name_es, "name_en": l.name_en, "level_es": l.level_es, "level_en": l.level_en, "detail": l.detail}
        for l in cv.languages
    ])
    l_edited = st.data_editor(ldf, num_rows="dynamic", use_container_width=True, key="lang_editor")
    cv.languages = [
        LanguageSkill(name_es=r["name_es"], name_en=r["name_en"], level_es=r["level_es"], level_en=r["level_en"], detail=r["detail"] or "")
        for _, r in l_edited.iterrows() if r["name_es"]
    ]

# --- Anecdotes ---
with st.expander("Anécdotas (para cartas de intención)"):
    st.caption("Detalles personales y concretos que se usan en las cartas de intención, no en el CV. Deja tags vacíos para que sean de uso genérico (siempre disponibles).")
    adf = pd.DataFrame([
        {"id": a.id, "text_es": a.text_es, "text_en": a.text_en, "tags": tags_to_str(a.tags)}
        for a in cv.anecdotes
    ])
    a_edited = st.data_editor(adf, num_rows="dynamic", use_container_width=True, key="anecdote_editor")
    cv.anecdotes = [
        Anecdote(id=r["id"], text_es=r["text_es"], text_en=r["text_en"], tags=str_to_tags(r["tags"]))
        for _, r in a_edited.iterrows() if r["id"]
    ]

# --- Interests ---
with st.expander("Intereses"):
    c1, c2 = st.columns(2)
    interests_es = c1.text_area("Intereses (ES, coma)", ", ".join(cv.interests_es))
    interests_en = c2.text_area("Interests (EN, comma)", ", ".join(cv.interests_en))
    cv.interests_es = str_to_tags(interests_es)
    cv.interests_en = str_to_tags(interests_en)

st.divider()
if st.button("💾 Guardar cambios", type="primary"):
    storage.save_master_cv(cv, commit_message="Update master CV from app")
    st.success("Guardado.")
