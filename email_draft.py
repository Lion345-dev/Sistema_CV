"""Builds an outgoing application email for manual review and sending.

This module NEVER sends anything — it only assembles recipient, subject, and
body text, plus a note on what to attach. Luis copies this into his own email
client (or a mailto: link) and sends it himself. That's a deliberate,
confirmed decision — see the project plan — not a missing feature.
"""
from __future__ import annotations

import urllib.parse
from dataclasses import dataclass

from models import MasterCV

SUBJECT_TEMPLATES = {
    "es": "Postulación — {role} — {name}",
    "en": "Application — {role} — {name}",
}

BODY_TEMPLATES = {
    "es": (
        "Estimado equipo de reclutamiento,\n\n"
        "Adjunto mi CV y carta de intención para la vacante de {role}"
        "{company_clause}. Quedo atento a cualquier duda o a coordinar una "
        "entrevista cuando les convenga.\n\n"
        "Saludos cordiales,\n"
        "{name}\n"
        "{email} · {phone}"
    ),
    "en": (
        "Dear Hiring Team,\n\n"
        "Please find attached my CV and cover letter for the {role} position"
        "{company_clause}. I'm happy to answer any questions or schedule an "
        "interview at your convenience.\n\n"
        "Best regards,\n"
        "{name}\n"
        "{email} · {phone}"
    ),
}


@dataclass
class EmailDraft:
    to: str
    subject: str
    body: str
    attachments_note: str
    mailto_url: str


def _company_clause(company: str, language: str) -> str:
    if not company:
        return ""
    return f" at {company}" if language == "en" else f" en {company}"


def build_email_draft(
    cv: MasterCV,
    role_title: str,
    company: str,
    language: str,
    to_email: str = "",
    cv_filename: str = "",
    cover_letter_filename: str = "",
) -> EmailDraft:
    langbank = language if language in SUBJECT_TEMPLATES else "en"

    subject = SUBJECT_TEMPLATES[langbank].format(role=role_title, name=cv.contact.name)
    body = BODY_TEMPLATES[langbank].format(
        role=role_title,
        company_clause=_company_clause(company, langbank),
        name=cv.contact.name,
        email=cv.contact.email,
        phone=cv.contact.phone,
    )

    attachments = [f for f in (cv_filename, cover_letter_filename) if f]
    if attachments:
        note = ("Adjuntar: " if langbank == "es" else "Attach: ") + ", ".join(attachments)
    else:
        note = "Recuerda adjuntar el CV y la carta de intención descargados." if langbank == "es" else "Remember to attach the downloaded CV and cover letter."

    mailto_params = {"subject": subject, "body": body}
    mailto_url = f"mailto:{urllib.parse.quote(to_email)}?" + urllib.parse.urlencode(mailto_params, quote_via=urllib.parse.quote)

    return EmailDraft(to=to_email, subject=subject, body=body, attachments_note=note, mailto_url=mailto_url)
