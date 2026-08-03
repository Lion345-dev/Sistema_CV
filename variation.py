"""Structural uniqueness engine.

generator.py decides WHAT content goes into a document (tailoring). This
module decides HOW it's structurally presented — which phrasing variant,
which section order, which connective wording — so that two documents for
two different postings never come out looking like the same template with
the words swapped. That's the whole point: reduce the chance an employer's
AI-detector flags the output as templated.

Each choice is seeded deterministically from the posting_id, so regenerating
the same posting reproduces the same document (important for the "download
regenerates on demand, nothing is persisted as a binary" storage design —
see storage.py). Before finalizing, the chosen combination is checked against
generated_versions.yaml history; on a collision the seed is bumped and the
choice is re-rolled.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field

from models import MasterCV, GeneratedVersion
import generator
from matcher import detect_tags_in_text
from docx_export import CoverLetterContent

# Sections after "summary"/"experience" (always first, by CV convention) can
# reorder among themselves. Each tuple is a full valid order for everything
# after "experience". Certifications/projects lead for markets-flavored
# postings in the reference documents; keeping education/languages/skills
# after them is always safe for one-page ATS-style layouts.
SECTION_ORDER_VARIANTS: list[list[str]] = [
    ["summary", "experience", "certifications", "projects", "education", "languages", "skills"],
    ["summary", "experience", "projects", "certifications", "education", "languages", "skills"],
    ["summary", "experience", "certifications", "education", "projects", "languages", "skills"],
    ["summary", "experience", "projects", "education", "certifications", "languages", "skills"],
]

INTERESTS_LABELS = {
    "es": ["Intereses", "Fuera del trabajo"],
    "en": ["Interests", "Outside of work"],
}

MAX_REROLL_ATTEMPTS = 25


def derive_seed(posting_id: str, salt: str = "") -> int:
    digest = hashlib.sha256(f"{posting_id}:{salt}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


@dataclass
class VariationChoices:
    summary_variant_id: str
    section_order_index: int
    interests_label_index: int
    seed_used: int

    def as_template_choices(self) -> dict:
        return {
            "summary_variant_id": self.summary_variant_id,
            "section_order_index": self.section_order_index,
            "interests_label_index": self.interests_label_index,
        }


def _roll_choices(cv: MasterCV, posting_text: str, language: str, seed: int) -> tuple[VariationChoices, object]:
    rng = random.Random(seed)
    posting_tags = detect_tags_in_text(posting_text)

    candidates = generator.get_summary_candidates(cv, posting_tags, language)
    summary_variant = rng.choice(candidates)

    order_index = rng.randrange(len(SECTION_ORDER_VARIANTS))
    interests_index = rng.randrange(len(INTERESTS_LABELS.get(language, INTERESTS_LABELS["en"])))

    choices = VariationChoices(
        summary_variant_id=summary_variant.id,
        section_order_index=order_index,
        interests_label_index=interests_index,
        seed_used=seed,
    )
    return choices, summary_variant


def _collides(choices: VariationChoices, doc_type: str, language: str, history: list[GeneratedVersion]) -> bool:
    target = choices.as_template_choices()
    for v in history:
        if v.doc_type == doc_type and v.language == language and v.template_choices == target:
            return True
    return False


def resolve_variation(
    cv: MasterCV,
    posting_text: str,
    language: str,
    posting_id: str,
    doc_type: str,
    history: list[GeneratedVersion],
) -> tuple[VariationChoices, object]:
    """Returns (VariationChoices, chosen SummaryVariant). Re-rolls deterministically
    (seed + attempt) until the (summary_variant_id, section_order_index,
    interests_label_index) tuple hasn't been used before for this doc_type+language."""
    base_seed = derive_seed(posting_id, salt=doc_type)
    for attempt in range(MAX_REROLL_ATTEMPTS):
        seed = base_seed + attempt
        choices, summary_variant = _roll_choices(cv, posting_text, language, seed)
        if not _collides(choices, doc_type, language, history):
            return choices, summary_variant
    # exhausted reasonable attempts (only plausible with a tiny phrasing bank
    # and many postings sharing the same focus) — return the last roll anyway
    return choices, summary_variant


