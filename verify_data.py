import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pprint import pprint

# MongoDB connection string
MONGODB_URI = "mongodb+srv://navansami_db_user:fairmont100@cluster0.frkrxj0.mongodb.net/"
DATABASE_NAME = "telbook"
COLLECTION_NAME = "contacts"

async def verify_data():
    """Verify the seeded data and check for any issues."""

    # Connect to MongoDB
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    contacts_collection = db[COLLECTION_NAME]

    # Count total contacts
    total = await contacts_collection.count_documents({})
    print(f"Total contacts in database: {total}")

    # Get first 3 contacts to verify structure
    print("\nSample contacts (first 3):")
    cursor = contacts_collection.find().limit(3)
    async for contact in cursor:
        print("\n---")
        pprint(contact)

    # Check for any contacts with missing required fields
    print("\n\nChecking for data issues...")

    # Check for missing or empty names
    missing_names = await contacts_collection.count_documents({"$or": [{"name": ""}, {"name": {"$exists": False}}]})
    print(f"Contacts with missing/empty names: {missing_names}")

    # Check for missing created_at/updated_at
    missing_timestamps = await contacts_collection.count_documents({
        "$or": [
            {"created_at": {"$exists": False}},
            {"updated_at": {"$exists": False}}
        ]
    })
    print(f"Contacts with missing timestamps: {missing_timestamps}")

    # Check for contacts where languages or tags are not arrays
    not_array_langs = await contacts_collection.count_documents({"languages": {"$not": {"$type": "array"}}})
    not_array_tags = await contacts_collection.count_documents({"tags": {"$not": {"$type": "array"}}})
    print(f"Contacts with non-array languages: {not_array_langs}")
    print(f"Contacts with non-array tags: {not_array_tags}")

    # Close connection
    client.close()
    print("\nVerification complete!")

if __name__ == "__main__":
    asyncio.run(verify_data())
