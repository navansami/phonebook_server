"""Database indexes for performance optimization."""

from .database import get_database


async def create_indexes():
    """Create all necessary indexes for optimal query performance."""
    db = get_database()
    contacts = db.contacts

    # Create indexes for frequently queried fields
    await contacts.create_index("name")
    await contacts.create_index("department")
    await contacts.create_index("extension")
    await contacts.create_index("email")
    await contacts.create_index("tags")
    await contacts.create_index("languages")
    await contacts.create_index("is_ert")
    await contacts.create_index("is_ifa")
    await contacts.create_index("is_third_party")

    # Compound index for common filter combinations
    await contacts.create_index([("name", 1), ("department", 1)])
    await contacts.create_index([("is_third_party", 1), ("name", 1)])

    # Text index for search functionality
    await contacts.create_index([
        ("name", "text"),
        ("department", "text"),
        ("designation", "text"),
        ("tags", "text")
    ])

    print("[OK] Database indexes created successfully")
