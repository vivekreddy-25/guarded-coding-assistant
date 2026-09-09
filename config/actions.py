import re
import math
from nemoguardrails.actions import action


SECRET_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI-style API key"),
    (r"gsk_[a-zA-Z0-9]{20,}", "Groq API key"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key ID"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub personal access token"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private key block"),
    (r"(?i)[\"']?password[\"']?\s*[:=]\s*[\"'][^\"']{4,}[\"']", "Hardcoded password"),
    (r"(?i)[\"']?api_?key[\"']?\s*[:=]\s*[\"'][^\"']{8,}[\"']", "Hardcoded API key field"),
    (r"(?i)[\"']?secret[\"']?\s*[:=]\s*[\"'][^\"']{4,}[\"']", "Hardcoded secret field"),
]


def shannon_entropy(s: str) -> float:
    """Measures randomness of a string. High entropy strings are often secrets/keys."""
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in probs)


def detect_secrets(text: str):
    findings = []

    for pattern, label in SECRET_PATTERNS:
        if re.search(pattern, text):
            findings.append(label)

    candidates = re.findall(r"[A-Za-z0-9+/=_\-]{20,}", text)
    for candidate in candidates:
        if shannon_entropy(candidate) > 4.0:
            findings.append(f"High-entropy string (possible unlabeled secret): {candidate[:10]}...")

    return findings


@action(is_system_action=True)
async def check_output_for_secrets(context: dict) -> bool:
    """Returns True if the bot's response should be BLOCKED due to detected secrets."""
    bot_response = context.get("bot_message", "")
    findings = detect_secrets(bot_response)
    return len(findings) > 0