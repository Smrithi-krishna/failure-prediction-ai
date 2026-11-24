from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Project, ProjectAssessment
from schemas import AssessmentResponse, AssessmentResult

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


@router.get(
    "/projects/{project_id}/assessment",
    response_model=AssessmentResponse,
)
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

    assessment = (
        db.query(ProjectAssessment)
        .filter(ProjectAssessment.project_id == project_id)
        .order_by(
            ProjectAssessment.created_at.desc(),
            ProjectAssessment.id.desc(),
        )
        .first()
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="No assessment found for this project",
        )

    result = AssessmentResult(
        risk={
            "score": assessment.risk_score,
            "level": assessment.risk_level,
            "factors": assessment.risk_factors,
            "explanation": assessment.risk_explanation,
        },
        swot=assessment.swot_analysis,
        feasibility={
            "score": assessment.feasibility_score,
            "verdict": assessment.feasibility_verdict,
            "explanation": assessment.feasibility_explanation,
            "constraints": assessment.feasibility_constraints,
        },
        missing_information=assessment.missing_information,
        assumptions=assessment.assumptions,
    )

    return AssessmentResponse(
        project_id=project_id,
        assessment_id=assessment.id,
        created_at=assessment.created_at,
        result=result,
    )