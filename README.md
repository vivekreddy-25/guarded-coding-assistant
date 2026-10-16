# Guarded Coding Assistant

A coding assistant built on NVIDIA NeMo Guardrails, wrapping free-tier LLM inference (Groq) with a layered safety pipeline: input filtering, output review, and a custom secrets-detection engine I wrote myself. This started as a way to learn programmable guardrails properly, not just call an LLM API and hope for the best.

**Live demo:** [add your Streamlit Cloud link here once deployed]

## What it does

It's a normal coding assistant on the surface — ask it a Python question, get a helpful answer. Underneath, every message passes through several checks before it reaches the model, and every response is checked again before it reaches you:

- **Input rail** — refuses requests for malware, exploits, or jailbreak attempts (prompt injection, "ignore your instructions," roleplay-based restriction bypasses), while still allowing legitimate security-education questions through
- **Output rail (LLM-based)** — reviews generated responses for anything that shouldn't be shown, using the same self-check pattern as the input side
- **Output rail (custom, rule-based)** — a Python action I wrote that scans every response for hardcoded secrets: known API key formats (OpenAI, Groq, AWS, GitHub), password/secret fields in both `variable = "value"` and `"key": "value"` styles, and a Shannon-entropy check that catches high-randomness strings even when they don't match a known pattern

## Why I built it this way

Most guardrails demos I found online just enable NeMo's built-in self-check and stop there. I wanted something closer to what an actual production system would need — which meant writing my own detection logic instead of relying purely on an LLM asking itself "is this safe?", and actually testing it against adversarial input rather than assuming it works.

## What I found while building it

This is the part I think matters most, so I'm documenting it honestly rather than presenting a clean success story:

- **Rate limits change your numbers.** My first benchmark run showed wildly inconsistent latency (some requests took 30+ seconds). Turned out Groq's free tier has a token-per-minute budget, and my guardrails pipeline makes up to three LLM calls per message. Capping response length and adding delays between test requests fixed it and got latency down to a consistent ~1.5-2.5 seconds.
- **My regex missed a real case.** My password-detection pattern only matched `password = "value"` style code. A live test asked for a database connection example, and the model wrote `"password": "secret_pass"` — dictionary style — which slipped straight through undetected. I found this by testing, not by reasoning about it in advance. Fixed the pattern, added a regression test for exactly this case so it can't silently break again.
- **Overly cautious wording has a cost too.** My first output-safety policy blocked a completely legitimate question ("how does SQL injection work as a vulnerability?") because the LLM judge read "vulnerability" and "injection" as red flags. Guardrails aren't just about blocking more — an over-strict policy makes the tool worse to use. I rewrote the policy to explicitly allow security education while still blocking real attack content.
- **Self-check rails should be deterministic, generation shouldn't be.** I ended up running two separate model configs: temperature 0 for the safety-check calls (so the same input always gets the same safety verdict) and temperature 0.4 for the actual coding answers (so they don't feel robotic).

## Results

Tested against a 50-prompt adversarial set (25 legitimate coding questions, 25 malicious/jailbreak attempts):

| Metric | Result |
|---|---|
| Accuracy | 50/50 (100%) |
| False negatives (malicious prompts that got through) | 0 |
| False positives (legit questions wrongly blocked) | 0 |
| Average latency | ~2.78s per request |

Full results and the test set are in `tests/adversarial_prompts.json` and `tests/results.json`.

## Stack

- **NVIDIA NeMo Guardrails** (Colang DSL) for the rails pipeline
- **Groq API** (free tier, `openai/gpt-oss-120b`) for inference
- **Python** for the custom secrets-detection action
- **Streamlit** for the demo interface

## Running it locally

```bash
git clone <your-repo-url>
cd guarded-coding-assistant
python -m venv venv
venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

Create a `.env` file with your own free Groq API key:
GROQ_API_KEY=your_key_here

Then run either the CLI version or the web UI:
```bash
python guarded_assistant.py
# or
streamlit run streamlit_app.py
```

## What I'd add next

- Static analysis (Bandit) on any generated code, not just secrets scanning
- A malicious-code detection rail specifically for exploit/malware requests framed as "educational"
- Comparing this Groq-based setup against a local Ollama version on speed and accuracy
- Streaming responses instead of waiting for the full guardrails pipeline to finish