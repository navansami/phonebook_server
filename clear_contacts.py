"""
Clear all contacts from the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "telbook")


async def clear_contacts():
    """Clear all contacts from the database"""
    print("=" * 60)
    print("CLEARING ALL CONTACTS")
    print("=" * 60)
    print()

    # Connect to MongoDB
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    contacts_collection = db.contacts

    try:
        # Get current count
        count = await contacts_collection.count_documents({})
        print(f"Current contacts in database: {count}")

        if count == 0:
            print("Database is already empty.")
            return

        # Delete all contacts
        result = await contacts_collection.delete_many({})
        print(f"\n[OK] Successfully deleted {result.deleted_count} contacts!")

        print()
        print("=" * 60)
        print("Database is now empty and ready for real data.")
        print("Add contacts through the admin dashboard at:")
        print("http://localhost:5174/admin")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(clear_contacts())
