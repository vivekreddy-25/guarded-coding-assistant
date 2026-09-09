# Custom guardrail action — checks the model's response for hardcoded
# secrets before it ever reaches the user. This runs alongside NeMo's
# built-in LLM-based self-check, as a second, rule-based layer that
# doesn't depend on an LLM's judgment.

import re
import math
from nemoguardrails.actions import action


# known prefixes/formats for real API keys and credentials.
# started with just OpenAI/Groq-style keys, added more as I thought of them
SECRET_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI-style API key"),
    (r"gsk_[a-zA-Z0-9]{20,}", "Groq API key"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key ID"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub personal access token"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private key block"),
    # this pattern covers both variable = "..." and "key": "..." styles —
    # originally only matched the = style, missed a real dict-style leak
    # during testing, so it's written to catch both now
    (r"(?i)[\"']?password[\"']?\s*[:=]\s*[\"'][^\"']{4,}[\"']", "Hardcoded password"),
    (r"(?i)[\"']?api_?key[\"']?\s*[:=]\s*[\"'][^\"']{8,}[\"']", "Hardcoded API key field"),
    (r"(?i)[\"']?secret[\"']?\s*[:=]\s*[\"'][^\"']{4,}[\"']", "Hardcoded secret field"),
]


def shannon_entropy(s: str) -> float:
    # entropy is basically a measure of "how random does this string look".
    # real keys/tokens tend to be high entropy since they're randomly generated,
    # whereas normal words and code have much lower entropy. this catches secrets
    # that don't match any of the known patterns above.
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in probs)


def detect_secrets(text: str):
    findings = []

    for pattern, label in SECRET_PATTERNS:
        if re.search(pattern, text):
            findings.append(label)

    # look for any long random-looking chunk of text and check its entropy —
    # threshold of 4.0 was picked by testing, seemed to catch real secrets
    # without flagging normal code too often
    candidates = re.findall(r"[A-Za-z0-9+/=_\-]{20,}", text)
    for candidate in candidates:
        if shannon_entropy(candidate) > 4.0:
            findings.append(f"High-entropy string (possible unlabeled secret): {candidate[:10]}...")

    return findings


@action(is_system_action=True)
async def check_output_for_secrets(context: dict) -> bool:
    # this is the function NeMo actually calls from the Colang flow.
    # returning True means "block this response"
    bot_response = context.get("bot_message", "")
    findings = detect_secrets(bot_response)
    return len(findings) > 0