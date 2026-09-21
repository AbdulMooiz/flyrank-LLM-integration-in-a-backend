import json
import time
from pathlib import Path
from typing import Optional

LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def log_cost(prompt_version: str, model: str, usage, duration_ms: int, repaired: bool) -> None:
    """Stage 4: one line per call. This is the data behind the README's
    'what does 10,000 requests a day cost' line."""
    entry = {
        "ts": time.time(),
        "prompt_version": prompt_version,
        "model": model,
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "duration_ms": duration_ms,
        "repaired": repaired,
    }
    with open(LOGS_DIR / "cost.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")


def log_quarantine(input_text: str, raw_output: str, error: Optional[str], prompt_version: str) -> None:
    """Stage 3: bad output is set aside with the reason, never returned to
    the caller and never allowed to crash the request."""
    entry = {
        "ts": time.time(),
        "input": input_text,
        "raw_output": raw_output,
        "error": error,
        "prompt_version": prompt_version,
    }
    with open(LOGS_DIR / "quarantine.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
