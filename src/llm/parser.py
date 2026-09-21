import json
import re
from typing import Optional, Tuple

from pydantic import ValidationError

from .schema import TriageOutput

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)
_BRACE_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json_text(raw: str) -> str:
    """Models like to wrap JSON in a code fence, or add a sentence before it.
    Pull out just the object."""
    fence_match = _FENCE_RE.search(raw)
    if fence_match:
        return fence_match.group(1)
    brace_match = _BRACE_RE.search(raw)
    if brace_match:
        return brace_match.group(0)
    return raw


def parse_and_validate(raw_text: str) -> Tuple[Optional[TriageOutput], Optional[str]]:
    """Stage 3. Returns (result, error). Exactly one of them is None.
    Never raises. A structurally valid object with a value outside the
    schema's closed lists is still a failure, and this is where it is caught."""
    candidate = _extract_json_text(raw_text)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as e:
        return None, f"Could not parse JSON: {e}"
    try:
        return TriageOutput.model_validate(data), None
    except ValidationError as e:
        return None, str(e)
