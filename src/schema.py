"""Pydantic models describing the structured review the LLM must return.

These classes serve two purposes: they are passed to Gemini as the response
schema (so the output is JSON in this exact shape), and they validate the
response once it comes back. Optional[str] fields use None to mean
"not found on the drawing", which is itself a meaningful review result.
"""

from typing import Literal, Optional

from pydantic import BaseModel


class DrawingIdentification(BaseModel):
    """Title-block information that identifies the drawing."""

    drawing_number: Optional[str] = None
    title: Optional[str] = None
    revision: Optional[str] = None
    scale: Optional[str] = None
    sheet: Optional[str] = None


class Specifications(BaseModel):
    """Manufacturing specifications stated on the drawing."""

    material: Optional[str] = None
    heat_treatment: Optional[str] = None
    surface_finish: Optional[str] = None
    general_tolerance: Optional[str] = None


class DimensionsSummary(BaseModel):
    """High-level summary of the dimensioning on the drawing."""

    overall_dimensions: str          # e.g. "120 x 60 x 25 mm"
    total_dimensions_found: int      # rough count of dimensions visible
    dimensions_with_tolerance: int   # how many of those carry an explicit tolerance


class Finding(BaseModel):
    """One error or concern found on the drawing."""

    category: str                          # e.g. "Missing dimension", "Missing datum"
    severity: Literal["high", "medium", "low"]
    location: str                          # where on the drawing (view, zone, feature)
    description: str                       # what is wrong
    recommendation: str                    # how to fix it


class DrawingReview(BaseModel):
    """Complete review of a single drawing -- the top-level output model."""

    identification: DrawingIdentification
    description: str                       # what the drawing shows
    specifications: Specifications
    dimensions: DimensionsSummary
    findings: list[Finding]                # priority: missing dimensions / missing datums; empty if none
    other_issues: list[Finding]            # any other error or concern; empty if none
    overall_assessment: str                # short verdict for the scanning engineer
