from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Project

router = APIRouter(tags=["Milestone 2"])


@router.post("/projects/{project_id}/assessment")
def create_assessment(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    raise HTTPException(
        status_code=501,
        detail="Assessment generation is awaiting the assessment service.",
    )


@router.get("/projects/{project_id}/assessment")
def get_assessment(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    raise HTTPException(
        status_code=501,
        detail="Assessment retrieval is awaiting database integration.",
    )