"""
Script to clean up base64-encoded profile pictures from the database.

This script will:
1. Find all contacts with base64-encoded profile_picture data
2. Remove the base64 data (set profile_picture to None)
3. Report how many contacts were cleaned up

Run this after implementing Cloudinary storage to improve database performance.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


async def cleanup_base64_images():
    """Remove base64-encoded images from database."""
    print("\n=== Cleaning up base64 profile pictures ===\n")

    # Connect to database
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]
    contacts = db.contacts

    # Find contacts with profile_picture starting with "data:image"
    query = {"profile_picture": {"$regex": "^data:image"}}

    # Count affected contacts
    count = await contacts.count_documents(query)
    print(f"Found {count} contacts with base64-encoded profile pictures")

    if count == 0:
        print("No cleanup needed!")
        client.close()
        return

    # Ask for confirmation
    response = input(f"\nDo you want to remove base64 data from {count} contacts? (yes/no): ")

    if response.lower() != 'yes':
        print("Operation cancelled")
        client.close()
        return

    # Update contacts - set profile_picture to None
    result = await contacts.update_many(
        query,
        {"$set": {"profile_picture": None}}
    )

    print(f"\n[OK] Successfully cleaned up {result.modified_count} contacts")
    print("Profile pictures have been set to None")
    print("Users can re-upload pictures which will now be stored in Cloudinary")

    client.close()
    print("\n=== Cleanup Complete ===\n")


if __name__ == "__main__":
    asyncio.run(cleanup_base64_images())
