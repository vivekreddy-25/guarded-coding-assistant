import os
import streamlit as st
from nemoguardrails import LLMRails, RailsConfig

# Load the Groq key from Streamlit's secrets manager (set up in step 4 below)
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["GROQ_API_KEY"]

st.set_page_config(page_title="Guarded Coding Assistant", page_icon="🛡️")
st.title(" Guarded Coding Assistant")
st.caption("A coding assistant protected by NVIDIA NeMo Guardrails — input/output safety checks, jailbreak resistance, and custom secrets detection.")

@st.cache_resource
def load_rails():
    config = RailsConfig.from_path("./config")
    return LLMRails(config)

rails = load_rails()

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
            response = rails.generate(messages=[{"role": "user", "content": prompt}])
            answer = response["content"]
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})