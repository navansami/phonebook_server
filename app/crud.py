from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from .database import get_database
from .models import ContactCreate, ContactUpdate, Contact, TaxonomyValue

TAXONOMY_CONFIG: Dict[str, Dict[str, str]] = {
    "departments": {"field": "department", "kind": "scalar"},
    "companies": {"field": "company", "kind": "scalar"},
    "designations": {"field": "designation", "kind": "scalar"},
    "tags": {"field": "tags", "kind": "array"},
    "languages": {"field": "languages", "kind": "array"},
}


def normalize_taxonomy_value(value: str) -> str:
    """Normalize taxonomy values for consistent matching."""
    return " ".join(value.split()).strip()


def get_taxonomy_config(taxonomy_type: str) -> Dict[str, str]:
    config = TAXONOMY_CONFIG.get(taxonomy_type)
    if not config:
        raise ValueError("Unsupported taxonomy type")
    return config


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
    limit: int = 20,
    include_pictures: bool = False
) -> tuple[List[Contact], int]:
    """Get contacts with filters and pagination."""
    db = get_database()
    contacts = db.contacts

    # Build query
    query: Dict[str, Any] = {}

    if search:
        # Use text search for better performance with indexes
        query["$text"] = {"$search": search}

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

    # Get contacts (optionally exclude profile_picture for performance)
    if include_pictures:
        # Include profile pictures (for admin dashboard)
        cursor = contacts.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
        contact_list = await cursor.to_list(length=limit)
        contacts_result = [Contact(id=c["_id"], **{k: v for k, v in c.items() if k != "_id"}) for c in contact_list]
    else:
        # Exclude profile pictures for faster loading (public view)
        projection = {"profile_picture": 0}
        cursor = contacts.find(query, projection).sort(sort_field, sort_direction).skip(skip).limit(limit)
        contact_list = await cursor.to_list(length=limit)

        # Convert to Contact objects, ensuring profile_picture is None when excluded
        contacts_result = []
        for c in contact_list:
            contact_dict = {k: v for k, v in c.items() if k != "_id"}
            contact_dict["profile_picture"] = None  # Set to None since it was excluded
            contacts_result.append(Contact(id=c["_id"], **contact_dict))

    return (contacts_result, total)


async def get_contacts_for_export(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    language: Optional[str] = None,
    is_ert: Optional[bool] = None,
    is_ifa: Optional[bool] = None,
    is_third_party: Optional[bool] = None,
    exclude_third_party: Optional[bool] = None,
    sort_by: str = "name",
) -> List[Contact]:
    """Get all contacts matching the given filters for export."""
    contacts, _ = await get_contacts(
        search=search,
        tag=tag,
        language=language,
        is_ert=is_ert,
        is_ifa=is_ifa,
        is_third_party=is_third_party,
        exclude_third_party=exclude_third_party,
        sort_by=sort_by,
        skip=0,
        limit=10000,
        include_pictures=True,
    )
    return contacts


async def update_contact(contact_id: str, contact_update: ContactUpdate) -> Optional[Contact]:
    """Update a contact."""
    db = get_database()
    contacts = db.contacts

    # Get existing contact
    existing = await contacts.find_one({"_id": contact_id})
    if not existing:
        return None

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


async def bulk_update_contacts(contact_ids: List[str], contact_update: ContactUpdate) -> int:
    """Bulk update multiple contacts."""
    db = get_database()
    contacts = db.contacts

    update_dict = contact_update.model_dump(exclude_unset=True)
    if not update_dict:
        raise ValueError("No updates provided")

    update_dict["updated_at"] = datetime.utcnow()
    result = await contacts.update_many(
        {"_id": {"$in": contact_ids}},
        {"$set": update_dict},
    )
    return result.modified_count


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


async def get_taxonomy_inventory(taxonomy_type: str) -> List[TaxonomyValue]:
    """Get live taxonomy inventory with stored values and contact usage."""
    config = get_taxonomy_config(taxonomy_type)
    db = get_database()
    contacts = db.contacts
    taxonomy_values = db.taxonomy_values

    counts: Dict[str, int] = {}
    display_names: Dict[str, str] = {}
    samples: Dict[str, List[str]] = {}

    cursor = contacts.find({}, {"name": 1, config["field"]: 1})
    async for contact in cursor:
      raw_value = contact.get(config["field"])
      raw_values = raw_value if config["kind"] == "array" and isinstance(raw_value, list) else [raw_value]
      for value in raw_values:
          if not value:
              continue
          normalized = normalize_taxonomy_value(value)
          if not normalized:
              continue
          counts[normalized] = counts.get(normalized, 0) + 1
          display_names.setdefault(normalized, value)
          samples.setdefault(normalized, [])
          contact_name = contact.get("name")
          if contact_name and len(samples[normalized]) < 3 and contact_name not in samples[normalized]:
              samples[normalized].append(contact_name)

    stored_cursor = taxonomy_values.find({"type": taxonomy_type}, {"name": 1, "normalized_name": 1})
    async for stored in stored_cursor:
        normalized = stored.get("normalized_name") or normalize_taxonomy_value(stored.get("name", ""))
        if not normalized:
            continue
        display_names.setdefault(normalized, stored.get("name", normalized))
        counts.setdefault(normalized, 0)
        samples.setdefault(normalized, [])

    items = [
        TaxonomyValue(name=display_names[normalized], count=counts[normalized], samples=samples[normalized])
        for normalized in counts.keys()
    ]
    items.sort(key=lambda item: (-item.count, item.name.lower()))
    return items


