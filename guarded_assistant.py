# Assistant with input and output checks provided by NeMo Guardrails.

import os
import sys
from dotenv import load_dotenv
from nemoguardrails import LLMRails, RailsConfig

load_dotenv()

# The model sometimes answers with smart quotes, em dashes, or other
# characters outside Windows' default console codepage (cp1252), which
# crashes a plain print() with UnicodeEncodeError. Force UTF-8 output.
sys.stdout.reconfigure(encoding="utf-8")

# NeMo's OpenAI-compatible client uses OPENAI_API_KEY.
os.environ["OPENAI_API_KEY"] = os.environ.get("GROQ_API_KEY", "")

config = RailsConfig.from_path("./config")
rails = LLMRails(config)


def ask_guarded_assistant(question: str) -> str:
    response = rails.generate(messages=[
        {"role": "user", "content": question}
    ])
    return response["content"]


if __name__ == "__main__":
    print("Guarded Coding Assistant (type 'exit' to quit)\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        answer = ask_guarded_assistant(user_input)
        print(f"\nAssistant: {answer}\n")