"""Turn a DrawingReview into a readable plain-text report.

Sections always appear in the same order with the same headers, so reports
look identical across drawings and gaps are easy to spot.
"""

from src.schema import DrawingReview

NOT_SPECIFIED = "Not specified"
_LINE = "=" * 70


def _value(text) -> str:
    """Return the text, or 'Not specified' if it is None/empty (makes gaps visible)."""
    return text if text else NOT_SPECIFIED


def _section(title: str) -> str:
    """Return a section header block."""
    return f"\n{title}\n{'-' * len(title)}"


def format_review(review: DrawingReview) -> str:
    """Build the full text report for a review."""
    lines = [_LINE, "ENGINEERING DRAWING REVIEW", _LINE]

    # Section 1: identification fields from the title block.
    ident = review.identification
    lines.append(_section("1. DRAWING IDENTIFICATION"))
    lines.append(f"Drawing number : {_value(ident.drawing_number)}")
    lines.append(f"Title          : {_value(ident.title)}")
    lines.append(f"Revision       : {_value(ident.revision)}")
    lines.append(f"Scale          : {_value(ident.scale)}")
    lines.append(f"Sheet          : {_value(ident.sheet)}")

    # Section 2: what the drawing shows.
    lines.append(_section("2. DESCRIPTION"))
    lines.append(_value(review.description))

    # Section 3: manufacturing specifications.
    specs = review.specifications
    lines.append(_section("3. SPECIFICATIONS"))
    lines.append(f"Material          : {_value(specs.material)}")
    lines.append(f"Heat treatment    : {_value(specs.heat_treatment)}")
    lines.append(f"Surface finish    : {_value(specs.surface_finish)}")
    lines.append(f"General tolerance : {_value(specs.general_tolerance)}")

    # Section 4: dimensioning summary.
    dims = review.dimensions
    lines.append(_section("4. DIMENSIONS SUMMARY"))
    lines.append(f"Overall dimensions        : {_value(dims.overall_dimensions)}")
    lines.append(f"Total dimensions found    : {dims.total_dimensions_found}")
    lines.append(f"Dimensions with tolerance : {dims.dimensions_with_tolerance}")

    # Section 5: findings, or an explicit statement that there are none.
    lines.append(_section(f"5. FINDINGS ({len(review.findings)})"))
    if not review.findings:
        lines.append("No findings - no errors were identified on this drawing.")
    for number, finding in enumerate(review.findings, start=1):
        lines.append(f"{number}. [{finding.severity.upper()}] {finding.category}")
        lines.append(f"   Location       : {finding.location}")
        lines.append(f"   Issue          : {finding.description}")
        lines.append(f"   Recommendation : {finding.recommendation}")

    # Section 6: overall verdict.
    lines.append(_section("6. OVERALL ASSESSMENT"))
    lines.append(_value(review.overall_assessment))
    lines.append(_LINE)

    return "\n".join(lines)
