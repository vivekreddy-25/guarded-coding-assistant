# Unguarded baseline for comparison with guarded_assistant.py.

import os
import sys
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# The model sometimes answers with smart quotes, em dashes, or other
# characters outside Windows' default console codepage (cp1252), which
# crashes a plain print() with UnicodeEncodeError. Force UTF-8 output.
sys.stdout.reconfigure(encoding="utf-8")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def ask_assistant(question: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a helpful coding assistant. Answer coding questions clearly and provide code examples when useful."},
            {"role": "user", "content": question}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print("Coding Assistant (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ("exit", "quit"):
            break

        answer = ask_assistant(user_input)
        print(f"\nAssistant: {answer}\n")