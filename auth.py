import streamlit as st
from dotenv import load_dotenv
import os

from pymongo import MongoClient
from vector_embedding import store_embeddings
from generative import get_qa_chain
from storage import (
    save_message,
    load_chat_history,
    get_user_orgs,
    create_invite
)

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["vector_db"]
pdf_collection = db["pdf_docs"]

st.set_page_config(page_title="PDF Chatbot", page_icon="📄", layout="wide")

# ---------------- Session state ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

# ---------------- Authentication ----------------
if "user_id" not in st.session_state:
    auth_screen()
    st.stop()

user_id = st.session_state.user_id
email = st.session_state.email
account_type = st.session_state.get("account_type", "individual")

# Load chat history once
if "chat_loaded" not in st.session_state:
    st.session_state.chat_history = load_chat_history(user_id)
    st.session_state.chat_loaded = True

# ---------------- Sidebar ----------------
with st.sidebar:
    st.title(f"👤 {email}")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.divider()

    # -------- ORGANIZATION MODE --------
    if account_type == "organization":
        st.subheader("Workspace")

        orgs = get_user_orgs(user_id)
        org_names = [o["name"] for o in orgs]

        selected_org = st.selectbox("Select workspace", org_names)

        org_id = None
        for o in orgs:
            if o["name"] == selected_org:
                org_id = str(o["_id"])
                break

        # Invite members
        st.subheader("Invite Member")
        invite_email = st.text_input("Email")

        if st.button("Send Invite"):
            token = create_invite(invite_email, org_id)
            st.success(f"Invite token: {token}")

    else:
        org_id = None

    st.divider()

    # -------- Upload section --------
    st.subheader("Upload PDFs")
    files = st.file_uploader(
        "Upload PDFs",
        type="pdf",
        accept_multiple_files=True
    )

    if files and st.button("Process Documents"):
        with st.spinner("Processing PDFs..."):
            if account_type == "organization":
                store_embeddings(files, org_id=org_id)
                st.session_state.qa_chain = get_qa_chain(org_id=org_id)
            else:
                store_embeddings(files, user_id=user_id)
                st.session_state.qa_chain = get_qa_chain(user_id=user_id)

            st.session_state.chat_history = []

        st.success("Documents ready for chat!")

# ---------------- Main chat ----------------
st.title("📄 PDF Chat Assistant")

# Check if context exists
# Check if context exists
if account_type == "organization" and org_id:
    context_filter = {"org_id": str(org_id)}
else:
    context_filter = {"user_id": str(user_id)}

context_exists = pdf_collection.find_one(context_filter)

# Show chat history
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# If no context, block chat
if not context_exists:
    st.info("Upload PDFs in the sidebar to create your knowledge base.")
    st.stop()

# If context exists but chain not created yet
if not st.session_state.qa_chain:
    if account_type == "organization":
        st.session_state.qa_chain = get_qa_chain(org_id=org_id)
    else:
        st.session_state.qa_chain = get_qa_chain(user_id=user_id)

# ---------------- Chat input ----------------
user_input = st.chat_input("Ask a question...")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    save_message(user_id, "user", user_input)

    with st.chat_message("assistant"):
        result = st.session_state.qa_chain.invoke(
            {"input": user_input}
        )
        answer = result["answer"]
        st.markdown(answer)

    st.session_state.chat_history.append(("assistant", answer))
    save_message(user_id, "assistant", answer)

