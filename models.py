"""Data model for the master CV, job postings, applications, and generation history."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Contact:
    name: str
    location: str
    email: str
    phone: str
    linkedin_url: str


@dataclass
class SummaryVariant:
    id: str
    language: str  # "es" | "en"
    focus_tags: list[str]  # e.g. ["markets", "investment"] or ["regulatory", "writing"]
    text: str


@dataclass
class Bullet:
    text_es: str
    text_en: str
    tags: list[str] = field(default_factory=list)
    metric: Optional[str] = None  # short human note on what number this bullet leads with, for dedupe/selection


@dataclass
class ExperienceEntry:
    id: str
    company: str
    role_es: str
    role_en: str
    location: str
    start: str
    end: str  # "Presente" / "Present" or a year
    bullets: list[Bullet] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class EducationEntry:
    institution: str
    degree_es: str
    degree_en: str
    location: str
    start: str
    end: str
    notes_es: str = ""
    notes_en: str = ""


@dataclass
class Certification:
    id: str
    name: str
    issuer: str
    status: str  # "completed" | "in_progress"
    date: str
    tags: list[str] = field(default_factory=list)


@dataclass
class ProjectBullet:
    text_es: str
    text_en: str
    length: str = "medium"  # "short" | "medium" | "long" — lets variation engine pick a length-appropriate subset


@dataclass
class Project:
    id: str
    name: str
    bullets: list[ProjectBullet] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class SkillGroup:
    category: str
    items_es: list[str] = field(default_factory=list)
    items_en: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class Anecdote:
    """A personal, concrete detail for cover letters — not a CV bullet.
    Tag-less anecdotes are generic context (e.g. dual-degree + full-time work)
    usable in any cover letter; tagged ones surface only when relevant."""
    id: str
    text_es: str
    text_en: str
    tags: list[str] = field(default_factory=list)


@dataclass
class LanguageSkill:
    name_es: str
    name_en: str
    level_es: str
    level_en: str
    detail: str = ""


@dataclass
class MasterCV:
    contact: Contact
    summary_bank: list[SummaryVariant] = field(default_factory=list)
    experience: list[ExperienceEntry] = field(default_factory=list)
    education: list[EducationEntry] = field(default_factory=list)
    certifications: list[Certification] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    skills: list[SkillGroup] = field(default_factory=list)
    languages: list[LanguageSkill] = field(default_factory=list)
    anecdotes: list[Anecdote] = field(default_factory=list)
    interests_es: list[str] = field(default_factory=list)
    interests_en: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "MasterCV":
        return MasterCV(
            contact=Contact(**d["contact"]),
            summary_bank=[SummaryVariant(**s) for s in d.get("summary_bank", [])],
            experience=[
                ExperienceEntry(
                    **{**e, "bullets": [Bullet(**b) for b in e.get("bullets", [])]}
                )
                for e in d.get("experience", [])
            ],
            education=[EducationEntry(**e) for e in d.get("education", [])],
            certifications=[Certification(**c) for c in d.get("certifications", [])],
            projects=[
                Project(**{**p, "bullets": [ProjectBullet(**b) for b in p.get("bullets", [])]})
                for p in d.get("projects", [])
            ],
            skills=[SkillGroup(**s) for s in d.get("skills", [])],
            languages=[LanguageSkill(**l) for l in d.get("languages", [])],
            anecdotes=[Anecdote(**a) for a in d.get("anecdotes", [])],
            interests_es=d.get("interests_es", []),
            interests_en=d.get("interests_en", []),
        )


@dataclass
class Application:
    id: str
    company: str
    role_title: str
    posting_text: str
    language: str  # "es" | "en"
    date_created: str
    date_applied: Optional[str] = None
    match_score: Optional[int] = None
    match_rationale: list[str] = field(default_factory=list)
    cv_version_id: Optional[str] = None
    cover_letter_version_id: Optional[str] = None
    status: str = "draft"  # draft | applied | interview | rejected | offer
    notes: str = ""
    email_draft_id: Optional[str] = None
    interview_prep_path: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Application":
        return Application(**d)


@dataclass
class GeneratedVersion:
    id: str
    posting_id: str
    doc_type: str  # "cv" | "cover_letter"
    language: str
    template_choices: dict = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "GeneratedVersion":
        return GeneratedVersion(**d)
