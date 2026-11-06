# Standalone tests for the Bandit code-security check; no API calls needed.

import asyncio
import importlib.util

spec = importlib.util.spec_from_file_location("actions_module", "./config/actions.py")
actions_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(actions_module)

check_output_code_security = actions_module.check_output_code_security

test_cases = [
    (
        "Here's a query:\n```python\n"
        "query = \"SELECT * FROM users WHERE name = '\" + name + \"'\"\n"
        "cursor.execute(query)\n"
        "```",
        True,
    ),
    (
        "You can run it like this:\n```python\n"
        "import subprocess\n"
        "subprocess.run(user_input, shell=True)\n"
        "```",
        True,
    ),
    (
        "```python\n"
        "result = eval(user_expression)\n"
        "```",
        True,
    ),
    (
        "Here's a clean example:\n```python\n"
        "def add(a, b):\n"
        "    return a + b\n"
        "```",
        False,
    ),
    (
        "Just explaining binary search, no code blocks here at all.",
        False,
    ),
]

for i, (text, expect_flag) in enumerate(test_cases, 1):
    warning = asyncio.run(check_output_code_security({"bot_message": text}))
    flagged = bool(warning)
    status = "PASS" if flagged == expect_flag else "FAIL"
    print(f"Test {i}: {status} (flagged={flagged}, expected={expect_flag})")
    if warning:
        print(f"  {warning.strip().splitlines()[1]}")
