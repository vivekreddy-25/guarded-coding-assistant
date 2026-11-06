# Web chat UI for the guarded assistant, built with Streamlit.
# Same guardrails pipeline as guarded_assistant.py, just wrapped in a
# browser-based chat interface instead of a terminal loop.
#
# This is meant to be deployed publicly (Streamlit Community Cloud) so people
# can try it without cloning the repo. Every visitor shares the owner's Groq
# API key and quota, so there's a per-session message cap below to keep one
# visitor from exhausting it for everyone else.

import os
import streamlit as st
from nemoguardrails import LLMRails, RailsConfig

MAX_MESSAGES_PER_SESSION = 15

# on Streamlit Cloud the key lives in their secrets manager, not a .env file —
# st.secrets reads from that (or from .streamlit/secrets.toml locally)
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["GROQ_API_KEY"]

st.set_page_config(page_title="Guarded Coding Assistant", page_icon="🛡️")
st.title("Guarded Coding Assistant")
st.caption("A coding assistant protected by NVIDIA NeMo Guardrails — input/output safety checks, jailbreak resistance, custom secrets detection, and a Bandit code-security check.")
st.caption(f"This is a shared public demo running on the owner's API key, so each browser session is capped at {MAX_MESSAGES_PER_SESSION} messages.")


@st.cache_resource
def load_rails():
    # cached so the config only loads once per session instead of on
    # every single message — loading it fresh each time would be slow
    config = RailsConfig.from_path("./config")
    return LLMRails(config)


rails = load_rails()

# keeps the chat history visible across reruns (Streamlit reruns the
# whole script on every interaction, so without this the chat would
# reset after every message)
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if len(st.session_state.messages) >= MAX_MESSAGES_PER_SESSION * 2:
    st.info("You've hit this demo's per-session message limit. Refresh the page to start a new session, or run the project locally for unlimited use.")
elif prompt := st.chat_input("Ask a coding question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Checking and generating..."):
            # same pipeline as the CLI version: input check -> generation ->
            # output check -> secrets check -> code security check, all
            # inside this one call
            response = rails.generate(messages=[{"role": "user", "content": prompt}])
            answer = response["content"]
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
