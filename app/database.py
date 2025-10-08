from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """Create database connection."""
    global client, database
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = client[settings.DATABASE_NAME]
    print(f"[OK] Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_mongo_connection():
    """Close database connection."""
    global client
    if client:
        client.close()
        print("[OK] Closed MongoDB connection")


def get_database():
    """Get database instance."""
    return database
