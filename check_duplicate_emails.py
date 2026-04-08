import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from collections import defaultdict

# MongoDB connection string
MONGODB_URI = "mongodb+srv://navansami_db_user:fairmont100@cluster0.frkrxj0.mongodb.net/"
DATABASE_NAME = "telbook"
COLLECTION_NAME = "contacts"

async def check_duplicate_emails():
    """Check for duplicate emails in the database."""

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    contacts_collection = db[COLLECTION_NAME]

    # Get all contacts with emails
    cursor = contacts_collection.find({"email": {"$ne": "", "$exists": True}})

    email_map = defaultdict(list)

    async for contact in cursor:
        email = contact.get('email', '').strip().lower()
        if email:
            email_map[email].append({
                'id': contact['_id'],
                'name': contact.get('name'),
                'email': contact.get('email')
            })

    # Find duplicates
    duplicates = {email: contacts for email, contacts in email_map.items() if len(contacts) > 1}

    if duplicates:
        print(f"Found {len(duplicates)} duplicate emails:\n")
        for email, contacts in duplicates.items():
            print(f"Email: {email}")
            for contact in contacts:
                print(f"  - ID: {contact['id']}, Name: {contact['name']}")
            print()
    else:
        print("No duplicate emails found!")

    # Check specifically for the email in question
    print("\nChecking for 'bouquetandco@gmail.com':")
    target_email = "bouquetandco@gmail.com"
    matches = await contacts_collection.find({"email": target_email}).to_list(length=10)

    if matches:
        print(f"Found {len(matches)} contact(s) with email '{target_email}':")
        for match in matches:
            print(f"  - ID: {match['_id']}")
            print(f"    Name: {match.get('name')}")
            print(f"    Email: {match.get('email')}")
            print(f"    Is 3rd Party: {match.get('is_third_party', False)}")
            print()
    else:
        print(f"No contacts found with email '{target_email}'")

    client.close()

if __name__ == "__main__":
    asyncio.run(check_duplicate_emails())
