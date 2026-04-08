import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from app.models import Contact

# MongoDB connection string
MONGODB_URI = "mongodb+srv://navansami_db_user:fairmont100@cluster0.frkrxj0.mongodb.net/"
DATABASE_NAME = "telbook"
COLLECTION_NAME = "contacts"

async def find_and_fix_validation_issues():
    """Find and fix all validation issues."""

    # Connect to MongoDB
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    contacts_collection = db[COLLECTION_NAME]

    # Get all contacts
    print("Fetching all contacts...")
    cursor = contacts_collection.find()

    problematic_contacts = []
    valid_count = 0

    async for contact_doc in cursor:
        try:
            # Try to create a Contact object
            contact = Contact(
                id=contact_doc["_id"],
                **{k: v for k, v in contact_doc.items() if k != "_id"}
            )
            valid_count += 1
        except ValidationError as e:
            problematic_contacts.append({
                'id': contact_doc.get('_id'),
                'name': contact_doc.get('name'),
                'error': str(e),
                'data': contact_doc
            })
        except Exception as e:
            problematic_contacts.append({
                'id': contact_doc.get('_id'),
                'name': contact_doc.get('name'),
                'error': str(e),
                'data': contact_doc
            })

    print(f"Valid contacts: {valid_count}")
    print(f"Problematic contacts: {len(problematic_contacts)}")

    if problematic_contacts:
        print("\n" + "="*80)
        print("PROBLEMATIC CONTACTS:")
        print("="*80)

        for pc in problematic_contacts:
            print(f"\nID: {pc['id']}")
            print(f"Name: {pc['name']}")

            # Check for field length issues
            data = pc['data']
            if 'extension' in data and data['extension'] and len(str(data['extension'])) > 20:
                print(f"  - Extension too long ({len(data['extension'])} chars): {data['extension']}")
            if 'mobile' in data and data['mobile'] and len(str(data['mobile'])) > 50:
                print(f"  - Mobile too long ({len(data['mobile'])} chars): {data['mobile']}")
            if 'landline' in data and data['landline'] and len(str(data['landline'])) > 50:
                print(f"  - Landline too long ({len(data['landline'])} chars): {data['landline']}")
            if 'email' in data and data['email'] and len(str(data['email'])) > 200:
                print(f"  - Email too long ({len(data['email'])} chars): {data['email']}")
            if 'website' in data and data['website'] and len(str(data['website'])) > 500:
                print(f"  - Website too long ({len(data['website'])} chars): {data['website']}")
            if 'name' in data and data['name'] and len(str(data['name'])) > 200:
                print(f"  - Name too long ({len(data['name'])} chars): {data['name']}")
            if 'company' in data and data['company'] and len(str(data['company'])) > 200:
                print(f"  - Company too long ({len(data['company'])} chars): {data['company']}")
            if 'department' in data and data['department'] and len(str(data['department'])) > 200:
                print(f"  - Department too long ({len(data['department'])} chars): {data['department']}")
            if 'designation' in data and data['designation'] and len(str(data['designation'])) > 200:
                print(f"  - Designation too long ({len(data['designation'])} chars): {data['designation']}")

        # Ask user if they want to fix
        print("\n" + "="*80)
        print("FIXING ISSUES...")
        print("="*80)

        for pc in problematic_contacts:
            contact_id = pc['id']
            data = pc['data']
            updates = {}

            # Truncate fields that are too long
            if 'extension' in data and data['extension'] and len(str(data['extension'])) > 20:
                original = data['extension']
                # Keep only the first extension if comma-separated
                truncated = original.split(',')[0].strip() if ',' in original else original[:20]
                updates['extension'] = truncated
                print(f"\n{contact_id} - {pc['name']}")
                print(f"  Extension: '{original}' -> '{truncated}'")

            if 'mobile' in data and data['mobile'] and len(str(data['mobile'])) > 50:
                updates['mobile'] = str(data['mobile'])[:50]
                print(f"\n{contact_id} - {pc['name']}")
                print(f"  Truncated mobile to 50 chars")

            if 'landline' in data and data['landline'] and len(str(data['landline'])) > 50:
                updates['landline'] = str(data['landline'])[:50]
                print(f"\n{contact_id} - {pc['name']}")
                print(f"  Truncated landline to 50 chars")

            if 'email' in data and data['email'] and len(str(data['email'])) > 200:
                updates['email'] = str(data['email'])[:200]
                print(f"\n{contact_id} - {pc['name']}")
                print(f"  Truncated email to 200 chars")

            # Apply updates
            if updates:
                await contacts_collection.update_one(
                    {"_id": contact_id},
                    {"$set": updates}
                )
                print(f"  -> Updated successfully")

        print(f"\nFixed {len(problematic_contacts)} contacts")

    # Close connection
    client.close()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(find_and_fix_validation_issues())
