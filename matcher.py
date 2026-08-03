"""Deterministic, explainable match scoring between a job posting and the
master CV. No API dependency — works standalone. An optional Gemini-based
semantic nuance layer can sit on top of this later without changing the
public interface (score_posting always returns a MatchResult; a future
`semantic_adjust(result, posting_text)` can just nudge `.score`).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from models import MasterCV

# tag -> keywords/phrases (ES + EN) that signal this tag is relevant to a posting.
# Matching is done on accent-stripped, lowercased text via substring search.
TAG_KEYWORDS: dict[str, list[str]] = {
    "markets": [
        "mercado", "mercados", "bursatil", "bursatiles", "bolsa", "inversion", "inversiones",
        "valores", "trading", "market", "markets", "securities", "investment", "investments",
        "equity", "commodities", "renta variable", "renta fija", "capital markets",
    ],
    "investment": [
        "inversion", "inversiones", "portafolio", "cartera de inversion", "investment",
        "portfolio", "asset management", "gestion de activos",
    ],
    "quant": [
        "python", "data science", "ciencia de datos", "analisis de datos", "modelos",
        "quantitative", "quant", "machine learning", "power bi", "sql", "programacion",
    ],
    "data-science": [
        "data science", "ciencia de datos", "machine learning", "analisis de datos",
        "power bi", "visualizacion de datos", "modelos predictivos",
    ],
    "regulatory": [
        "regulacion", "regulatorio", "normativ", "cumplimiento", "compliance", "regulation",
        "regulatory", "banca", "banking regulation", "seguro de depositos", "deposit insurance",
        "resolucion bancaria", "ipab",
    ],
    "policy": [
        "politica publica", "politicas", "policy", "framework", "marco regulatorio",
        "internacional", "international", "vinculacion", "cooperacion internacional",
    ],
    "writing": [
        "redaccion", "redactar", "reportes", "informes", "writing", "reports",
        "documentacion", "documentation", "analisis tecnico", "technical writing",
        "materiales tecnicos",
    ],
    "english": [
        "ingles avanzado", "advanced english", "bilingue", "bilingual", "english proficiency",
        "professional english",
    ],
    "leadership": [
        "liderazgo", "equipo", "coordinacion de equipo", "leadership", "team management",
        "gestion de equipos",
    ],
    "process-improvement": [
        "eficiencia", "procesos", "mejora continua", "efficiency", "process improvement",
        "optimizacion",
    ],
    "reconciliation": [
        "conciliacion", "conciliaciones bancarias", "reconciliation", "bank reconciliation",
    ],
    "financial-reporting": [
        "reportes financieros", "financial reporting", "estados financieros",
        "financial statements",
    ],
    "sales": [
        "ventas", "sales", "cartera de clientes", "prospeccion", "prospecting",
    ],
    "client-relations": [
        "clientes", "customer", "atencion al cliente", "customer relations",
    ],
    "coordination": [
        "coordinacion", "logistica", "coordination", "logistics", "organizacion de eventos",
    ],
    "problem-solving": [
        "resolucion de problemas", "problem solving", "incidentes", "manejo de crisis",
    ],
}

SOURCE_WEIGHT = {"certification": 3, "experience": 2, "project": 2, "skill": 1}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.lower()


def detect_tags_in_text(text: str) -> set[str]:
    norm = _normalize(text)
    found = set()
    for tag, keywords in TAG_KEYWORDS.items():
        for kw in keywords:
            if _normalize(kw) in norm:
                found.add(tag)
                break
    return found


@dataclass
class TagSource:
    tag: str
    source_type: str  # certification | experience | project | skill
    label: str


def _cv_tag_sources(cv: MasterCV) -> list[TagSource]:
    sources: list[TagSource] = []
    for c in cv.certifications:
        for t in c.tags:
            sources.append(TagSource(t, "certification", c.name))
    for e in cv.experience:
        for t in e.tags:
            sources.append(TagSource(t, "experience", f"{e.role_es} — {e.company}"))
    for p in cv.projects:
        for t in p.tags:
            sources.append(TagSource(t, "project", p.name))
    for sg in cv.skills:
        for t in sg.tags:
            sources.append(TagSource(t, "skill", sg.category))
    return sources


@dataclass
class MatchResult:
    score: int
    matched_tags: list[str] = field(default_factory=list)
    gap_tags: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)


MAX_SINGLE_TAG_WEIGHT = max(SOURCE_WEIGHT.values())  # a cert-level presence fully satisfies a tag


def score_posting(cv: MasterCV, posting_text: str) -> MatchResult:
    """Score = how well the tags the POSTING cares about are backed in the CV,
    not how much of the CV's total surface is relevant. This way a broad,
    mixed background (e.g. an old sales job) doesn't dilute the score for a
    posting that only cares about a few specific things.
    """
    posting_tags = detect_tags_in_text(posting_text)
    sources = _cv_tag_sources(cv)

    cv_tags: dict[str, list[TagSource]] = {}
    for s in sources:
        cv_tags.setdefault(s.tag, []).append(s)

    def tag_weight(tag_sources: list[TagSource]) -> int:
        return sum(SOURCE_WEIGHT[s.source_type] for s in tag_sources)

    if not posting_tags:
        return MatchResult(
            score=0, matched_tags=[], gap_tags=[],
            rationale=["No se detectaron temas claros en el texto de la vacante — pega la descripción completa del puesto."],
        )

    matched_tags = sorted(t for t in posting_tags if t in cv_tags)
    gap_tags = sorted(posting_tags - cv_tags.keys())

    achieved = sum(min(tag_weight(cv_tags[t]), MAX_SINGLE_TAG_WEIGHT) for t in matched_tags)
    ideal = MAX_SINGLE_TAG_WEIGHT * len(posting_tags)
    score = round(100 * achieved / ideal) if ideal else 0
    score = max(0, min(100, score))

    rationale = []
    for t in matched_tags:
        labels = sorted({s.label for s in cv_tags[t]})
        rationale.append(f"✓ {t}: {', '.join(labels)}")
    if gap_tags:
        rationale.append(f"⚠ La vacante también menciona: {', '.join(gap_tags)} — no cubierto claramente en tu perfil.")

    return MatchResult(score=score, matched_tags=matched_tags, gap_tags=gap_tags, rationale=rationale)
