"""Orchestrates a drawing review: PDF -> PNG -> Gemini -> validated DrawingReview.

Also provides list_available_drawings() so the notebook can show what PDFs exist.
Used by both the notebook and the CLI (src/main.py).
"""

from pathlib import Path

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from src.config import DATA_DIR, GEMINI_MODEL, OUTPUT_DIR, PROJECT_ROOT, get_api_key
from src.pdf_renderer import render_pdf_page
from src.prompts import SYSTEM_PROMPT
from src.schema import DrawingReview

# The short user message sent alongside the image (the real instructions are in the system prompt).
USER_MESSAGE = "Review this engineering drawing."


def list_available_drawings() -> list[Path]:
    """Return all PDFs found under data/easy/ and data/complex/, sorted by folder then name."""
    pdfs = []
    # Look in each difficulty folder; a missing folder is simply skipped.
    for folder in ("easy", "complex"):
        pdfs.extend(sorted((DATA_DIR / folder).glob("*.pdf")))
    return pdfs


def build_request(pdf_path, page: int = 0) -> dict:
    """Render the PDF and assemble everything that will be sent to Gemini.

    Returns a dict with the model name, system prompt, user message and image details.
    """
    # Relative paths are resolved against the project root so the CLI works from anywhere.
    pdf_path = Path(pdf_path)
    if not pdf_path.is_absolute():
        pdf_path = PROJECT_ROOT / pdf_path

    # Render the page to PNG and read the bytes that would be uploaded.
    image_path = render_pdf_page(pdf_path, page)
    image_bytes = image_path.read_bytes()

    return {
        "model": GEMINI_MODEL,
        "system_prompt": SYSTEM_PROMPT,
        "user_message": USER_MESSAGE,
        "pdf_path": pdf_path,
        "page": page,
        "image_path": image_path,
        "image_bytes": image_bytes,
        "image_mime_type": "image/png",
    }


def print_request(request: dict) -> None:
    """Print a human-readable summary of an assembled request (used by dry-run)."""
    print("=" * 70)
    print("DRY RUN - request that WOULD be sent to Gemini (no API call made)")
    print("=" * 70)
    print(f"Model        : {request['model']}")
    print(f"Source PDF   : {request['pdf_path']} (page {request['page']})")
    print(f"Image file   : {request['image_path']}")
    print(f"Image size   : {len(request['image_bytes']) / 1024:.0f} KB ({request['image_mime_type']})")
    print(f"User message : {request['user_message']}")
    print("-" * 70)
    print("SYSTEM PROMPT:")
    print("-" * 70)
    print(request["system_prompt"])


def review_drawing(pdf_path, page: int = 0, dry_run: bool = False):
    """Review one page of a drawing PDF.

    dry_run=True: print and return the assembled request dict without calling the API.
    dry_run=False: call Gemini, validate the JSON reply and return a DrawingReview
    (also saved to outputs/<name>_p<page>_review.json).
    """
    # Steps 1-2: render the image and assemble the request.
    request = build_request(pdf_path, page)

    # Dry run stops here, before anything touches the network or needs an API key.
    if dry_run:
        print_request(request)
        return request

    # Step 3: create the client (raises a helpful error if the key is missing).
    client = genai.Client(api_key=get_api_key())

    # Step 4: call Gemini, asking for JSON that conforms to the DrawingReview schema.
    print(f"[review] Calling {request['model']} ...")
    try:
        response = client.models.generate_content(
            model=request["model"],
            contents=[
                types.Part.from_bytes(
                    data=request["image_bytes"], mime_type=request["image_mime_type"]
                ),
                request["user_message"],
            ],
            config=types.GenerateContentConfig(
                system_instruction=request["system_prompt"],
                response_mime_type="application/json",
                response_schema=DrawingReview,
            ),
        )
    except errors.APIError as exc:
        # Surface the API's own status code and message rather than a generic wrapper.
        raise RuntimeError(f"Gemini API call failed (HTTP {exc.code} {exc.status}): {exc.message}") from exc

    # Step 5: an empty text reply usually means the response was blocked or cut off.
    if not response.text:
        raise RuntimeError(
            "Gemini returned no text (the response may have been blocked or truncated). "
            f"Finish reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'}"
        )

    # Step 6: validate the JSON against our schema.
    try:
        review = DrawingReview.model_validate_json(response.text)
    except ValidationError as exc:
        raise RuntimeError(
            f"Gemini's reply did not match the DrawingReview schema:\n{exc}\n\nRaw reply:\n{response.text}"
        ) from exc

    # Step 7: save the review next to the rendered image for later reference.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    review_path = OUTPUT_DIR / f"{Path(request['pdf_path']).stem}_p{page}_review.json"
    review_path.write_text(review.model_dump_json(indent=2), encoding="utf-8")
    print(f"[review] Saved review to {review_path}")

    return review
