from datetime import datetime
from db.connection import players_collection
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

_client = MongoClient(os.getenv("MONGODB_URI"))
_db = _client[os.getenv("MONGODB_DB_NAME", "scout_agent_db")]
shortlists_col = _db["shortlists"]


def save_shortlist(session_id: str, name: str, player_names: list, notes: str = "") -> dict:
    existing = shortlists_col.find_one({"session_id": session_id, "name": name})
    doc = {
        "session_id": session_id,
        "name": name,
        "player_names": player_names,
        "notes": notes,
        "updated_at": datetime.utcnow(),
    }
    if existing:
        shortlists_col.update_one({"_id": existing["_id"]}, {"$set": doc})
    else:
        doc["created_at"] = datetime.utcnow()
        shortlists_col.insert_one(doc)
    return {"success": True, "name": name, "count": len(player_names)}


def get_shortlist(session_id: str, name: str) -> dict | None:
    doc = shortlists_col.find_one({"session_id": session_id, "name": name}, {"_id": 0})
    return doc


def get_all_shortlists(session_id: str) -> list:
    return list(shortlists_col.find({"session_id": session_id}, {"_id": 0}))


def delete_shortlist(session_id: str, name: str) -> dict:
    result = shortlists_col.delete_one({"session_id": session_id, "name": name})
    return {"success": result.deleted_count > 0}


def add_player_to_shortlist(session_id: str, name: str, player_name: str) -> dict:
    shortlists_col.update_one(
        {"session_id": session_id, "name": name},
        {
            "$addToSet": {"player_names": player_name},
            "$set": {"updated_at": datetime.utcnow()},
            "$setOnInsert": {"created_at": datetime.utcnow(), "notes": ""},
        },
        upsert=True,
    )
    return {"success": True}


def remove_player_from_shortlist(session_id: str, name: str, player_name: str) -> dict:
    shortlists_col.update_one(
        {"session_id": session_id, "name": name},
        {"$pull": {"player_names": player_name}, "$set": {"updated_at": datetime.utcnow()}},
    )
    return {"success": True}