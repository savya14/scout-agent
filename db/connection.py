from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)

client.admin.command("ping")

db = client[DB_NAME]

players_collection = db["players"]

print("✅ MongoDB Atlas Connected")


def get_collection(name: str):
    return db[name]


def get_db():
    return db