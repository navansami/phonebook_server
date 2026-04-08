import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from app.models import Contact
from datetime import datetime
from app.config import settings

# MongoDB connection from settings
MONGODB_URI = settings.MONGODB_URI
DATABASE_NAME = settings.DATABASE_NAME
COLLECTION_NAME = "contacts"

async def test_contact_validation():
    """Test each contact to find validation issues."""

    # Connect to MongoDB
    print(f"Connecting to MongoDB...")
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
            print(f"\n❌ Validation error for contact {contact_doc.get('_id', 'UNKNOWN')}:")
            print(f"   Name: {contact_doc.get('name', 'N/A')}")
            print(f"   Error: {e}")
            problematic_contacts.append({
                'id': contact_doc.get('_id'),
                'name': contact_doc.get('name'),
                'error': str(e),
                'data': contact_doc
            })
        except Exception as e:
            print(f"\n❌ Unexpected error for contact {contact_doc.get('_id', 'UNKNOWN')}:")
            print(f"   Name: {contact_doc.get('name', 'N/A')}")
            print(f"   Error: {type(e).__name__}: {e}")
            problematic_contacts.append({
                'id': contact_doc.get('_id'),
                'name': contact_doc.get('name'),
                'error': str(e),
                'data': contact_doc
            })

    print(f"\n✅ Valid contacts: {valid_count}")
    print(f"❌ Problematic contacts: {len(problematic_contacts)}")

    if problematic_contacts:
        print("\n\nProblematic contact details:")
        print("=" * 80)
        for pc in problematic_contacts:
            print(f"\nID: {pc['id']}")
            print(f"Name: {pc['name']}")
            print(f"Error: {pc['error']}")
            print(f"Data keys: {list(pc['data'].keys())}")

            # Check for missing required fields
            required_fields = ['name', 'created_at', 'updated_at', 'languages', 'tags',
                             'expose', 'is_ert', 'is_third_party', 'is_ifa']
            missing_fields = [f for f in required_fields if f not in pc['data']]
            if missing_fields:
                print(f"Missing fields: {missing_fields}")

            # Check field types
            if 'languages' in pc['data']:
                print(f"Languages type: {type(pc['data']['languages'])}, value: {pc['data']['languages']}")
            if 'tags' in pc['data']:
                print(f"Tags type: {type(pc['data']['tags'])}, value: {pc['data']['tags']}")

    # Close connection
    client.close()
    print("\n\nValidation test complete!")

if __name__ == "__main__":
    asyncio.run(test_contact_validation())
