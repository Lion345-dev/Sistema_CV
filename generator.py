"""Content tailoring: decides *what* goes into a CV for a given posting —
which summary, which bullets, which certifications, how much project detail —
based on tag relevance to the posting. Structural presentation (section
order, phrasing choice, exact wording variation) is variation.py's job; this
module always returns the same content for the same (posting, language)
pair, in a stable/neutral order — variation.py permutes it afterward.
"""
from __future__ import annotations

import re
import unicodedata

from models import MasterCV, Certification, ExperienceEntry, SkillGroup
from matcher import detect_tags_in_text
from docx_export import CVContent, ExperienceBlock, ProjectBlock, EducationBlock

MAX_CERTIFICATIONS = 3
MAX_SKILL_GROUPS = 2
MIN_BULLETS_PER_ENTRY = 2
TOTAL_BULLET_BUDGET = 10  # across all experience entries combined, tuned to keep the CV to one page

_ES_MARKERS = {"de", "la", "el", "en", "para", "con", "que", "los", "del", "una", "por", "más"}
_EN_MARKERS = {"the", "and", "for", "with", "you", "will", "your", "our", "this", "team"}


def detect_language(posting_text: str) -> str:
    """Best-effort heuristic default; the caller can always override with an
    explicit choice (the New Posting page asks the user to confirm)."""
    norm = unicodedata.normalize("NFKD", posting_text).encode("ascii", "ignore").decode("ascii").lower()
    words = set(re.findall(r"[a-z]+", norm))
    es_hits = len(words & _ES_MARKERS)
    en_hits = len(words & _EN_MARKERS)
    return "en" if en_hits > es_hits else "es"


def _relevance(tags: list[str], posting_tags: set[str]) -> int:
    return len(set(tags) & posting_tags)


def get_summary_candidates(cv: MasterCV, posting_tags: set[str], language: str) -> list:
    """All summary variants tied for the best relevance score, in bank order.
    variation.py picks among these with a seed; select_summary just takes the first."""
    candidates = [s for s in cv.summary_bank if s.language == language] or cv.summary_bank
    best_score = max(_relevance(s.focus_tags, posting_tags) for s in candidates)
    return [s for s in candidates if _relevance(s.focus_tags, posting_tags) == best_score]


def select_summary(cv: MasterCV, posting_tags: set[str], language: str):
    return get_summary_candidates(cv, posting_tags, language)[0]


def select_certifications(cv: MasterCV, posting_tags: set[str], max_certs: int = MAX_CERTIFICATIONS) -> list[Certification]:
    ranked = sorted(
        enumerate(cv.certifications),
        key=lambda pair: (-_relevance(pair[1].tags, posting_tags), pair[0]),
    )
    return [c for _, c in ranked[:max_certs]]

def format_certification_lines(certs: list[Certification], language: str) -> list[str]:
    lines = []
    for c in certs:
        if c.status == "in_progress":
            status = "en curso" if language == "es" else "in progress"
            lines.append(f"{c.name} — {c.issuer} — {status}, {c.date}")
        else:
            lines.append(f"{c.name} — {c.issuer} — {c.date}")
    return lines


def select_skill_groups(cv: MasterCV, posting_tags: set[str], max_groups: int = MAX_SKILL_GROUPS) -> list[SkillGroup]:
    ranked = sorted(
        enumerate(cv.skills),
        key=lambda pair: (-_relevance(pair[1].tags, posting_tags), pair[0]),
    )
    chosen = [sg for _, sg in ranked[:max_groups]]
    return chosen or cv.skills[:1]


def select_experience_bullets(cv: MasterCV, posting_tags: set[str], language: str) -> list[ExperienceBlock]:
    """Greedy budget allocation: every entry keeps its top MIN_BULLETS_PER_ENTRY
    bullets by relevance, then remaining budget goes to the highest-relevance
    bullets across all entries, wherever they are."""
    per_entry_ranked: dict[str, list[tuple[int, int]]] = {}  # entry.id -> [(bullet_idx, score), ...] desc by score
    for e in cv.experience:
        scored = sorted(
            range(len(e.bullets)),
            key=lambda i: (-_relevance(e.bullets[i].tags, posting_tags), i),
        )
        per_entry_ranked[e.id] = scored

    selected: dict[str, set[int]] = {e.id: set() for e in cv.experience}
    budget = TOTAL_BULLET_BUDGET

    # guarantee a floor per entry first
    for e in cv.experience:
        floor = min(MIN_BULLETS_PER_ENTRY, len(e.bullets))
        for idx in per_entry_ranked[e.id][:floor]:
            selected[e.id].add(idx)
            budget -= 1

    # spend remaining budget on the single highest-relevance unselected bullet, repeatedly
    while budget > 0:
        best = None  # (score, entry_id, bullet_idx)
        for e in cv.experience:
            for idx in per_entry_ranked[e.id]:
                if idx in selected[e.id]:
                    continue
                score = _relevance(e.bullets[idx].tags, posting_tags)
                if best is None or score > best[0]:
                    best = (score, e.id, idx)
                break  # only consider each entry's next-best unselected bullet per round
        if best is None:
            break
        _, entry_id, idx = best
        selected[entry_id].add(idx)
        budget -= 1

    blocks = []
    for e in cv.experience:
        role = e.role_es if language == "es" else e.role_en
        end = e.end
        if end.strip().lower() in ("presente", "present"):
            end = "Presente" if language == "es" else "Present"
        dates = f"{e.start} – {end}"
        ordered_idxs = sorted(selected[e.id])  # keep original bullet order within the entry
        bullets = [e.bullets[i].text_es if language == "es" else e.bullets[i].text_en for i in ordered_idxs]
        blocks.append(ExperienceBlock(e.company, role, e.location, dates, bullets))
    return blocks


