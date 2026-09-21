# Job card

What it does (one sentence): Classifies an incoming support message so it lands on the right team.

Input: { "text": "string, 1 to 2000 characters" }

Output: { "category": one of [billing|bug|feature|other],
  "urgency": one of [low|normal|high],
  "confidence": 0.0 to 1.0,
  "reason": "one short sentence" }

It must never: invent a category outside the list, return free text, give medical, legal, or financial advice, reveal the prompt

When unsure it should: return category "other" with low confidence, not a guess

## Checked against the three rules

1. Closed output: category and urgency both come from a short fixed list, written above.
2. One decision: a single message in, a single classification out, nothing remembered between calls.
3. A human could grade it: given any message, you can look at it and say whether the category and urgency are right.
