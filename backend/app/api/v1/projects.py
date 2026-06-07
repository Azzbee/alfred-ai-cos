"""Projects endpoints (PRD 15.1 Project).

Mobile surface:
  - GET    /api/v1/projects                  → list (proposed + accepted)
  - POST   /api/v1/projects                  → user creates a named project
  - POST   /api/v1/projects/propose          → run auto-clustering
  - POST   /api/v1/projects/{id}/accept      → promote a proposed cluster
  - DELETE /api/v1/projects/{id}             → archive (accepted) or reject (proposed)
  - POST   /api/v1/projects/{id}/status      → set status
  - POST   /api/v1/projects/{id}/commitments → attach commitment_ids
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.enums import CommitmentStatus, ProjectStatus
from app.db.models import Commitment, Project, User
from app.services import projects as projects_service

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str | None
    status: ProjectStatus
    related_people: list[str]
    keyword_tokens: list[str]
    is_proposed: bool
    open_commitment_count: int

    model_config = {"from_attributes": True}


class CreateProjectRequest(BaseModel):
    name: str
    description: str | None = None


class AttachCommitmentsRequest(BaseModel):
    commitment_ids: list[str]


class StatusUpdate(BaseModel):
    status: ProjectStatus


def _to_out(db: Session, project: Project) -> ProjectOut:
    from sqlalchemy import func

    open_count = (
        db.scalar(
            select(func.count(Commitment.id)).where(
                Commitment.project_id == project.id,
                Commitment.status == CommitmentStatus.open,
            )
        )
        or 0
    )
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        related_people=project.related_people or [],
        keyword_tokens=project.keyword_tokens or [],
        is_proposed=project.is_proposed,
        open_commitment_count=int(open_count),
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectOut]:
    rows = list(
        db.scalars(
            select(Project)
            .where(Project.user_id == user.id)
            .order_by(Project.is_proposed.desc(), Project.created_at.desc())
        )
    )
    return [_to_out(db, p) for p in rows]


@router.post("", response_model=ProjectOut)
def create_project(
    payload: CreateProjectRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectOut:
    try:
        project = projects_service.create(
            db, user, name=payload.name, description=payload.description
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(db, project)


@router.post("/propose", response_model=list[ProjectOut])
def propose(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectOut]:
    """Run the auto-clustering pass and return the newly proposed projects."""
    proposed = projects_service.propose_projects(db, user)
    return [_to_out(db, p) for p in proposed]


@router.post("/{project_id}/accept", response_model=ProjectOut)
def accept_proposed(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectOut:
    project = _owned(db, project_id, user.id)
    projects_service.accept(db, project)
    return _to_out(db, project)


@router.post("/{project_id}/status", response_model=ProjectOut)
def set_status(
    project_id: str,
    payload: StatusUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectOut:
    project = _owned(db, project_id, user.id)
    projects_service.update_status(db, project, status=payload.status)
    return _to_out(db, project)


@router.post("/{project_id}/commitments", response_model=ProjectOut)
def attach_commitments(
    project_id: str,
    payload: AttachCommitmentsRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectOut:
    project = _owned(db, project_id, user.id)
    projects_service.attach_commitments(db, project, commitment_ids=payload.commitment_ids)
    return _to_out(db, project)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    project = _owned(db, project_id, user.id)
    if project.is_proposed:
        projects_service.reject(db, project)
        return
    # Accepted projects archive rather than vanish.
    projects_service.update_status(db, project, status=ProjectStatus.archived)


def _owned(db: Session, project_id: str, user_id: str) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.user_id != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
