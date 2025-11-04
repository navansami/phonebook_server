"""Debug script to analyze database performance."""

import asyncio
import time
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


async def analyze_performance():
    """Analyze database performance issues."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]
    contacts = db.contacts

    print("\n=== Database Performance Analysis ===\n")

    # 1. Count total contacts
    print("1. Counting contacts...")
    start = time.time()
    total = await contacts.count_documents({})
    elapsed = time.time() - start
    print(f"   Total contacts: {total}")
    print(f"   Time: {elapsed:.3f}s\n")

    # 2. Check indexes
    print("2. Checking indexes...")
    indexes = await contacts.index_information()
    print(f"   Indexes found: {len(indexes)}")
    for idx_name, idx_info in indexes.items():
        print(f"   - {idx_name}: {idx_info.get('key', [])}")
    print()

    # 3. Test query performance (first 500)
    print("3. Testing query with limit=500...")
    start = time.time()
    cursor = contacts.find({}).sort("name", 1).limit(500)
    results = await cursor.to_list(length=500)
    elapsed = time.time() - start
    print(f"   Fetched {len(results)} contacts")
    print(f"   Time: {elapsed:.3f}s\n")

    # 4. Check document size
    if results:
        import json
        sample = results[0]
        sample_size = len(json.dumps(sample, default=str))
        print(f"4. Sample document analysis:")
        print(f"   Sample document size: {sample_size} bytes")
        print(f"   Estimated total size for 500: {(sample_size * 500) / 1024:.2f} KB")
        print(f"   Document fields: {list(sample.keys())}\n")

    # 5. Test with projection (exclude large fields)
    print("5. Testing query with field projection...")
    start = time.time()
    cursor = contacts.find({}, {
        "_id": 1, "name": 1, "email": 1, "department": 1,
        "extension": 1, "mobile": 1, "designation": 1
    }).sort("name", 1).limit(500)
    results = await cursor.to_list(length=500)
    elapsed = time.time() - start
    print(f"   Fetched {len(results)} contacts (limited fields)")
    print(f"   Time: {elapsed:.3f}s\n")

    # 6. Check for any problematic fields
    print("6. Checking for large fields...")
    sample_contact = await contacts.find_one({})
    if sample_contact:
        for field, value in sample_contact.items():
            if isinstance(value, (str, list, dict)):
                size = len(str(value))
                if size > 1000:
                    print(f"   WARNING: Large field '{field}': {size} bytes")

    client.close()
    print("\n=== Analysis Complete ===\n")


if __name__ == "__main__":
    asyncio.run(analyze_performance())
