# GenAI Engineering Drawing Review

A prototype tool that reviews engineering drawings using a vision-capable LLM.
Submit a CAD drawing as a PDF and receive a structured review: what the drawing
shows, its key specifications, and any errors found.

This is an early-stage framework intended for expansion, not a production tool.

## What it does

1. Renders a drawing PDF to a high-resolution image
2. Sends the image to Google Gemini with a fixed system prompt instructing it to
   act as a CAD/mechanical engineering reviewer
3. Returns a validated, structured review in a consistent format across all drawings

The output format is deliberately fixed so an engineer reviewing many drawings can
scan results quickly and spot gaps — a blank field (e.g. missing material or
revision) is itself a meaningful signal.

### Review output sections

| Section | Contents |
|---|---|
| Identification | Drawing number, title, revision, scale, sheet |
| Description | Part type, views present, main features |
| Specifications | Material, heat treatment, surface finish, general tolerance |
| Dimensions | Overall size, count of dimensions, how many carry tolerances |
| Findings | Priority errors (missing dimensions / datums) — category, severity, location, recommendation |
| Other issues | Any other error or concern found, in the same format |
| Assessment | One-line overall summary |

Priority error categories are **missing dimensions** and **missing datums**.

## Project structure

```
genAI-engineering-drawing/
├── app.py                  # Streamlit chat UI
├── data/
│   ├── easy/               # simpler sample drawings
│   └── complex/            # more complex sample drawings
├── notebooks/
│   └── 01_drawing_review_demo.ipynb
├── src/
│   ├── config.py           # paths, model settings, .env loading
│   ├── pdf_renderer.py     # PDF → PNG
│   ├── schema.py           # Pydantic models for structured output
│   ├── prompts.py          # system prompt
│   ├── reviewer.py         # Gemini call + orchestration
│   ├── formatter.py        # structured output → readable report
│   └── main.py             # CLI entry point
├── outputs/                # rendered images, saved reviews (gitignored)
├── requirements.txt
└── .env.example
```

## Setup

Requires Python 3.10+.

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate      # Git Bash on Windows
# .\venv\Scripts\Activate.ps1     # PowerShell
# source venv/bin/activate        # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# then edit .env and add your Gemini API key
```

## Usage

**Streamlit UI** (easiest):

```bash
venv/Scripts/streamlit.exe run app.py
```

Opens at http://localhost:8501. Pick a drawing from `data/` or upload your own.

**Notebook** — step-by-step walkthrough of the pipeline:

```bash
jupyter notebook notebooks/01_drawing_review_demo.ipynb
```

**CLI**:

```bash
python -m src.main --drawing "data/easy/<filename>.pdf"
python -m src.main --drawing "data/easy/<filename>.pdf" --dry-run
```

`--dry-run` assembles and prints the request without calling the API — useful for
checking the pipeline works without spending tokens.

## Configuration

Settings live in `src/config.py`:

| Setting | Default | Notes |
|---|---|---|
| `GEMINI_MODEL` | `gemini-3.6-flash` | Pinned version — avoid `-latest` aliases so results don't change silently |
| `RENDER_DPI` | `300` | Very large sheets at high DPI may exceed the API request size limit |

## Transferring the project between machines

Do **not** zip or copy `venv/` — it contains absolute paths and breaks when moved.
Also exclude `.env` (contains your key) and `outputs/` (regenerates automatically).

On the target machine, recreate the environment with the setup steps above.

## Known limitations

- Single-drawing review only — no batch processing
- No conversation memory; each review is independent
- No downscaling for very large drawings, which may exceed API request size limits
- Reviews are LLM-generated and should be treated as a first-pass aid, not a
  substitute for engineering review