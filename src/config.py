"""Central configuration: project paths, model settings and the API key.

Everything is resolved relative to this file, so the project works unchanged
after being zipped and moved to another machine. The API key is read lazily
(see get_api_key) so that importing this module -- and running --dry-run --
never fails when no key is configured.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = the folder that contains `src/` (this file lives in src/).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load variables from <project root>/.env into the environment (if the file exists).
load_dotenv(PROJECT_ROOT / ".env")

# --- Paths -----------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"        # input drawings (data/easy, data/complex)
OUTPUT_DIR = PROJECT_ROOT / "outputs"   # rendered PNGs and saved reviews

# --- Model settings --------------------------------------------------------
GEMINI_MODEL = "gemini-3.6-flash" # change this one line to use another model
RENDER_DPI = 300                   # resolution used when rendering the PDF to PNG

# Raw key from the environment; may be None or the placeholder from .env.example.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Value shipped in .env.example -- treated the same as "no key".
_PLACEHOLDER_KEY = "your_key_here"


def get_api_key() -> str:
    """Return the Gemini API key, or raise a helpful error if it is not set.

    Called only right before a real API call, never at import time, so that
    dry-run mode works without a key.
    """
    # Missing or still the placeholder -> tell the user exactly how to fix it.
    if not GEMINI_API_KEY or GEMINI_API_KEY == _PLACEHOLDER_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env in the project "
            f"root ({PROJECT_ROOT}) and put your real Gemini API key in it. "
            "Use --dry-run to test the pipeline without a key."
        )
    return GEMINI_API_KEY
