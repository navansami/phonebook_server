import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from app.models import Contact
from app.config import settings

# MongoDB connection from settings
MONGODB_URI = settings.MONGODB_URI
DATABASE_NAME = settings.DATABASE_NAME
COLLECTION_NAME = "contacts"

async def simple_validation_test():
    """Simple validation test without unicode."""

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    contacts_collection = db[COLLECTION_NAME]

    cursor = contacts_collection.find()

    valid_count = 0
    error_count = 0

    async for contact_doc in cursor:
        try:
            contact = Contact(
                id=contact_doc["_id"],
                **{k: v for k, v in contact_doc.items() if k != "_id"}
            )
            valid_count += 1
        except:
            error_count += 1
            print(f"ERROR: Contact {contact_doc.get('_id')} - {contact_doc.get('name')}")

    print(f"Valid: {valid_count}")
    print(f"Errors: {error_count}")

    client.close()

if __name__ == "__main__":
    asyncio.run(simple_validation_test())
