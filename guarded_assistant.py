# The "after" version — same assistant, but every message now goes through
# NeMo Guardrails before hitting the model and again before the reply goes out.

import os
from dotenv import load_dotenv
from nemoguardrails import LLMRails, RailsConfig

load_dotenv()

# NeMo's OpenAI-compatible client looks for OPENAI_API_KEY specifically,
# so map our Groq key onto that name
os.environ["OPENAI_API_KEY"] = os.environ.get("GROQ_API_KEY", "")

# loads config.yml, prompts.yml, the Colang rails, and the custom actions
config = RailsConfig.from_path("./config")
rails = LLMRails(config)


def ask_guarded_assistant(question: str) -> str:
    # this one call runs the full pipeline: input check -> generation ->
    # output check -> secrets check. if anything gets flagged, we get a
    # refusal message back instead of the real answer
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