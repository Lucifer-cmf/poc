import streamlit as st
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from storage import accept_invite
from datetime import datetime

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["vector_db"]
users_collection = db["users"]


# ---------------- Login ----------------
def login_screen():
    st.subheader("Login")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        user = users_collection.find_one({
            "email": email,
            "password": password
        })

        if user:
            st.session_state.user_id = str(user["_id"])
            st.session_state.email = user["email"]
            st.session_state.account_type = "organization"
            st.success("Logged in")
            st.rerun()
        else:
            st.error("Invalid credentials")


# ---------------- Register (individual) ----------------
def register_screen():
    st.subheader("Register (Individual)")

    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")

    if st.button("Register"):
        existing = users_collection.find_one({"email": email})
        if existing:
            st.error("User already exists")
            return

        result = users_collection.insert_one({
            "email": email,
            "password": password,
            "created_at": datetime.now()
        })

        st.success("Account created. Please login.")


# ---------------- Invite Register ----------------
def invite_register_screen():
    st.subheader("Join Organization via Invite")

    token = st.text_input("Invite Token", key="invite_token")
    password = st.text_input("Set Password", type="password", key="invite_password")

    if st.button("Join Organization"):
        success, msg = accept_invite(token, password)

        if success:
            st.success(msg)
            st.info("You can now log in with your email and password.")
        else:
            st.error(msg)


# ---------------- Main auth screen ----------------
def auth_screen():
    st.title("Authentication")

    tab1, tab2, tab3 = st.tabs([
        "Login",
        "Register",
        "Invite Register"
    ])

    with tab1:
        login_screen()

    with tab2:
        register_screen()

    with tab3:
        invite_register_screen()