def select_project_blocks(cv: MasterCV, posting_tags: set[str], language: str) -> list[ProjectBlock]:
    blocks = []
    for p in cv.projects:
        relevant = _relevance(p.tags, posting_tags) > 0
        candidate_bullets = p.bullets if relevant else [b for b in p.bullets if b.length == "short"] or p.bullets[:1]
        texts = [b.text_es if language == "es" else b.text_en for b in candidate_bullets]
        blocks.append(ProjectBlock(p.name, texts))
    return blocks


def build_education_blocks(cv: MasterCV, language: str, include_notes: bool = False) -> list[EducationBlock]:
    blocks = []
    for ed in cv.education:
        degree = ed.degree_es if language == "es" else ed.degree_en
        notes = (ed.notes_es if language == "es" else ed.notes_en) if include_notes else ""
        dates = f"{ed.start} – {ed.end}"
        blocks.append(EducationBlock(ed.institution, [degree], ed.location, dates, notes))
    return blocks


def select_anecdotes(cv: MasterCV, posting_tags: set[str], language: str, max_n: int = 3) -> list:
    """Always includes the generic dual-degree/full-time-work anecdote (no
    tags — it's context, not a pitch), then the highest-relevance tagged ones."""
    generic = [a for a in cv.anecdotes if not a.tags]
    tagged = [a for a in cv.anecdotes if a.tags]
    ranked_tagged = sorted(tagged, key=lambda a: -_relevance(a.tags, posting_tags))
    relevant_tagged = [a for a in ranked_tagged if _relevance(a.tags, posting_tags) > 0]
    chosen = generic[:1] + relevant_tagged
    if len(chosen) < max_n:
        # pad with remaining tagged anecdotes even if not tag-matched, so a
        # short/generic posting still gets a substantive letter
        remaining = [a for a in ranked_tagged if a not in chosen]
        chosen += remaining[: max_n - len(chosen)]
    return chosen[:max_n]


def anecdote_text(anecdote, language: str) -> str:
    return anecdote.text_es if language == "es" else anecdote.text_en


def build_cv_content(
    cv: MasterCV,
    posting_text: str,
    language: str | None = None,
    summary_variant=None,
    section_order: list[str] | None = None,
) -> CVContent:
    language = language or detect_language(posting_text)
    posting_tags = detect_tags_in_text(posting_text)

    summary = summary_variant or select_summary(cv, posting_tags, language)
    certs = select_certifications(cv, posting_tags)
    skill_groups = select_skill_groups(cv, posting_tags)
    experience_blocks = select_experience_bullets(cv, posting_tags, language)
    project_blocks = select_project_blocks(cv, posting_tags, language)
    education_blocks = build_education_blocks(cv, language, include_notes=False)

    skill_lines = [", ".join(sg.items_es if language == "es" else sg.items_en) for sg in skill_groups]
    lang_lines = []
    for l in cv.languages:
        name = l.name_es if language == "es" else l.name_en
        level = l.level_es if language == "es" else l.level_en
        line = f"{name} — {level}"
        if l.detail:
            detail = l.detail.split(" / ")[0 if language == "es" else -1]
            line += f" ({detail})"
        lang_lines.append(line)

    interests = cv.interests_es if language == "es" else cv.interests_en

    content = CVContent(
        language=language,
        name=cv.contact.name,
        location=cv.contact.location,
        email=cv.contact.email,
        phone=cv.contact.phone,
        linkedin_url=cv.contact.linkedin_url,
        summary=summary.text,
        experience=experience_blocks,
        projects=project_blocks,
        education=education_blocks,
        certifications=format_certification_lines(certs, language),
        languages=lang_lines,
        skills=skill_lines,
        interests=list(interests),
    )
    if section_order:
        content.section_order = section_order
    return content
