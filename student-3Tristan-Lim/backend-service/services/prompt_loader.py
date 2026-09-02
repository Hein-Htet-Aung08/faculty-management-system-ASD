import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent   # backend-service/
APP_DIR = BASE_DIR.parent                           # student-3Tristan-Lim/
PROMPT_DIR = Path(os.getenv("PROMPT_DIR", APP_DIR / "prompts"))

IMPLEMENTATION_DIR = PROMPT_DIR / "service" / "implementation"
REVIEW_DIR = PROMPT_DIR / "service" / "review"


def load_prompt(relative_path):
    """Load a prompt by path relative to prompts/, e.g. 'service/review/x.txt'."""
    return (PROMPT_DIR / relative_path).read_text(encoding="utf-8").strip()


def load_service_prompt(filename):
    """Load a prompt by bare filename, searching implementation then review."""
    for directory in (IMPLEMENTATION_DIR, REVIEW_DIR):
        candidate = directory / filename
        if candidate.exists():
            return candidate.read_text(encoding="utf-8").strip()

    raise FileNotFoundError(
        f"prompt '{filename}' not found under {IMPLEMENTATION_DIR} or {REVIEW_DIR}"
    )
