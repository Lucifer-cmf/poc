import os
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
import hashlib

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["vector_db"]
users_collection = db["users"]


# -------- Password Hash --------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# -------- Register --------
def register_user(username, password):
    if users_collection.find_one({"username": username}):
        return False, "User already exists"

    users_collection.insert_one({
        "username": username,
        "password": hash_password(password)
    })
    return True, "User registered successfully"


# -------- Login --------
def login_user(username, password):
    user = users_collection.find_one({"username": username})
    if not user:
        return False, "User not found"

    if user["password"] != hash_password(password):
        return False, "Incorrect password"

    return True, "Login successful"


# -------- Auth UI --------
def auth_screen():
    st.title("🔐 Login / Register")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # Login tab
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            success, msg = login_user(username, password)
            if success:
                st.session_state.user = username
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    # Register tab
    with tab2:
        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")

        if st.button("Register"):
            success, msg = register_user(new_user, new_pass)
            if success:
                st.success(msg)
            else:
                st.error(msg)