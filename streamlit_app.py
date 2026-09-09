# Web chat UI for the guarded assistant, built with Streamlit.
# Same guardrails pipeline as guarded_assistant.py, just wrapped in a
# browser-based chat interface instead of a terminal loop.

import os
import streamlit as st
from nemoguardrails import LLMRails, RailsConfig

# on Streamlit Cloud the key lives in their secrets manager, not a .env file —
# st.secrets reads from that (or from .streamlit/secrets.toml locally)
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["GROQ_API_KEY"]

st.set_page_config(page_title="Guarded Coding Assistant", page_icon="🛡️")
st.title(" Guarded Coding Assistant")
st.caption("A coding assistant protected by NVIDIA NeMo Guardrails — input/output safety checks, jailbreak resistance, and custom secrets detection.")


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

if prompt := st.chat_input("Ask a coding question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Checking and generating..."):
            # same pipeline as the CLI version: input check -> generation ->
            # output check -> secrets check, all inside this one call
            response = rails.generate(messages=[{"role": "user", "content": prompt}])
            answer = response["content"]
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})