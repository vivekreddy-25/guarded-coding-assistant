import importlib.util

spec = importlib.util.spec_from_file_location("secrets_module", "./config/actions.py")
secrets_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(secrets_module)

detect_secrets = secrets_module.detect_secrets

test_cases = [
    "Here's some code: api_key = 'sk-proj-abcdefghijklmnopqrstuvwxyz123456'",
    "Your AWS key is AKIAIOSFODNN7EXAMPLE",
    "password = 'hunter2'",
    "Just explaining how binary search works, no secrets here at all",
    "def add(a, b):\n    return a + b",
    '"password": "secret_pass",  # dict-style, the bug we found live',
]

for i, text in enumerate(test_cases, 1):
    findings = detect_secrets(text)
    print(f"Test {i}: {'DETECTED' if findings else 'clean'} -> {findings}")
    print(f"  Input: {text[:60]}\n")