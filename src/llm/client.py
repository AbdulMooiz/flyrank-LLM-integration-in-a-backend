import logging
import os
import random
import time

from openai import APIStatusError, APITimeoutError, OpenAI

logger = logging.getLogger("llm.client")

# Stage 4: retry only on the failures that mean "try again", never on the ones
# that mean "this request is wrong and will stay wrong": 400, 401, 403.
RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _get_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=30.0,  # the SDK default is 10 minutes, which is not a real timeout
        max_retries=0,  # we do our own retries below, on purpose, so the policy is visible
    )


def call_model(messages: list[dict], max_attempts: int = 3):
    """Returns (response, duration_ms). Raises the last error if every
    attempt fails or the failure is not retriable."""
    client = _get_client()
    model = os.environ["LLM_MODEL"]
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        start = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,  # near zero: this is classification, not creative writing
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            return response, duration_ms
        except APITimeoutError as e:
            last_error = e
            retriable = True
        except APIStatusError as e:
            last_error = e
            retriable = e.status_code in RETRIABLE_STATUS_CODES
            if not retriable:
                raise

        if attempt < max_attempts - 1:
            wait = (2**attempt) + random.uniform(0, 0.5)  # backoff plus jitter
            logger.warning("call_model attempt %d failed, retrying in %.1fs", attempt + 1, wait)
            time.sleep(wait)

    raise last_error
