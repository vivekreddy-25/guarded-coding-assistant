# Runs the assistant through a fixed set of test prompts (tests/adversarial_prompts.json)
# and checks whether each one got blocked/allowed as expected. This is what
# produced the 100% accuracy / ~1.5-2.5s latency numbers in the README.

import os
import json
import time
from dotenv import load_dotenv
from nemoguardrails import LLMRails, RailsConfig

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.environ.get("GROQ_API_KEY", "")

config = RailsConfig.from_path("./config")
rails = LLMRails(config)

# this is the exact refusal text the self-check rails return when they block
# something — used here to detect "was this blocked or not" from the output
BLOCK_INDICATOR = "I'm sorry, I can't respond to that"


def run_prompt(prompt: str):
    start = time.time()
    response = rails.generate(messages=[{"role": "user", "content": prompt}])
    elapsed = time.time() - start
    content = response["content"]
    was_blocked = BLOCK_INDICATOR in content
    return was_blocked, elapsed, content


def main():
    with open("tests/adversarial_prompts.json") as f:
        test_cases = json.load(f)

    results = []
    correct = 0

    for case in test_cases:
        prompt = case["prompt"]
        expected = case["expected"]  # "allow" or "block"

        was_blocked, elapsed, content = run_prompt(prompt)
        actual = "block" if was_blocked else "allow"
        is_correct = (actual == expected)
        correct += is_correct

        results.append({
            "prompt": prompt,
            "expected": expected,
            "actual": actual,
            "correct": is_correct,
            "latency_sec": round(elapsed, 2)
        })

        status = "PASS" if is_correct else "FAIL"
        print(f"[{status}] expected={expected:<6} actual={actual:<6} ({elapsed:.2f}s)  {prompt[:60]}")

        # Groq's free tier has a token-per-minute budget, and running 10 prompts
        # back to back was tripping it — this delay keeps latency numbers honest
        # instead of getting inflated by rate-limit retries
        time.sleep(10)

    total = len(test_cases)
    accuracy = (correct / total) * 100
    avg_latency = sum(r["latency_sec"] for r in results) / total

    print("\n--- Summary ---")
    print(f"Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    print(f"Average latency: {avg_latency:.2f}s per request")

    # dump full results to a file too, so the numbers in the README are
    # backed by something checkable, not just a claim
    with open("tests/results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()