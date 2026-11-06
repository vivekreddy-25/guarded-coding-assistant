# Rule-based response check that complements NeMo's self-check.

import os
import re
import sys
import json
import math
import tempfile
import subprocess
from nemoguardrails.actions import action


# Common credential formats and field names.
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
    # High-entropy strings may be tokens that do not match a known format.
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in probs)


def detect_secrets(text: str):
    findings = []

    for pattern, label in SECRET_PATTERNS:
        if re.search(pattern, text):
            findings.append(label)

    # Check long token-like strings too, including ones without a known prefix.
    candidates = re.findall(r"[A-Za-z0-9+/=_\-]{20,}", text)
    for candidate in candidates:
        # A score above 4 bits per character is treated as unusually random.
        if shannon_entropy(candidate) > 4.0:
            findings.append(f"High-entropy string (possible unlabeled secret): {candidate[:10]}...")

    return findings


@action(is_system_action=True)
async def check_output_for_secrets(context: dict) -> bool:
    # NeMo blocks the response when this action returns True.
    bot_response = context.get("bot_message", "")
    findings = detect_secrets(bot_response)
    return len(findings) > 0


# Findings below this severity are too noisy to surface (e.g. asserts, plain
# "import subprocess"); medium/high is where eval() misuse, string-built SQL,
# and shell=True calls actually land.
BANDIT_MIN_SEVERITY = {"MEDIUM", "HIGH"}


def extract_python_blocks(text: str) -> list:
    return re.findall(r"```(?:python|py)\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)


def run_bandit(code: str) -> list:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-f", "json", "-q", path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if not result.stdout:
            return []
        data = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        # If Bandit itself fails to run, don't block the response on that.
        return []
    finally:
        os.remove(path)

    return [
        {
            "severity": issue["issue_severity"],
            "test_id": issue["test_id"],
            "text": issue["issue_text"],
            "line": issue["line_number"],
        }
        for issue in data.get("results", [])
        if issue["issue_severity"] in BANDIT_MIN_SEVERITY
    ]


@action(is_system_action=True)
async def check_output_code_security(context: dict) -> str:
    # Returns a warning block to append to the response, or "" if there's
    # nothing to flag. Unlike check_output_for_secrets, this never blocks the
    # response outright -- the generated code is still useful even when it
    # has issues, as long as the user is told to review it.
    bot_response = context.get("bot_message", "")
    findings = []
    for code_block in extract_python_blocks(bot_response):
        findings.extend(run_bandit(code_block))

    if not findings:
        return ""

    lines = ["\n\n---", "**Static analysis (Bandit) flagged the code above:**"]
    for finding in findings:
        lines.append(f"- [{finding['severity']}] {finding['test_id']}: {finding['text']} (line {finding['line']})")
    lines.append("\nReview these before using the code as-is.")
    return "\n".join(lines)