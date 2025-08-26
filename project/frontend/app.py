import json
import os
from datetime import datetime

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

st.set_page_config(
    page_title="Azercell Chatbot",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .message-time {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .stButton > button {
        width: 100%;
        margin-top: 1rem;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Sidebar
with st.sidebar:
    st.title("🔮 Azercell Chatbot")
    st.markdown("---")

    # Backend status
    st.subheader("Backend Status")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            st.success("Backend Connected!")
        else:
            st.error("Backend Error")
    except Exception:
        st.error("Backend Unreachable")

    st.markdown("---")

    st.subheader("Knowledge Base Search")
    search_query = st.text_input("Search for specific information:")
    if st.button("Search"):
        if search_query:
            with st.spinner("Searching knowledge base..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/search",
                        json={"query": search_query}
                    )
                    if response.status_code == 200:
                        results = response.json()
                        st.success("Search completed!")
                        st.text_area("Results:", results.get("results", ""), height=200)
                    else:
                        st.error(f"Search failed: {response.text}")
                except Exception as e:
                    st.error(f"Search error: {str(e)}")

    st.markdown("---")

    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()

    if st.session_state.messages:
        conversation_text = "\n\n".join([
            f"{msg['role'].title()}: {msg['content']}"
            for msg in st.session_state.messages
        ])
        st.download_button(
            label="Export Conversation",
            data=conversation_text,
            file_name=f"azercell_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

st.title("🔮 Azercell Telecom Chatbot")
st.markdown("Ask me anything about Azercell policies, procedures, or general information!")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        st.caption(f"Time: {message['timestamp']}")

if prompt := st.chat_input("Type your message here..."):
    user_message = {
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"Time: {user_message['timestamp']}")

    conversation_history = []
    for msg in st.session_state.messages[:-1]:
        conversation_history.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        try:
            response = requests.post(
                f"{BACKEND_URL}/chat/stream",
                json={
                    "message": prompt,
                    "conversation_history": conversation_history
                },
                stream=True
            )

            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8').replace('data: ', ''))
                            if 'text' in data:
                                full_response += data['text']
                                message_placeholder.markdown(full_response + "▌")
                            elif 'error' in data:
                                st.error(f"Streaming error: {data['error']}")
                                break
                        except json.JSONDecodeError:
                            continue

                message_placeholder.markdown(full_response)

                assistant_message = {
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                st.session_state.messages.append(assistant_message)

            else:
                response = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={
                        "message": prompt,
                        "conversation_history": conversation_history
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    full_response = data.get("response", "No response received")
                    message_placeholder.markdown(full_response)

                    assistant_message = {
                        "role": "assistant",
                        "content": full_response,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }
                    st.session_state.messages.append(assistant_message)

                    sources = data.get("sources", [])
                    if sources:
                        with st.expander("📚 Sources"):
                            for source in sources:
                                st.markdown(f"**{source.get('type', 'Unknown')}:**")
                                st.text(source.get('content', ''))
                else:
                    st.error(f"Error: {response.text}")

        except Exception as e:
            st.error(f"Error communicating with backend: {str(e)}")
            message_placeholder.markdown("Sorry, I encountered an error. Please try again.")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Powered by AWS Bedrock & Claude AI | Azercell Telecom Chatbot</p>
        <p>Built with FastAPI & Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)