def build_varied_cv_content(
    cv: MasterCV,
    posting_text: str,
    language: str,
    posting_id: str,
    history: list[GeneratedVersion],
):
    """Convenience wrapper: resolves variation choices, builds the tailored
    CVContent with them applied, and returns (content, VariationChoices) so
    the caller can log the choices to generated_versions.yaml."""
    choices, summary_variant = resolve_variation(cv, posting_text, language, posting_id, "cv", history)
    section_order = SECTION_ORDER_VARIANTS[choices.section_order_index]
    content = generator.build_cv_content(
        cv, posting_text, language=language, summary_variant=summary_variant, section_order=section_order
    )
    labels = INTERESTS_LABELS.get(language, INTERESTS_LABELS["en"])
    content.interests_label = labels[choices.interests_label_index]
    return content, choices


# ============================================================================
# Cover letter phrasing bank + assembly
# ============================================================================

COVER_OPENING_TEMPLATES = {
    "en": [
        "I'm writing about the {role} posting{company_clause}.",
        "I came across the {role} opening{company_clause} and wanted to write directly, rather than send a generic cover letter.",
        "The {role} position{company_clause} caught my attention, and I'd like to explain why in my own words.",
    ],
    "es": [
        "Le escribo en relación con la vacante de {role}{company_clause}.",
        "Vi la vacante de {role}{company_clause} y preferí escribir directamente, en lugar de mandar una carta genérica.",
        "La vacante de {role}{company_clause} me llamó la atención, y quiero explicar por qué con mis propias palabras.",
    ],
}

COVER_CLOSING_TEMPLATES = {
    "en": [
        "I'd welcome the chance to talk this through further, including in English, whenever it's convenient.",
        "I'd be glad to discuss this in more detail whenever works for you.",
        "Happy to continue this conversation whenever it's useful — including in English.",
    ],
    "es": [
        "Con gusto platico esto con más detalle cuando les convenga.",
        "Quedo atento para conversar más a detalle en el momento que gusten.",
        "Me encantaría tener la oportunidad de platicar esto directamente cuando sea conveniente.",
    ],
}

SALUTATIONS = {
    "en": ["Dear Hiring Committee,", "Dear Hiring Team,", "To the Hiring Team,"],
    "es": ["Estimado equipo de reclutamiento,", "A quien corresponda,", "Estimados,"],
}

SIGNOFFS = {
    "en": ["Sincerely,", "Best regards,", "Kind regards,"],
    "es": ["Atentamente,", "Saludos cordiales,"],
}

TAG_FOCUS_PHRASES = {
    "regulatory": {"en": "banking regulation and how it actually gets applied", "es": "la regulación bancaria y cómo se aplica en la práctica"},
    "markets": {"en": "tracking markets and investment instruments", "es": "el seguimiento de mercados e instrumentos de inversión"},
    "policy": {"en": "comparing how different countries approach the same problem", "es": "comparar cómo distintos países abordan el mismo problema"},
    "writing": {"en": "structured technical writing", "es": "la redacción técnica estructurada"},
    "quant": {"en": "applying data and code to real financial decisions", "es": "aplicar datos y código a decisiones financieras reales"},
}
_FOCUS_PRIORITY = ["regulatory", "markets", "policy", "writing", "quant"]

CLOSING_THOUGHT_TEMPLATES = {
    "en": "I'm currently working on {cert_name}, which is part of why {focus_phrase} is something I'd genuinely want to spend time on, not just something to check off a job description.",
    "es": "Actualmente estoy en preparación para {cert_name}, y es parte de por qué {focus_phrase} es algo en lo que de verdad quiero invertir tiempo, no solo para cumplir con la descripción del puesto.",
}


def _company_clause(company: str, language: str) -> str:
    if not company:
        return ""
    return f" at {company}" if language == "en" else f" en {company}"


