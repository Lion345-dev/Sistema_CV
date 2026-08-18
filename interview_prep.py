"""Generates an interview-prep briefing once an application is marked as sent.

Uses Gemini (GOOGLE_API_KEY) grounded in the posting text, our own match
rationale, and the master CV — not live web search. Treat company facts and
"recent developments" as a starting point generated from the model's training
knowledge, not confirmed current news; the briefing itself tells Luis what to
double-check before a real interview.

Set GOOGLE_API_KEY in Streamlit secrets (or the GOOGLE_API_KEY env var for
local runs) to activate. Without it, generate_prep_content() returns a short
placeholder explaining what's missing instead of failing loudly.
"""
from __future__ import annotations

import os

from models import MasterCV, Application

MODEL_NAME = "gemini-3.6-flash"


def _get_api_key() -> str | None:
    key = os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    try:
        import streamlit as st

        return st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        return None


def _cv_context_bullets(cv: MasterCV, language: str) -> str:
    lines = []
    for e in cv.experience:
        role = e.role_es if language == "es" else e.role_en
        lines.append(f"- {role} en {e.company} ({e.start}–{e.end})")
    for p in cv.projects:
        if p.bullets:
            lines.append(f"- Proyecto propio: {p.name} — {p.bullets[0].text_es if language == 'es' else p.bullets[0].text_en}")
    for c in cv.certifications:
        status = "en curso" if c.status == "in_progress" else "completada"
        lines.append(f"- Certificación {status}: {c.name} ({c.issuer})")
    return "\n".join(lines)


def _build_prompt(cv: MasterCV, app: Application) -> str:
    rationale = "\n".join(f"- {line}" for line in app.match_rationale) or "(sin análisis de match previo)"
    cv_context = _cv_context_bullets(cv, app.language)

    return f"""Eres un asistente de preparación de entrevistas. Genera un briefing en \
Markdown para {cv.contact.name}, quien acaba de enviar su postulación a esta vacante.

EMPRESA: {app.company}
PUESTO: {app.role_title}

DESCRIPCIÓN DE LA VACANTE:
{app.posting_text}

POR QUÉ SU PERFIL CALZA (de nuestro propio análisis de match):
{rationale}

CONTEXTO REAL DE SU EXPERIENCIA (para que conectes ejemplos concretos, no genéricos):
{cv_context}

Genera un documento en Markdown con exactamente estas secciones:

## Sobre la empresa
Qué hace, en qué industria/mercado compite, tamaño/etapa aproximada si la sabes. Si no \
tienes certeza de datos recientes, dilo explícitamente en vez de inventar cifras o hechos.

## Cultura y qué valoran
Señales de cultura de trabajo y del tipo de perfil que buscan, basado en la descripción \
de la vacante y lo que sepas de la empresa.

## Preguntas probables de entrevista
5 a 8 preguntas específicas para este puesto y esta empresa — nada genérico tipo \
"cuéntame de ti".

## Cómo conectar su experiencia
Para los temas/preguntas más importantes, sugiere brevemente qué parte de su experiencia \
real (arriba) puede mencionar, con el ejemplo concreto, no una sugerencia vaga.

## Preguntas inteligentes que puede hacer
3 a 5 preguntas que él puede hacerles a ellos, que demuestren investigación real, no \
preguntas de relleno.

## Antes de la entrevista, verifica
Una lista corta de cosas que debería confirmar por su cuenta (noticias recientes, cambios \
de liderazgo, rondas de inversión, etc.), ya que tu conocimiento puede no estar actualizado.

Escribe en {"español" if app.language == "es" else "inglés"}, tono directo y concreto. \
Evita frases de relleno tipo "es una gran oportunidad" o "empresa líder en su sector" sin \
sustento."""


def generate_prep_content(cv: MasterCV, app: Application) -> str:
    api_key = _get_api_key()
    if not api_key:
        return (
            "# Preparación de entrevista — pendiente\n\n"
            "No se generó automáticamente porque falta configurar `GOOGLE_API_KEY` en los "
            "secrets de esta app (es independiente del que ya configuraste en tu otro "
            "proyecto — Sistema_CV necesita el suyo propio). Agrégalo y vuelve a marcar "
            "esta postulación como **applied** en el Tracker (o usa el botón Regenerar en "
            "Interview Prep) para producir este briefing.\n"
        )

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(_build_prompt(cv, app))
    text = (response.text or "").strip()
    if not text:
        return "# Preparación de entrevista — error\n\nLa API no devolvió contenido. Intenta regenerar desde Interview Prep."
    return text
