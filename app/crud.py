from typing import List, Optional, Dict, Any
from datetime import datetime
from .database import get_database
from .models import ContactCreate, ContactUpdate, Contact


async def get_next_contact_id() -> str:
    """Generate the next sequential contact ID."""
    db = get_database()
    contacts = db.contacts

    # Find the highest ID
    last_contact = await contacts.find_one(
        sort=[("_id", -1)]
    )

    if not last_contact:
        return "0001"

    try:
        last_id = int(last_contact["_id"])
        next_id = last_id + 1
        return f"{next_id:04d}"
    except (ValueError, KeyError):
        # If ID format is different, count documents
        count = await contacts.count_documents({})
        return f"{count + 1:04d}"


async def create_contact(contact: ContactCreate) -> Contact:
    """Create a new contact."""
    db = get_database()
    contacts = db.contacts

    # Check for duplicate email if email is provided
    if contact.email:
        existing_contact = await contacts.find_one({"email": contact.email})
        if existing_contact:
            raise ValueError(f"A contact with email '{contact.email}' already exists")

    contact_id = await get_next_contact_id()
    now = datetime.utcnow()

    contact_dict = contact.model_dump()
    contact_dict["_id"] = contact_id
    contact_dict["created_at"] = now
    contact_dict["updated_at"] = now

    await contacts.insert_one(contact_dict)

    return Contact(id=contact_id, **contact.model_dump(), created_at=now, updated_at=now)


async def get_contact(contact_id: str) -> Optional[Contact]:
    """Get a single contact by ID."""
    db = get_database()
    contacts = db.contacts

    contact = await contacts.find_one({"_id": contact_id})
    if not contact:
        return None

    return Contact(
        id=contact["_id"],
        **{k: v for k, v in contact.items() if k not in ["_id"]}
    )


async def get_contacts(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    language: Optional[str] = None,
    is_ert: Optional[bool] = None,
    is_ifa: Optional[bool] = None,
    is_third_party: Optional[bool] = None,
    exclude_third_party: Optional[bool] = None,
    sort_by: str = "name",
    skip: int = 0,
    limit: int = 20
) -> tuple[List[Contact], int]:
    """Get contacts with filters and pagination."""
    db = get_database()
    contacts = db.contacts

    # Build query
    query: Dict[str, Any] = {}

    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"department": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}},
            {"designation": {"$regex": search, "$options": "i"}},
        ]

    if tag:
        query["tags"] = {"$regex": tag, "$options": "i"}

    if language:
        query["languages"] = {"$regex": language, "$options": "i"}

    if is_ert is not None:
        query["is_ert"] = is_ert

    if is_ifa is not None:
        query["is_ifa"] = is_ifa

    if is_third_party is not None:
        query["is_third_party"] = is_third_party

    if exclude_third_party:
        query["is_third_party"] = {"$ne": True}

    # Count total
    total = await contacts.count_documents(query)

    # Build sort
    sort_field = "name"
    sort_direction = 1  # ascending

    if sort_by == "department":
        sort_field = "department"
    elif sort_by == "extension":
        sort_field = "extension"
        sort_direction = -1  # descending for extension

    # Get contacts
    cursor = contacts.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
    contact_list = await cursor.to_list(length=limit)

    return (
        [Contact(id=c["_id"], **{k: v for k, v in c.items() if k != "_id"}) for c in contact_list],
        total
    )


async def update_contact(contact_id: str, contact_update: ContactUpdate) -> Optional[Contact]:
    """Update a contact."""
    db = get_database()
    contacts = db.contacts

    # Get existing contact
    existing = await contacts.find_one({"_id": contact_id})
    if not existing:
        return None

    # Check for duplicate email if email is being updated
    if contact_update.email:
        duplicate = await contacts.find_one({
            "email": contact_update.email,
            "_id": {"$ne": contact_id}  # Exclude current contact
        })
        if duplicate:
            raise ValueError(f"A contact with email '{contact_update.email}' already exists")

    # Build update dict
    update_dict = contact_update.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()

    # Update
    await contacts.update_one(
        {"_id": contact_id},
        {"$set": update_dict}
    )

    # Get updated contact
    updated = await contacts.find_one({"_id": contact_id})
    return Contact(
        id=updated["_id"],
        **{k: v for k, v in updated.items() if k != "_id"}
    )


async def delete_contact(contact_id: str) -> bool:
    """Delete a contact."""
    db = get_database()
    contacts = db.contacts

    result = await contacts.delete_one({"_id": contact_id})
    return result.deleted_count > 0


async def get_all_tags() -> List[str]:
    """Get all unique tags."""
    db = get_database()
    contacts = db.contacts

    # Get all contacts and extract tags
    cursor = contacts.find({}, {"tags": 1})
    all_tags = set()

    async for contact in cursor:
        if "tags" in contact and contact["tags"]:
            all_tags.update(contact["tags"])

    return sorted(list(all_tags))


async def get_all_languages() -> List[str]:
    """Get all unique languages (excluding English)."""
    db = get_database()
    contacts = db.contacts

    # Get all contacts and extract languages
    cursor = contacts.find({}, {"languages": 1})
    all_languages = set()

    async for contact in cursor:
        if "languages" in contact and contact["languages"]:
            all_languages.update(contact["languages"])

    # Remove English
    all_languages.discard("English")

    return sorted(list(all_languages))
