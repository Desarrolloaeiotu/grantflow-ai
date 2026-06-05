"""Schemas for organization strategic analysis responses."""
from typing import Literal

from pydantic import BaseModel, Field


class AnalysisSection(BaseModel):
    """Individual section of strategic analysis."""

    text: str = Field(..., max_length=150, description="Concise analysis (max 150 chars)")
    conclusion: str = Field(..., description="Section conclusion")


class AnalysisResult(BaseModel):
    """Complete strategic analysis result for an organization."""

    capital: AnalysisSection = Field(
        ...,
        description="Capital availability: funding type, amounts, stage",
    )
    model_export: AnalysisSection = Field(
        ...,
        description="Interest in scaling/exporting educational models",
    )
    network: AnalysisSection = Field(
        ...,
        description="Strategic positioning value and network articulation",
    )
    colombia: AnalysisSection = Field(
        ...,
        description="Active projects in Colombia",
    )
    latam: AnalysisSection = Field(
        ...,
        description="Operations and programs in Latin America",
    )
    primary_role: Literal["capital", "exportacion", "posicionamiento"] = Field(
        ...,
        description="Primary strategic role for aeioTU",
    )
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Confidence level of the analysis",
    )
