import streamlit as st
from dotenv import load_dotenv
import os

from vector_embedding import store_embeddings
from generative import get_qa_chain
from auth import auth_screen
from storage import save_message, load_chat_history

load_dotenv()

st.set_page_config(page_title="PDF Chatbot", page_icon="📄", layout="wide")

# ----------------- Session State -----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

if "docs_loaded" not in st.session_state:
    st.session_state.docs_loaded = False

# ----------------- Authentication -----------------
if "user" not in st.session_state:
    auth_screen()
    st.stop()

# Load previous chats once
if "chat_loaded" not in st.session_state:
    st.session_state.chat_history = load_chat_history(st.session_state.user)
    st.session_state.chat_loaded = True


# ----------------- Sidebar -----------------
with st.sidebar:
    
    st.title("📂 Document Upload")

    files = st.file_uploader(
        "Upload PDFs",
        type="pdf",
        accept_multiple_files=True
    )

    if files and st.button("Process Documents"):
        with st.spinner("Processing PDFs..."):
            store_embeddings(files)
            st.session_state.qa_chain = get_qa_chain()
            st.session_state.chat_history = []
            st.session_state.docs_loaded = True
        st.success("Documents ready for chat!")

    st.divider()
    st.title(f"👤 {st.session_state.user}")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()


# ----------------- Main Chat Area -----------------
st.title("📄 PDF Chat Assistant")

if not st.session_state.docs_loaded:
    st.info("Upload PDFs from the sidebar to begin.")

# Display chat history
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# Chat input
if st.session_state.qa_chain:
    user_input = st.chat_input("Ask a question about your documents...")

    if user_input:
        # Save user message
        st.session_state.chat_history.append(("user", user_input))
        save_message(st.session_state.user, "user", user_input)

        with st.chat_message("user"):
            st.markdown(user_input)

        # Assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = st.session_state.qa_chain.invoke(
                    {"input": user_input}
                )
                answer = result["answer"]
                st.markdown(answer)

        # Save assistant message
        st.session_state.chat_history.append(("assistant", answer))
        save_message(st.session_state.user, "assistant", answer)