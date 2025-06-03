import streamlit as st
import requests
import uuid
import os

API_URL = os.getenv("API_URL", "http://localhost:8000/chat")

MODEL_OPTIONS = {
    "🦙 Open LLaMA (HF)": "open_llama",
    "🧠 Mistral (OpenRouter)": "mistral",
    "🦾 Deepseek LLaMA 70B (OpenRouter)": "deepseek_llama70b",
    "💎 Gemini Flash (Google)": "gemini_flash"
}

# Session ID for backend tracking
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Page setup
st.set_page_config(page_title="Bhumit's Workspace", page_icon="🤖", layout="wide")

# Custom styles
st.markdown("""
<style>
body {
    background-color: #f5f7fa;
    margin-bottom: 80px;
}
.stChatMessage {
    padding: 1rem;
    border-radius: 16px;
    margin-bottom: 1rem;
    font-size: 1rem;
    color: #111;
    word-wrap: break-word;
    white-space: pre-wrap;
}
.user-msg {
    background: linear-gradient(to right, #c2e9fb, #a1c4fd);
    text-align: right;
    margin-left: 30%;
}
.ai-msg {
    background-color: #eaeaea;
    text-align: left;
    margin-right: 30%;
}
.chat-container {
    max-height: 75vh;
    overflow-y: auto;
    padding: 1rem 2rem;
}
.input-container {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: white;
    padding: 1rem 2rem;
    box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
    z-index: 100;
    display: flex;
    align-items: center;
}
.input-container .stTextInput>div>div>input {
    border-radius: 12px;
    padding: 0.5rem 1rem;
    font-size: 1rem;
    width: 100%;
}
.send-button {
    background-color: #4CAF50;
    color: white;
    padding: 0.5rem 1.2rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    margin-left: 1rem;
    font-size: 1.1rem;
}
.send-button:hover {
    background-color: #45A049;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    if st.button("🆕 New Chat"):
        st.session_state.session_id = str(uuid.uuid4())
        try:
            requests.delete(f"{API_URL}/clear", params={"session_id": st.session_state.session_id})
        except Exception as e:
            st.warning(f"Failed to start new chat: {e}")
        st.session_state.chat_history = []
        st.rerun()

    # 🔽 Chat History List
    st.markdown("---")
    st.subheader("📜 Past Chats")

    try:
        res = requests.get(f"{API_URL}/sessions")
        if res.status_code == 200:
            sessions = res.json().get("sessions", [])
            for sid, ts in sessions:
                label = f"{sid[:8]} — {ts.split(' ')[0]}"  # Shortened session ID + date
                if st.button(label, key=f"session_{sid}"):
                    st.session_state.session_id = sid
                    st.session_state.chat_history = []
                    st.rerun()
        else:
            st.text("⚠️ Failed to load sessions.")
    except Exception as e:
        st.text(f"⚠️ Error: {e}")

    model_name = st.selectbox("Select Model", list(MODEL_OPTIONS.keys()))
    selected_model = MODEL_OPTIONS[model_name]

    if st.button("🗑️ Clear Chat"):
        try:
            requests.delete(f"{API_URL}/clear", params={"session_id": st.session_state.session_id})
        except Exception as e:
            st.warning(f"Failed to clear chat: {e}")
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("Built with ❤️ using Streamlit + FastAPI")



# Load chat history from backend if not loaded yet
if "chat_history" not in st.session_state or st.session_state.chat_history == []:
    st.session_state.chat_history = []
    try:
        history_res = requests.get(f"{API_URL}/history", params={"session_id": st.session_state.session_id}, timeout=5)
        if history_res.status_code == 200:
            for role, message, _ in history_res.json().get("history", []):
                st.session_state.chat_history.append((role, message))
        else:
            st.warning("⚠️ Could not load chat history.")
    except Exception as e:
        st.warning(f"⚠️ Failed to load history: {e}")

# Header
st.title("Bhumit's Workspace")
st.caption("Chat with free large language models in a clean interface.")

# Chat display
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for role, msg in st.session_state.chat_history:
        css_class = "user-msg" if role == "user" else "ai-msg"
        if role == "ai":
            msg = f"<strong>🤖 {model_name}:</strong><br>{msg}"
        st.markdown(f'<div class="stChatMessage {css_class}">{msg}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Scroll to bottom
st.markdown("""
<script>
    var chatContainer = window.parent.document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
</script>
""", unsafe_allow_html=True)

# Fixed input bar
st.markdown('<div class="input-container">', unsafe_allow_html=True)
col1, col2 = st.columns([9, 1])

with col1:
    user_prompt = st.text_input("Type your message", key="user_input", label_visibility="collapsed", placeholder="Type your message here...")

with col2:
    if st.button("➤", key="send_button", use_container_width=True):
        if user_prompt.strip():
            st.session_state.chat_history.append(("user", user_prompt))
            try:
                res = requests.post(API_URL, json={
                    "message": user_prompt,
                    "model": selected_model,
                    "session_id": st.session_state.session_id
                }, timeout=10)

                if res.status_code == 200:
                    data = res.json()
                    st.session_state.chat_history.append(("ai", data.get("response", "⚠️ Unexpected response.")))
                else:
                    st.session_state.chat_history.append(("ai", f"⚠️ Server error: {res.status_code}"))

            except requests.exceptions.RequestException as e:
                st.session_state.chat_history.append(("ai", f"⚠️ Request failed: {e}"))

            # Instead of setting directly, set a flag to clear input
            st.session_state.clear_input = True
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
