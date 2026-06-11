from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

_client = MongoClient(os.getenv("MONGODB_URI"))
_db = _client[os.getenv("MONGODB_DB_NAME", "scout_agent_db")]
memories_col = _db["memories"]


def store_memory(session_id: str, memory_type: str, content: dict, embedding: list = []) -> dict:
    doc = {
        "session_id": session_id,
        "memory_type": memory_type,
        "content": content,
        "embedding": embedding,
        "created_at": datetime.utcnow(),
    }
    memories_col.insert_one(doc)
    return {"success": True}


def get_memories(session_id: str, memory_type: str = None) -> list:
    query = {"session_id": session_id}
    if memory_type:
        query["memory_type"] = memory_type
    return list(memories_col.find(query, {"_id": 0}).sort("created_at", -1).limit(50))


def get_preferences(session_id: str) -> dict | None:
    doc = memories_col.find_one(
        {"session_id": session_id, "memory_type": "preference"},
        {"_id": 0},
        sort=[("created_at", -1)],
    )
    return doc["content"] if doc else None


def get_blacklisted_players(session_id: str) -> list:
    docs = memories_col.find(
        {"session_id": session_id, "memory_type": "feedback", "content.signal": -1},
        {"_id": 0, "content.player_id": 1},
    )
    return [d["content"]["player_id"] for d in docs if "player_id" in d.get("content", {})]


def get_recent_searches(session_id: str, limit: int = 5) -> list:
    docs = memories_col.find(
        {"session_id": session_id, "memory_type": "search"},
        {"_id": 0, "content": 1},
    ).sort("created_at", -1).limit(limit)
    return [d["content"] for d in docs]


def delete_memories(session_id: str) -> dict:
    result = memories_col.delete_many({"session_id": session_id})
    return {"deleted": result.deleted_count}