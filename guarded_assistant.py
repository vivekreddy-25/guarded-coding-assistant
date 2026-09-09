import os
from dotenv import load_dotenv
from nemoguardrails import LLMRails, RailsConfig

load_dotenv()

# NeMo Guardrails' OpenAI-compatible client reads from OPENAI_API_KEY,
# so we map our Groq key onto that variable name
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