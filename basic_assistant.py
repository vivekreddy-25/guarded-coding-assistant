# The "before" version — plain assistant, zero guardrails.
# Keeping this around so I can compare it against the guarded version later.

import os                          # need this to read environment variables
from dotenv import load_dotenv     # loads variables from a .env file into the environment
from groq import Groq              # Groq's official Python client

load_dotenv()  # reads .env and pulls GROQ_API_KEY into the environment so the line below can find it

# set up the client once, using the key we just loaded — this object is what
# actually talks to Groq's servers every time we ask it something
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def ask_assistant(question: str) -> str:
    # this function takes whatever the user typed and sends it straight to the model
    # no checks, no filtering — just a plain API call, on purpose (this is the baseline)
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",   # free-tier model on Groq, confirmed working during testing
        messages=[
            # system message = tells the model how to behave for the whole conversation
            {"role": "system", "content": "You are a helpful coding assistant. Answer coding questions clearly and provide code examples when useful."},
            # user message = the actual question that came from input()
            {"role": "user", "content": question}
        ],
        temperature=0.3,   # lower value = less random, more consistent answers — good for coding Q&A
    )
    # the actual reply text is buried a few levels deep in the response object, so pull it out here
    return response.choices[0].message.content


if __name__ == "__main__":
    # only runs when this file is executed directly (not when imported elsewhere)
    print("Coding Assistant (type 'exit' to quit)\n")   # just a header so it's obvious the loop started

    while True:                                # keep looping until the user decides to quit
        user_input = input("You: ")            # blocks here until the user types something and hits enter

        if user_input.lower() in ("exit", "quit"):   # simple exit condition, case-insensitive
            break                                      # kicks us out of the while loop

        answer = ask_assistant(user_input)     # send the question off, wait for the model's reply
        print(f"\nAssistant: {answer}\n")      # show the answer, with some spacing so it's readable