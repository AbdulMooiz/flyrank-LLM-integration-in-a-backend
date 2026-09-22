# Support message triage endpoint

This adds one endpoint, POST /triage, to my FlyRank backend API. It reads an
incoming support message and returns a category, an urgency level, a
confidence score, and a one sentence reason, so messages can be routed to the
right team automatically instead of a person reading each one first.

## Try it

    curl -X POST http://localhost:8000/triage \
      -H "Content-Type: application/json" \
      -d '{"text": "I was charged twice for my subscription this month"}'

Example response:

    {
      "category": "billing",
      "urgency": "high",
      "confidence": 0.9,
      "reason": "A duplicate charge is a billing error that needs a prompt correction."
    }

## The job card

The full contract is in JOB-CARD.md. In short: the category is always one of
billing, bug, feature, or other, urgency is always low, normal, or high, one
message goes in and one classification comes out with nothing remembered
between requests, and it must never invent a category, return free text, or
give medical, legal, or financial advice. When the model is unsure, it
returns "other" with a low confidence score rather than guessing.

## Provider

I used OpenRouter with the openrouter/free model router. Swapping providers
only means changing three environment variables: LLM_BASE_URL, LLM_API_KEY,
and LLM_MODEL, nothing else in the code has to change.

## Eval result

Score: 8/8 on category match
Date: 2026-09-22
Prompt version: triage-v1

Run `python evals/run_eval.py` with the server up and LLM_STUB unset to
reproduce this. The eight cases are in evals/cases.json.

## What one call costs

One real line from logs/cost.jsonl:

    {"ts": 1790033996.061271, "prompt_version": "triage-v1", "model": "openrouter/free", "input_tokens": 410, "output_tokens": 43, "duration_ms": 9203, "repaired": false}

Not every call is this cheap though. Across my log, output_tokens ranges from
about 40 up to over 1,200 for what should just be a short JSON object, and
duration climbed as high as 20 seconds on one call, close to my 30 second
timeout. That variance, not the token count on a clean call, is the real
driver of cost at scale.

At current usage this stays well inside OpenRouter's free tier, 20 requests
a minute and 50 a day, so there is no real dollar cost yet. TODO: one line
estimating cost at 10,000 requests a day once you have picked a paid model
and its per token price.

## How it behaves when things go wrong

- A missing or oversized `text` field never reaches the model, it's rejected
  with a 400 that names the exact field before any call is made.
- If the model's answer doesn't match the schema, it gets exactly one
  chance to correct itself with its own error message handed back to it. If
  that also fails, the request returns a 422 and the raw answer is logged to
  logs/quarantine.jsonl instead of being passed on to the caller.
- The client has an explicit 30 second timeout, since the SDK's own default
  is 10 minutes, which isn't a real timeout for an HTTP endpoint.
- Retries only happen on timeouts, 429s, and 5xxs, never on 400, 401, or
  403, since those mean the request itself is wrong and retrying won't fix
  that.
- LLM_ENABLED=false turns the whole feature off and returns a safe fallback
  immediately, without needing a deploy.

## What I'd fix with another day

The classification itself is solid, 8/8 on my eval, but the cost log shows
real inconsistency underneath that clean score: output_tokens swings from
about 40 to over 1,200 for the same fixed JSON shape, and duration once got
as close as 10 seconds from my timeout. With another day I'd tighten the
prompt further, or try the response_format parameter mentioned in the
assignment resources, to stop the model from occasionally reasoning out loud
before it gets to the JSON.