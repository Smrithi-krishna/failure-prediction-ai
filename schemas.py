from datetime import datetime
from typing import Literal, Optional
import logging

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

UNKNOWN_MARKERS = {"not known yet", "unknown", "n/a", ""}
CONFIDENCE_VALUES = {"high", "medium", "low"}


# Project input

class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=200)

    project_type: Literal[
        "Startup",
        "Business plan",
        "Hackathon",
        "College project",
        "Innovation concept",
        "Not known yet",
    ] = "Not known yet"

    description: str = "Not known yet"
    problem_being_solved: str = "Not known yet"
    proposed_solution: str = "Not known yet"
    industry: str = "Not known yet"

    target_customers: Literal[
        "B2B",
        "B2C",
        "B2G",
        "Internal / Academic",
        "Not known yet",
    ] = "Not known yet"

    target_audience_description: str = "Not known yet"

    geographic_scope: Literal[
        "Global",
        "Country",
        "Region / State",
        "City",
        "Not known yet",
    ] = "Not known yet"

    location: Optional[str] = None

    business_model: Literal[
        "Subscription",
        "One-time sale",
        "Marketplace",
        "Free with ads",
        "Freemium",
        "Not decided",
        "Not known yet",
    ] = "Not known yet"

    budget: Optional[float] = Field(default=None, ge=0)
    budget_currency: Optional[str] = None

    budget_status: Literal[
        "Amount",
        "None",
        "Not known yet",
    ] = "Not known yet"

    runway_months: Optional[int] = Field(default=None, ge=0)

    runway_status: Literal[
        "Enter months",
        "Not known yet",
    ] = "Not known yet"

    known_competitors: list[str] = Field(default_factory=list)

    competitors_status: Literal[
        "provided",
        "none",
        "unknown",
    ] = "unknown"

    @field_validator(
        "project_name",
        "project_type",
        "description",
        "problem_being_solved",
        "proposed_solution",
        "industry",
        "target_customers",
        "target_audience_description",
        "geographic_scope",
        "business_model",
        "budget_status",
        "runway_status",
    )
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "must not be blank; use 'Not known yet' if unknown"
            )
        return v

    @field_validator("description")
    @classmethod
    def description_min_length(cls, v: str) -> str:
        if (
            v.strip().lower() not in UNKNOWN_MARKERS
            and len(v.strip()) < 50
        ):
            raise ValueError(
                "description must be at least 50 characters"
            )
        return v

    @model_validator(mode="after")
    def budget_requires_currency(self):
        if self.budget_status == "Amount" and (
            self.budget is None or not self.budget_currency
        ):
            raise ValueError(
                "An amount and currency are required when budget is Amount"
            )

        if (
            self.competitors_status == "provided"
            and not self.known_competitors
        ):
            raise ValueError("Provide at least one competitor")

        if (
            self.competitors_status != "provided"
            and self.known_competitors
        ):
            raise ValueError(
                "Competitor names require provided status"
            )

        return self

    def missing_fields(self) -> list[str]:
        missing = []

        for name, value in self.model_dump().items():
            if value is None:
                missing.append(name)
            elif (
                isinstance(value, str)
                and value.strip().lower() in UNKNOWN_MARKERS
            ):
                missing.append(name)

        if self.competitors_status == "unknown":
            missing.append("known_competitors")

        return missing


class ProjectResponse(BaseModel):
    id: int
    project_name: str
    project_type: str
    description: str
    problem_being_solved: str
    proposed_solution: str
    industry: str
    target_customers: str
    target_audience_description: str
    geographic_scope: str
    location: Optional[str]
    business_model: str
    budget: Optional[float]
    budget_currency: Optional[str]
    budget_status: str
    runway_months: Optional[int]
    runway_status: str
    known_competitors: list[str]
    competitors_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Milestone 1 - Market analysis output

