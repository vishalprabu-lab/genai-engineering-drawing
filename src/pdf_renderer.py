"""Render one page of a PDF drawing to a PNG image using PyMuPDF.

The PNG is what gets sent to Gemini. Rendered images are cached in outputs/:
if the PNG for a given PDF/page/DPI already exists it is reused.
"""

from pathlib import Path

import pymupdf  # PyMuPDF

from src.config import OUTPUT_DIR, RENDER_DPI


def render_pdf_page(pdf_path, page: int = 0, dpi: int = RENDER_DPI) -> Path:
    """Render `page` (0-based) of `pdf_path` to a PNG and return the PNG path.

    Skips rendering if the PNG already exists.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Encode page and DPI in the filename so different settings never collide in the cache.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUTPUT_DIR / f"{pdf_path.stem}_p{page}_{dpi}dpi.png"

    # Simple cache: reuse the existing image instead of re-rendering.
    if png_path.exists():
        print(f"[render] Using cached image: {png_path.name}")
        return png_path

    # Open the PDF and validate the requested page number.
    with pymupdf.open(pdf_path) as doc:
        if not 0 <= page < doc.page_count:
            raise ValueError(
                f"Page {page} out of range: {pdf_path.name} has {doc.page_count} page(s) "
                f"(valid range 0-{doc.page_count - 1})."
            )

        # Rasterise the page at the requested DPI and write it out as PNG.
        pixmap = doc[page].get_pixmap(dpi=dpi)
        pixmap.save(png_path)

    print(f"[render] Rendered {pdf_path.name} page {page} at {dpi} DPI -> {png_path.name}")
    return png_path
