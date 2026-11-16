import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from google.genai.errors import APIError
from sqlalchemy.orm import Session

from database import get_db
from models import MarketAnalysis, Project
from schemas import AnalysisResponse, ProjectCreate
from services.gemini_service import generate_market_analysis

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/projects/{project_id}/market-analysis")
def analyse_market(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project = ProjectCreate(
        project_name=db_project.project_name,
        project_type=db_project.project_type or "Not known yet",
        description=db_project.description or "Not known yet",
        problem_being_solved=db_project.problem_being_solved or "Not known yet",
        proposed_solution=db_project.proposed_solution or "Not known yet",
        industry=db_project.industry or "Not known yet",
        target_customers=db_project.target_customers or "Not known yet",
        target_audience_description=db_project.target_audience_description or "Not known yet",
        geographic_scope=db_project.geographic_scope or "Not known yet",
        location=db_project.location,
        business_model=db_project.business_model or "Not known yet",
        budget=db_project.budget,
        budget_currency=db_project.budget_currency,
        budget_status=db_project.budget_status or "Not known yet",
        runway_months=db_project.runway_months,
        runway_status=db_project.runway_status or "Not known yet",
        known_competitors=db_project.known_competitors or [],
        competitors_status=db_project.competitors_status or "unknown",
    )

    db_analysis = MarketAnalysis(project_id=project_id, status="pending")
    db.add(db_analysis)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to save analysis for project %d", project_id)
        raise HTTPException(status_code=500, detail="Analysis could not be saved")
    db.refresh(db_analysis)

    try:
        raw, model_name = generate_market_analysis(project, search_results=[])
    except TimeoutError:
        logger.exception("Gemini request timed out for project %d", project_id)
        db_analysis.status = "failed"
        db_analysis.error_message = "AI analysis timed out. Please try again later."
        db.commit()
        raise HTTPException(
            status_code=504,
            detail="AI analysis timed out. Please try again later.",
        )
    except APIError as exc:
        logger.exception("Gemini API failed for project %d", project_id)
        db_analysis.status = "failed"
        db_analysis.error_message = "AI analysis is temporarily unavailable. Please try again later."
        db.commit()
        status_code = 504 if exc.code == 504 else 502
        detail = (
            "AI analysis timed out. Please try again later."
            if status_code == 504
            else "AI analysis is temporarily unavailable. Please try again later."
        )
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception:
        logger.exception("Gemini call failed for project %d", project_id)
        db_analysis.status = "failed"
        db_analysis.error_message = "AI analysis could not be generated. Please try again later."
        db.commit()
        raise HTTPException(
            status_code=502,
            detail="AI analysis could not be generated. Please try again later.",
        )

    raw["missing_information"] = sorted(
        set(raw.get("missing_information", [])) | set(project.missing_fields())
    )
    raw["competitor_analysis"] = {
        "status": "insufficient",
        "status_reason": "Live competitor search is not configured; user-submitted competitors are unverified.",
        "competitors": [],
        "comparison": [],
        "competitive_advantages": [],
        "competitive_gaps": [],
    }

    warnings = []
    try:
        validated = AnalysisResponse(
            project_id=project_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            model=model_name,
            **raw,
        )
    except Exception:
        logger.exception("Pydantic validation failed for project %d", project_id)
        db_analysis.status = "failed"
        db_analysis.error_message = "Analysis returned invalid data."
        db.commit()
        raise HTTPException(status_code=502, detail="AI analysis returned invalid data")

    competitor_analysis = validated.competitor_analysis
    if competitor_analysis.status in {"partial", "insufficient"}:
        warnings.append(
            f"Competitor status: {competitor_analysis.status} — "
            f"{competitor_analysis.status_reason}"
        )

    result = validated.model_dump()
    db_analysis.status = "complete"
    db_analysis.model_used = model_name
    db_analysis.analysis_json = result
    db_analysis.warnings = warnings or None
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to save analysis for project %d", project_id)
        raise HTTPException(status_code=500, detail="Analysis could not be saved")

    return {
        "message": "Market analysis completed",
        "project_id": project_id,
        "analysis": result,
    }


@router.get("/projects/{project_id}/market-analysis")
def get_market_analysis(project_id: int, db: Session = Depends(get_db)):
    analyses = (
        db.query(MarketAnalysis)
        .filter(MarketAnalysis.project_id == project_id)
        .order_by(MarketAnalysis.created_at.desc())
        .all()
    )
    if not analyses:
        raise HTTPException(
            status_code=404, detail="No analysis found for this project"
        )

    latest = analyses[0]
    return {
        "project_id": project_id,
        "status": latest.status,
        "model_used": latest.model_used,
        "warnings": latest.warnings,
        "analysis": latest.analysis_json,
    }
