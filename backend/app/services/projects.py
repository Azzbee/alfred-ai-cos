"""Project service (PRD 14.1 agent 7, PRD 15.1 Project).

Two paths into a Project row:

  1. **User-created** (`create(...)`). The user names a project on the
     Projects screen, then attaches commitments to it (the mobile UI passes
     commitment ids; we set `Commitment.project_id`).

  2. **Auto-clustered** (`propose_projects(...)`). The service scans the
     user's open commitments and proposes clusters by shared
     counterparty-person + keyword overlap. Proposed rows are stored with
     `is_proposed=True`; the user accepts or rejects on the screen.

A commitment can belong to at most one project at a time. Re-attaching to a
new project clears the old link."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import CommitmentStatus, ProjectStatus
from app.db.models import Commitment, Person, Project, User

# Tokens we treat as filler for keyword clustering — same shape as the
# extraction stopwords but cut down to project-naming relevance.
_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "to",
        "for",
        "of",
        "and",
        "or",
        "in",
        "on",
        "at",
        "by",
        "your",
        "you",
        "with",
        "this",
        "that",
        "is",
        "are",
        "be",
        "send",
        "make",
        "please",
        "review",
        "approve",
        "sign",
        "confirm",
        "follow",
        "reply",
        "draft",
        "thanks",
    }
)


@dataclass
class ProposedCluster:
    """A speculative project cluster discovered by `propose_projects`."""

    name: str
    related_emails: list[str]
    keyword_tokens: list[str]
    commitment_ids: list[str]


# ---------- user-driven CRUD ----------


def create(
    db: Session,
    user: User,
    *,
    name: str,
    description: str | None = None,
) -> Project:
    """Create a user-named project. Idempotent on (user_id, name): re-creating
    the same name returns the existing row so the mobile UI can stay simple."""
    name = name.strip()
    if not name:
        raise ValueError("Project name required")
    existing = db.scalar(select(Project).where(Project.user_id == user.id, Project.name == name))
    if existing is not None:
        if existing.is_proposed:
            existing.is_proposed = False  # accept-by-recreate
            db.commit()
        return existing
    project = Project(
        user_id=user.id,
        name=name,
        description=description,
        status=ProjectStatus.active,
        is_proposed=False,
    )
    db.add(project)
    db.commit()
    return project


def attach_commitments(db: Session, project: Project, *, commitment_ids: list[str]) -> int:
    """Set `Commitment.project_id` on each id that belongs to the same user.
    Returns the count attached."""
    if not commitment_ids:
        return 0
    rows = list(
        db.scalars(
            select(Commitment).where(
                Commitment.user_id == project.user_id,
                Commitment.id.in_(commitment_ids),
            )
        )
    )
    for c in rows:
        c.project_id = project.id
    db.commit()
    return len(rows)


def detach_commitment(db: Session, commitment: Commitment) -> Commitment:
    """Clear the project link on one commitment. Useful when the user moves
    an item out of a project."""
    commitment.project_id = None
    db.commit()
    return commitment


def update_status(db: Session, project: Project, *, status: ProjectStatus) -> Project:
    project.status = status
    db.commit()
    return project


def accept(db: Session, project: Project) -> Project:
    """Promote a proposed project to a real one (`is_proposed=False`)."""
    project.is_proposed = False
    db.commit()
    return project


def reject(db: Session, project: Project) -> None:
    """Delete a proposed project. Commitments stay; the cluster suggestion
    just goes away. Real projects must use status=archived instead."""
    if not project.is_proposed:
        raise ValueError("Use status=archived on accepted projects, not delete")
    db.delete(project)
    db.commit()


# ---------- auto-clustering ----------


def _tokens(text: str) -> set[str]:
    """Return distinctive 4+-char tokens for clustering."""
    if not text:
        return set()
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) >= 4 and w not in _STOPWORDS}


def propose_projects(
    db: Session,
    user: User,
    *,
    min_cluster_size: int = 3,
    min_keyword_overlap: int = 2,
) -> list[Project]:
    """Scan open commitments and propose project clusters. Two clustering
    signals:

      A. Shared `counterparty_person_id` — if N commitments point at the
         same Person AND share keyword tokens, that's almost certainly one
         deal / project. Project name defaults to the person's organization
         or display name.

      B. Keyword overlap without a shared person — emerging projects where
         the counterparty differs but the language is consistent (e.g. an
         RFP that goes to multiple vendors).

    Persists proposed Project rows (idempotent: if a proposed project with
    the same composition already exists, skip)."""
    open_commits = list(
        db.scalars(
            select(Commitment).where(
                Commitment.user_id == user.id,
                Commitment.status == CommitmentStatus.open,
            )
        )
    )
    if len(open_commits) < min_cluster_size:
        return []

    # Map commitment.id -> (token_set, person_id, counterparty)
    commit_meta: dict[str, tuple[set[str], str | None, str | None]] = {}
    for c in open_commits:
        toks = _tokens(f"{c.description or ''} {c.evidence or ''}")
        commit_meta[c.id] = (toks, c.counterparty_person_id, c.counterparty)

    proposed: list[Project] = []
    seen_signatures: set[str] = _existing_signatures(db, user.id)

    # Path A: cluster by shared person.
    by_person: dict[str, list[Commitment]] = defaultdict(list)
    for c in open_commits:
        if c.counterparty_person_id:
            by_person[c.counterparty_person_id].append(c)
    for person_id, commits in by_person.items():
        if len(commits) < min_cluster_size:
            continue
        # Confirm at least min_keyword_overlap shared tokens across cluster.
        token_lists = [commit_meta[c.id][0] for c in commits]
        shared = set.intersection(*token_lists) if token_lists else set()
        if len(shared) < min_keyword_overlap:
            continue
        person = db.get(Person, person_id)
        name = (
            person.organization
            or (person.name if person else None)
            or commits[0].counterparty
            or "Untitled project"
        )
        cluster = ProposedCluster(
            name=str(name)[:200],
            related_emails=[person.email_lower] if person else [],
            keyword_tokens=sorted(shared)[:8],
            commitment_ids=[c.id for c in commits],
        )
        sig = _signature(cluster)
        if sig in seen_signatures:
            continue
        seen_signatures.add(sig)
        proposed.append(_persist_proposed(db, user, cluster))

    # Path B: keyword-driven clusters across different counterparties. Greedy:
    # pick the largest pairwise overlap, group commitments that share it,
    # repeat. Skips commitments already in a Path A cluster.
    consumed: set[str] = {cid for p in proposed for cid in _commit_ids_for(db, p)}
    remaining = [c for c in open_commits if c.id not in consumed]
    while True:
        cluster = _largest_keyword_cluster(
            remaining, commit_meta, min_cluster_size, min_keyword_overlap
        )
        if cluster is None:
            break
        sig = _signature(cluster)
        if sig not in seen_signatures:
            seen_signatures.add(sig)
            proposed.append(_persist_proposed(db, user, cluster))
        # Remove its members and loop.
        member_ids = set(cluster.commitment_ids)
        remaining = [c for c in remaining if c.id not in member_ids]

    db.commit()
    return proposed


def _largest_keyword_cluster(
    commits: list[Commitment],
    commit_meta: dict[str, tuple[set[str], str | None, str | None]],
    min_size: int,
    min_overlap: int,
) -> ProposedCluster | None:
    """Find the biggest group of commitments that share `min_overlap` tokens."""
    if len(commits) < min_size:
        return None
    # Build a token → commitment_ids index.
    by_token: dict[str, set[str]] = defaultdict(set)
    for c in commits:
        toks = commit_meta[c.id][0]
        for t in toks:
            by_token[t].add(c.id)
    # Score each candidate group: a token's score is its membership count.
    # We want the LARGEST set of commitments that all share ≥ min_overlap tokens.
    # Approximation: pick the token with the most members; intersect with the
    # next-most token; keep going while the intersection size ≥ min_size.
    ranked = sorted(by_token.items(), key=lambda kv: -len(kv[1]))
    if not ranked or len(ranked[0][1]) < min_size:
        return None
    # Start from the top token.
    current_set = set(ranked[0][1])
    used_tokens = [ranked[0][0]]
    for tok, members in ranked[1:]:
        if len(used_tokens) >= 6:
            break
        candidate = current_set & members
        if len(candidate) >= min_size:
            current_set = candidate
            used_tokens.append(tok)
            if len(used_tokens) >= min_overlap and len(current_set) >= min_size:
                # Stop growing once we have enough overlap; otherwise the
                # cluster gets too narrow.
                if len(current_set) == min_size:
                    break
    if len(used_tokens) < min_overlap or len(current_set) < min_size:
        return None
    member_emails: set[str] = set()
    for cid in current_set:
        _, _, cp = commit_meta[cid]
        if cp:
            from app.services.people import _parse_email

            _, email = _parse_email(cp)
            if email:
                member_emails.add(email)
    name = " · ".join(used_tokens[:3]).title()
    return ProposedCluster(
        name=name[:200],
        related_emails=sorted(member_emails),
        keyword_tokens=used_tokens,
        commitment_ids=sorted(current_set),
    )


def _persist_proposed(db: Session, user: User, cluster: ProposedCluster) -> Project:
    proj = Project(
        user_id=user.id,
        name=cluster.name,
        description=None,
        status=ProjectStatus.active,
        related_people=cluster.related_emails,
        keyword_tokens=cluster.keyword_tokens,
        is_proposed=True,
    )
    db.add(proj)
    db.flush()
    # Attach the cluster's commitments to this proposed project so the user
    # immediately sees the group when reviewing.
    for cid in cluster.commitment_ids:
        c = db.get(Commitment, cid)
        if c is not None and c.project_id is None:
            c.project_id = proj.id
    return proj


def _existing_signatures(db: Session, user_id: str) -> set[str]:
    """Signatures of already-proposed (or accepted) projects so the same
    cluster isn't re-suggested every run."""
    sigs: set[str] = set()
    for p in db.scalars(select(Project).where(Project.user_id == user_id)):
        sigs.add(_signature_from_fields(p.related_people or [], p.keyword_tokens or []))
    return sigs


def _signature(cluster: ProposedCluster) -> str:
    return _signature_from_fields(cluster.related_emails, cluster.keyword_tokens)


def _signature_from_fields(emails: list[str], tokens: list[str]) -> str:
    return f"{sorted(set(e.lower() for e in emails))}|{sorted(set(tokens))}"


def _commit_ids_for(db: Session, project: Project) -> list[str]:
    rows = db.scalars(select(Commitment.id).where(Commitment.project_id == project.id))
    return list(rows)
