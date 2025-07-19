from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI

mongo_client = AsyncIOMotorClient(DB_URI)
database = mongo_client.restricted_save
users_collection = database['users']
sessions_collection = database['sessions']
