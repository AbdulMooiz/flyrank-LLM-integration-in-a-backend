import os

from fastapi import APIRouter, HTTPException

from src.llm.client import call_model
from src.llm.logging_utils import log_cost, log_quarantine
from src.llm.parser import parse_and_validate
from src.llm.prompt_loader import load_prompt
from src.llm.schema import Category, TriageInput, TriageOutput, Urgency

router = APIRouter()

PROMPT_VERSION = "triage-v1"

STUB_RESPONSE = TriageOutput(
    category=Category.other,
    urgency=Urgency.low,
    confidence=0.42,
    reason="Stub mode response, no model was called.",
)


@router.post("/triage", response_model=TriageOutput)
def triage(payload: TriageInput) -> TriageOutput:
    # Stage 1: payload is already validated by the time this line runs.
    # A missing or oversized text field never reaches this function; FastAPI
    # and the exception handler in main.py turn it into a 400 first.

    # Stage 4: kill switch. Flip this in an outage without a deploy.
    if os.environ.get("LLM_ENABLED", "true").lower() == "false":
        return STUB_RESPONSE

    # Stage 1: stub mode. Every restart while building costs zero quota.
    if os.environ.get("LLM_STUB") == "1":
        return STUB_RESPONSE

    system_prompt = load_prompt(PROMPT_VERSION)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": payload.text},
    ]

    try:
        response, duration_ms = call_model(messages)
    except Exception:
        # Stage 4: timed out, or every retry was exhausted. Never crash.
        raise HTTPException(status_code=504, detail="The model did not respond in time.")

    raw_text = response.choices[0].message.content
    result, error = parse_and_validate(raw_text)
    repaired = False

    if result is None:
        # Stage 3: exactly one repair retry, handing the model its own error.
        repaired = True
        repair_messages = messages + [
            {"role": "assistant", "content": raw_text},
            {
                "role": "user",
                "content": (
                    f"Your previous answer was rejected for this reason: {error}. "
                    "Return only corrected JSON matching the schema."
                ),
            },
        ]
        try:
            response, extra_ms = call_model(repair_messages)
            duration_ms += extra_ms
        except Exception:
            raise HTTPException(status_code=504, detail="The model did not respond in time.")
        raw_text = response.choices[0].message.content
        result, error = parse_and_validate(raw_text)

    log_cost(PROMPT_VERSION, os.environ.get("LLM_MODEL", "unknown"), response.usage, duration_ms, repaired)

    if result is None:
        # Stage 3: give up cleanly. Quarantine the raw output, never return it.
        log_quarantine(payload.text, raw_text, error, PROMPT_VERSION)
        raise HTTPException(status_code=422, detail="The model's answer could not be validated.")

    return result
