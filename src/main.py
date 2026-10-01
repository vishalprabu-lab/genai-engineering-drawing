"""Command-line entry point.

Usage (from the project root):
    python -m src.main --drawing data/easy/example.pdf [--page 0] [--dry-run]

Just calls the same functions the notebook uses -- no separate logic.
"""

import argparse

from src.formatter import format_review
from src.reviewer import review_drawing


def main() -> None:
    """Parse command-line arguments, run the review and print the report."""
    # Define the supported arguments.
    parser = argparse.ArgumentParser(description="Review an engineering drawing PDF with Gemini.")
    parser.add_argument("--drawing", required=True, help="Path to the drawing PDF (relative to the project root or absolute).")
    parser.add_argument("--page", type=int, default=0, help="0-based page number to review (default 0).")
    parser.add_argument("--dry-run", action="store_true", help="Assemble and print the request without calling the API.")
    args = parser.parse_args()

    # Run the review; in dry-run mode this prints the request and returns it.
    result = review_drawing(args.drawing, page=args.page, dry_run=args.dry_run)

    # Only a real run returns a DrawingReview that can be formatted as a report.
    if not args.dry_run:
        print(format_review(result))


if __name__ == "__main__":
    main()
