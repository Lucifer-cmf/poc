import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import uuid
from bson import ObjectId

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["vector_db"]

chat_collection = db["chat_history"]
orgs_collection = db["organizations"]
memberships_collection = db["memberships"]
invites_collection = db["invitations"]
users_collection = db["users"]


def save_message(user_id, role, message):
    chat_collection.insert_one({
        "user_id": user_id,
        "role": role,
        "message": message,
        "timestamp": datetime.now()
    })


def load_chat_history(user_id):
    chats = chat_collection.find(
        {"user_id": user_id}
    ).sort("timestamp", 1)

    return [(c["role"], c["message"]) for c in chats]


# -------- Organization functions --------
def get_user_orgs(user_id):
    memberships = memberships_collection.find({"user_id": user_id})
    org_ids = [ObjectId(m["org_id"]) for m in memberships]
    return list(orgs_collection.find({"_id": {"$in": org_ids}}))


# -------- Invitation functions --------
def create_invite(email, org_id, role="member"):
    token = str(uuid.uuid4())

    invites_collection.insert_one({
        "email": email,
        "org_id": org_id,
        "role": role,
        "token": token,
        "status": "pending",
        "created_at": datetime.now()
    })

    return token


def accept_invite(token, password):
    invite = invites_collection.find_one({"token": token, "status": "pending"})
    if not invite:
        return False, "Invalid or expired invite"

    # Create user
    user = {
        "email": invite["email"],
        "password": password,
        "created_at": datetime.now()
    }
    result = users_collection.insert_one(user)
    user_id = str(result.inserted_id)

    memberships_collection.insert_one({
        "user_id": user_id,
        "org_id": invite["org_id"],
        "role": invite["role"]
    })

    invites_collection.update_one(
        {"token": token},
        {"$set": {"status": "accepted"}}
    )

    return True, "Invite accepted"
