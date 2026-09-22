import json
from pathlib import Path

import requests

CASES_PATH = Path(__file__).parent / "cases.json"
ENDPOINT = "http://localhost:8000/triage"


def main() -> None:
    cases = json.loads(CASES_PATH.read_text())
    correct = 0
    failures = []

    for i, case in enumerate(cases):
        resp = requests.post(ENDPOINT, json={"text": case["input"]})
        if resp.status_code != 200:
            failures.append((i, case["input"], f"HTTP {resp.status_code}: {resp.text}"))
            continue
        data = resp.json()
        if data["category"] == case["expected_category"]:
            correct += 1
        else:
            failures.append(
                (i, case["input"], f"got category={data['category']!r}, expected {case['expected_category']!r}")
            )

    print(f"Score: {correct}/{len(cases)} on category match")
    if failures:
        print("\nMisses:")
        for i, text, reason in failures:
            print(f"  [{i}] {text!r}\n      {reason}")


if __name__ == "__main__":
    main()
