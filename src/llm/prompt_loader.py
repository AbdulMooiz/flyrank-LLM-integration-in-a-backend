from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


@lru_cache(maxsize=8)
def load_prompt(name: str) -> str:
    """Stage 2: the prompt lives in a file with a version number, not a string
    inside a route handler, so it can be diffed and code reviewed like any
    other spec. name is the file stem, e.g. "triage-v1"."""
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")