class MarketSize(BaseModel):
    value: Optional[float]
    unit: Optional[str]
    source: Optional[str]
    confidence: str

    @field_validator("confidence")
    @classmethod
    def valid_confidence(cls, v: str) -> str:
        if v not in CONFIDENCE_VALUES:
            raise ValueError(
                f"confidence must be one of {CONFIDENCE_VALUES}"
            )
        return v


class GrowthTrend(BaseModel):
    trend: str
    evidence: str
    source_url: Optional[str]
    confidence: str

    @field_validator("confidence")
    @classmethod
    def valid_confidence(cls, v: str) -> str:
        if v not in CONFIDENCE_VALUES:
            raise ValueError(
                f"confidence must be one of {CONFIDENCE_VALUES}"
            )
        return v


class MarketAnalysis(BaseModel):
    market_summary: str
    target_market_description: str
    market_size: MarketSize
    growth_trends: list[GrowthTrend]
    opportunities: list[str]
    challenges: list[dict]
    data_date_range: Optional[str]

    @model_validator(mode="after")
    def drop_unverified_trends(self) -> "MarketAnalysis":
        clean = [
            trend
            for trend in self.growth_trends
            if trend.source_url
        ]

        dropped = len(self.growth_trends) - len(clean)

        if dropped:
            logger.warning(
                "Dropped %d growth trend(s) missing source_url",
                dropped,
            )

        self.growth_trends = clean
        return self


class Competitor(BaseModel):
    name: str
    description: Optional[str] = None
    positioning: Optional[str] = None
    source_url: str
    verified_from_search: bool = False
    confidence: str

    @field_validator("confidence")
    @classmethod
    def valid_confidence(cls, v: str) -> str:
        if v not in CONFIDENCE_VALUES:
            raise ValueError(
                f"confidence must be one of {CONFIDENCE_VALUES}"
            )
        return v


class CompetitorAnalysis(BaseModel):
    status: str
    status_reason: str
    competitors: list[Competitor]
    comparison: list[dict]
    competitive_advantages: list[str]
    competitive_gaps: list[str]

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        if v not in {"found", "partial", "insufficient"}:
            raise ValueError(
                "status must be found, partial, or insufficient"
            )
        return v

    @model_validator(mode="after")
    def drop_unverified_competitors(self) -> "CompetitorAnalysis":
        clean = [
            competitor
            for competitor in self.competitors
            if (
                competitor.source_url
                and competitor.verified_from_search
            )
        ]

        dropped = len(self.competitors) - len(clean)

        if dropped:
            logger.warning(
                "Dropped %d competitor(s) missing source_url",
                dropped,
            )

        self.competitors = clean

        if len(self.competitors) < 2:
            self.status = "insufficient"
            self.status_reason = (
                "Fewer than two competitors have verified search sources."
            )

        return self


class AnalysisResponse(BaseModel):
    project_id: int
    generated_at: str
    model: str
    market_analysis: MarketAnalysis
    competitor_analysis: CompetitorAnalysis
    missing_information: list[str]
    assumptions: list[str]
    overall_confidence: str

    @field_validator("overall_confidence")
    @classmethod
    def valid_confidence(cls, v: str) -> str:
        if v not in CONFIDENCE_VALUES:
            raise ValueError(
                f"overall_confidence must be one of {CONFIDENCE_VALUES}"
            )
        return v


# Milestone 2 - Risk, SWOT, and feasibility output

class RiskAssessment(BaseModel):
    score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )
    level: Literal["low", "medium", "high", "unknown"]
    factors: list[str]
    explanation: str


class SWOTAnalysis(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]


class FeasibilityAssessment(BaseModel):
    score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )
    verdict: Literal[
        "feasible",
        "feasible_with_conditions",
        "not_feasible",
        "insufficient_information",
    ]
    explanation: str
    constraints: list[str]


class AssessmentResult(BaseModel):
    risk: RiskAssessment
    swot: SWOTAnalysis
    feasibility: FeasibilityAssessment
    missing_information: list[str]
    assumptions: list[str]


class AssessmentResponse(BaseModel):
    project_id: int
    assessment_id: int
    created_at: datetime
    result: AssessmentResult