import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("dbName")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]