def _build_closing_thought(cv: MasterCV, posting_tags: set[str], language: str) -> str:
    cert = next((c for c in cv.certifications if c.status == "in_progress"), cv.certifications[0])
    focus_tag = next((t for t in _FOCUS_PRIORITY if t in posting_tags), None)
    phrase = TAG_FOCUS_PHRASES.get(focus_tag, {}).get(
        language, "this kind of work" if language == "en" else "este tipo de trabajo"
    )
    return CLOSING_THOUGHT_TEMPLATES[language].format(cert_name=cert.name, focus_phrase=phrase)


def _assemble_paragraphs(opening: str, anecdote_texts: list[str], closing_thought: str, three_paragraphs: bool) -> list[str]:
    if not anecdote_texts:
        return [opening, closing_thought]
    if three_paragraphs and len(anecdote_texts) >= 2:
        para1 = f"{opening} {anecdote_texts[0]}"
        para2 = " ".join(anecdote_texts[1:])
        para3 = closing_thought
        return [para1, para2, para3]
    # two-paragraph structure: everything but the closing thought folds together
    para1 = f"{opening} {anecdote_texts[0]}"
    para2 = " ".join(anecdote_texts[1:] + [closing_thought]) if len(anecdote_texts) > 1 else closing_thought
    return [para1, para2]


def resolve_cover_letter_variation(
    cv: MasterCV,
    posting_text: str,
    language: str,
    posting_id: str,
    history: list[GeneratedVersion],
) -> dict:
    base_seed = derive_seed(posting_id, salt="cover_letter")
    langbank = language if language in COVER_OPENING_TEMPLATES else "en"

    def roll(seed: int) -> dict:
        rng = random.Random(seed)
        return {
            "opening_index": rng.randrange(len(COVER_OPENING_TEMPLATES[langbank])),
            "closing_index": rng.randrange(len(COVER_CLOSING_TEMPLATES[langbank])),
            "salutation_index": rng.randrange(len(SALUTATIONS[langbank])),
            "signoff_index": rng.randrange(len(SIGNOFFS[langbank])),
            "three_paragraphs": rng.choice([True, False]),
        }

    for attempt in range(MAX_REROLL_ATTEMPTS):
        choices = roll(base_seed + attempt)
        collision = any(
            v.doc_type == "cover_letter" and v.language == language and v.template_choices == choices
            for v in history
        )
        if not collision:
            return choices
    return choices


def build_varied_cover_letter_content(
    cv: MasterCV,
    posting_text: str,
    language: str,
    posting_id: str,
    role_title: str,
    company: str,
    date_line: str,
    history: list[GeneratedVersion],
) -> tuple[CoverLetterContent, dict]:
    langbank = language if language in COVER_OPENING_TEMPLATES else "en"
    posting_tags = detect_tags_in_text(posting_text)
    choices = resolve_cover_letter_variation(cv, posting_text, language, posting_id, history)

    opening = COVER_OPENING_TEMPLATES[langbank][choices["opening_index"]].format(
        role=role_title, company_clause=_company_clause(company, langbank)
    )
    closing_sentence = COVER_CLOSING_TEMPLATES[langbank][choices["closing_index"]]
    salutation = SALUTATIONS[langbank][choices["salutation_index"]]
    signoff = SIGNOFFS[langbank][choices["signoff_index"]]

    anecdotes = generator.select_anecdotes(cv, posting_tags, language, max_n=3)
    anecdote_texts = [generator.anecdote_text(a, language) for a in anecdotes]
    closing_thought = _build_closing_thought(cv, posting_tags, language)

    paragraphs = _assemble_paragraphs(opening, anecdote_texts, closing_thought, choices["three_paragraphs"])
    paragraphs.append(closing_sentence)

    content = CoverLetterContent(
        language=language,
        date_line=date_line,
        salutation=salutation,
        paragraphs=paragraphs,
        closing=signoff,
        signature_name=cv.contact.name,
    )
    return content, choices
