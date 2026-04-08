import json
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# MongoDB connection from settings
MONGODB_URI = settings.MONGODB_URI
DATABASE_NAME = settings.DATABASE_NAME
COLLECTION_NAME = "contacts"

async def seed_contacts():
    """Seed contacts from Telephonebook.json into MongoDB."""

    # Connect to MongoDB
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    contacts_collection = db[COLLECTION_NAME]

    # Read the JSON file
    print("Reading Telephonebook.json...")
    with open("Telephonebook.json", "r", encoding="utf-8") as f:
        contacts_data = json.load(f)

    print(f"Found {len(contacts_data)} contacts to import")

    # Transform and prepare contacts for insertion
    contacts_to_insert = []
    now = datetime.utcnow()

    for contact in contacts_data:
        # Skip contacts without names
        if not contact.get("name") or contact.get("name").strip() == "":
            print(f"Skipping contact {contact.get('id')} - no name")
            continue

        # Transform the contact data
        transformed_contact = {
            "_id": contact.get("id", ""),
            "name": contact.get("name", "").strip(),
            "extension": contact.get("extension", ""),
            "company": contact.get("company", ""),
            "department": contact.get("department", ""),
            "designation": contact.get("designation", ""),
            "mobile": contact.get("mobile", ""),
            "landline": contact.get("landline", ""),
            "email": contact.get("email", ""),
            "website": contact.get("website", ""),
            "comments": contact.get("comments", ""),
            "profile_picture": None,
            "expose": True,
            "is_ert": False,
            "is_third_party": False,
            "is_ifa": False,
            "created_at": now,
            "updated_at": now
        }

        # Parse languages (comma-separated string to list)
        languages_str = contact.get("languages", "")
        if languages_str:
            transformed_contact["languages"] = [lang.strip() for lang in languages_str.split(",") if lang.strip()]
        else:
            transformed_contact["languages"] = []

        # Parse tags (comma-separated string to list)
        tags_str = contact.get("tags", "")
        if tags_str:
            transformed_contact["tags"] = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        else:
            transformed_contact["tags"] = []

        contacts_to_insert.append(transformed_contact)

    if not contacts_to_insert:
        print("No valid contacts to insert!")
        client.close()
        return

    # Clear existing contacts (optional - remove this if you want to keep existing data)
    print(f"Clearing existing contacts...")
    delete_result = await contacts_collection.delete_many({})
    print(f"Deleted {delete_result.deleted_count} existing contacts")

    # Insert all contacts
    print(f"Inserting {len(contacts_to_insert)} contacts...")
    try:
        result = await contacts_collection.insert_many(contacts_to_insert, ordered=False)
        print(f"Successfully inserted {len(result.inserted_ids)} contacts!")
    except Exception as e:
        print(f"Error during insertion: {e}")
        print("Some contacts may have been inserted before the error occurred.")

    # Verify insertion
    count = await contacts_collection.count_documents({})
    print(f"Total contacts in database: {count}")

    # Close connection
    client.close()
    print("Database connection closed")

if __name__ == "__main__":
    asyncio.run(seed_contacts())