async def create_taxonomy_value(taxonomy_type: str, name: str) -> None:
    """Create a standalone taxonomy value."""
    normalized_name = normalize_taxonomy_value(name)
    if not normalized_name:
        raise ValueError("Name cannot be empty")

    get_taxonomy_config(taxonomy_type)
    db = get_database()
    taxonomy_values = db.taxonomy_values
    now = datetime.utcnow()

    await taxonomy_values.update_one(
        {"type": taxonomy_type, "normalized_name": normalized_name.casefold()},
        {
            "$set": {
                "type": taxonomy_type,
                "name": normalized_name,
                "normalized_name": normalized_name.casefold(),
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )


async def _update_contacts_for_taxonomy(
    taxonomy_type: str,
    current_name: str,
    new_name: Optional[str] = None,
) -> int:
    """Rename or remove a taxonomy value across contacts."""
    config = get_taxonomy_config(taxonomy_type)
    db = get_database()
    contacts = db.contacts
    current_normalized = normalize_taxonomy_value(current_name).casefold()
    replacement = normalize_taxonomy_value(new_name) if new_name else None
    updated_count = 0

    cursor = contacts.find({}, {"_id": 1, config["field"]: 1})
    async for contact in cursor:
        current_value = contact.get(config["field"])
        should_update = False

        if config["kind"] == "scalar":
            if current_value and normalize_taxonomy_value(current_value).casefold() == current_normalized:
                next_value = replacement
                should_update = True
            else:
                continue
        else:
            values = current_value if isinstance(current_value, list) else []
            next_values: List[str] = []
            seen = set()
            for value in values:
                candidate = replacement if normalize_taxonomy_value(value).casefold() == current_normalized else value
                if not candidate:
                    continue
                normalized_candidate = normalize_taxonomy_value(candidate).casefold()
                if normalized_candidate in seen:
                    continue
                seen.add(normalized_candidate)
                next_values.append(normalize_taxonomy_value(candidate))
            if next_values != values:
                next_value = next_values
                should_update = True
            else:
                continue

        if should_update:
            await contacts.update_one(
                {"_id": contact["_id"]},
                {"$set": {config["field"]: next_value, "updated_at": datetime.utcnow()}},
            )
            updated_count += 1

    return updated_count


async def rename_taxonomy_value(taxonomy_type: str, current_name: str, new_name: str) -> int:
    """Rename a taxonomy value and update all matching contacts."""
    current_normalized = normalize_taxonomy_value(current_name)
    next_normalized = normalize_taxonomy_value(new_name)
    if not current_normalized or not next_normalized:
        raise ValueError("Both current and new names are required")

    await create_taxonomy_value(taxonomy_type, next_normalized)
    updated_contacts = await _update_contacts_for_taxonomy(taxonomy_type, current_normalized, next_normalized)

    db = get_database()
    await db.taxonomy_values.delete_one(
        {"type": taxonomy_type, "normalized_name": current_normalized.casefold()}
    )

    return updated_contacts


async def delete_taxonomy_value(
    taxonomy_type: str,
    name: str,
    replacement_name: Optional[str] = None,
) -> int:
    """Delete a taxonomy value, optionally replacing it in all contacts first."""
    normalized_name = normalize_taxonomy_value(name)
    if not normalized_name:
        raise ValueError("Name is required")

    inventory = await get_taxonomy_inventory(taxonomy_type)
    current_item = next(
        (item for item in inventory if normalize_taxonomy_value(item.name).casefold() == normalized_name.casefold()),
        None,
    )
    usage_count = current_item.count if current_item else 0

    updated_contacts = 0
    if usage_count > 0:
        if not replacement_name or not normalize_taxonomy_value(replacement_name):
            raise ValueError("Replacement name is required for values currently used by contacts")
        replacement_normalized = normalize_taxonomy_value(replacement_name)
        await create_taxonomy_value(taxonomy_type, replacement_normalized)
        updated_contacts = await _update_contacts_for_taxonomy(taxonomy_type, normalized_name, replacement_normalized)

    db = get_database()
    await db.taxonomy_values.delete_one(
        {"type": taxonomy_type, "normalized_name": normalized_name.casefold()}
    )

    return updated_contacts
