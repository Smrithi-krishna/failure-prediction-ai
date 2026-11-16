from datetime import datetime
from typing import Any, Optional

from sqlalchemy import ForeignKey, String, Text, Float, Integer, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    project_type: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    problem_being_solved: Mapped[Optional[str]] = mapped_column(Text)
    proposed_solution: Mapped[Optional[str]] = mapped_column(Text)
    industry: Mapped[Optional[str]] = mapped_column(String(150))
    target_customers: Mapped[Optional[str]] = mapped_column(String(150))
    target_audience_description: Mapped[Optional[str]] = mapped_column(Text)
    geographic_scope: Mapped[Optional[str]] = mapped_column(String(200))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    business_model: Mapped[Optional[str]] = mapped_column(String(100))
    budget: Mapped[Optional[float]] = mapped_column(Float)
    budget_currency: Mapped[Optional[str]] = mapped_column(String(10))
    budget_status: Mapped[Optional[str]] = mapped_column(String(100))
    runway_months: Mapped[Optional[int]] = mapped_column(Integer)
    runway_status: Mapped[Optional[str]] = mapped_column(String(100))
    known_competitors: Mapped[Optional[Any]] = mapped_column(JSON)
    competitors_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    analyses: Mapped[list["MarketAnalysis"]] = relationship(
        back_populates="project",
        order_by="MarketAnalysis.created_at",
    )


class MarketAnalysis(Base):
    __tablename__ = "market_analysis"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    model_used: Mapped[Optional[str]] = mapped_column(String(100))
    analysis_json: Mapped[Optional[Any]] = mapped_column(JSON)
    warnings: Mapped[Optional[Any]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship(back_populates="analyses")
