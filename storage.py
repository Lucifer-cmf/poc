import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["vector_db"]
chat_collection = db["chat_history"]


# -------- Save chat message --------
def save_message(username, role, message):
    chat_collection.insert_one({
        "username": username,
        "role": role,
        "message": message,
        "timestamp": datetime.now()
    })


# -------- Load chat history --------
def load_chat_history(username):
    chats = chat_collection.find(
        {"username": username}
    ).sort("timestamp", 1)

    history = []
    for chat in chats:
        history.append((chat["role"], chat["message"]))
    return history


# -------- Clear chat history --------
def clear_chat(username):
    chat_collection.delete_many({"username": username})