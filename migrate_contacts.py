#!/usr/bin/env python3
"""
Contact Migration Script
========================
Migrates contacts from JSON file to MongoDB database.

Usage:
    python migrate_contacts.py [--json-file PATH] [--skip-duplicates]

Options:
    --json-file PATH      Path to JSON file with contact data
    --skip-duplicates     Skip duplicate contacts instead of updating them
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from pymongo import MongoClient, UpdateOne
    from pymongo.errors import BulkWriteError, ConnectionFailure
except ImportError:
    print("Error: pymongo is required. Install it with: pip install pymongo")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv is required. Install it with: pip install python-dotenv")
    sys.exit(1)




def load_env():
    """Load environment variables from .env file"""
    # Try to find .env file in various locations
    possible_locations = [
        Path(__file__).parent / '.env',
        Path(__file__).parent.parent / '.env',
        Path(__file__).parent.parent / 'server' / '.env',
    ]

    env_loaded = False
    for env_path in possible_locations:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"Loaded environment from: {env_path}")
            env_loaded = True
            break

    if not env_loaded:
        print("Warning: No .env file found, using environment variables")

    return env_loaded


def extract_contacts_from_json(json_file_path: str) -> Optional[List[Dict[str, Any]]]:
    """Extract contact data from JSON file"""
    print(f"\nReading JSON file: {json_file_path}")

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            contacts = json.load(f)

        if not isinstance(contacts, list):
            print("Error: JSON file must contain an array of contacts")
            return None

        print(f"Found {len(contacts)} contacts in JSON file")
        return contacts
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}")
        return None
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return None


def transform_contact(old_contact: Dict[str, Any]) -> Dict[str, Any]:
    """Transform old contact format to new schema"""
    current_time = datetime.utcnow()

    # Helper function to convert comma-separated string to array
    def to_array(value: Any) -> List[str]:
        if value is None or value == '':
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            # Split by comma and clean up
            return [item.strip() for item in value.split(',') if item.strip()]
        return []

    # Helper function to convert empty strings to None
    def to_optional(value: Any) -> Optional[str]:
        if value is None or value == '' or value == 'null':
            return None
        return str(value)

    # Build the new contact document
    new_contact = {
        '_id': str(old_contact.get('id', '')),
        'name': old_contact.get('name', '').strip(),
        'extension': to_optional(old_contact.get('extension')),
        'company': to_optional(old_contact.get('company')),
        'department': to_optional(old_contact.get('department')),
        'designation': to_optional(old_contact.get('designation')),
        'mobile': to_optional(old_contact.get('mobile')),
        'landline': to_optional(old_contact.get('landline')),
        'email': to_optional(old_contact.get('email')),
        'website': to_optional(old_contact.get('website')),
        'comments': to_optional(old_contact.get('comments')),
        'expose': True,  # Default to True for all contacts
        'languages': to_array(old_contact.get('languages')),
        'tags': to_array(old_contact.get('tags')),
        'is_ert': old_contact.get('is_ert', False),
        'created_at': current_time,
        'updated_at': current_time,
    }

    return new_contact


def connect_to_mongodb() -> Optional[MongoClient]:
    """Connect to MongoDB using connection string from environment"""
    mongodb_uri = os.getenv('MONGODB_URI')

    if not mongodb_uri:
        print("Error: MONGODB_URI not found in environment variables")
        print("Please ensure .env file exists with MONGODB_URI defined")
        return None

    print(f"\nConnecting to MongoDB...")
    print(f"URI: {mongodb_uri[:20]}...{mongodb_uri[-10:] if len(mongodb_uri) > 30 else ''}")

    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB")
        return client
    except ConnectionFailure as e:
        print(f"Error: Failed to connect to MongoDB: {e}")
        return None
    except Exception as e:
        print(f"Error: Unexpected error connecting to MongoDB: {e}")
        return None


def migrate_contacts(
    contacts: List[Dict[str, Any]],
    client: MongoClient,
    skip_duplicates: bool = False
) -> Dict[str, int]:
    """
    Migrate contacts to MongoDB

    Returns:
        Dictionary with migration statistics
    """
    db_name = os.getenv('DATABASE_NAME', 'telbook')
    db = client[db_name]
    collection = db['contacts']

    print(f"\nDatabase: {db_name}")
    print(f"Collection: contacts")
    print(f"Total contacts to migrate: {len(contacts)}")
    print(f"Duplicate handling: {'skip' if skip_duplicates else 'update'}")
    print()

    stats = {
        'total': len(contacts),
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0,
    }

    # Transform all contacts
    print("Transforming contact data...")
    transformed_contacts = []
    for i, contact in enumerate(contacts, 1):
        try:
            transformed = transform_contact(contact)
            transformed_contacts.append(transformed)

            # Show progress every 20 contacts
            if i % 20 == 0 or i == len(contacts):
                print(f"  Transformed {i}/{len(contacts)} contacts...")
        except Exception as e:
            print(f"  Error transforming contact {contact.get('id', 'unknown')}: {e}")
            stats['errors'] += 1

    print(f"Successfully transformed {len(transformed_contacts)} contacts")

    # Prepare bulk operations
    print("\nPreparing bulk operations...")
    operations = []

    for contact in transformed_contacts:
        if skip_duplicates:
            # Insert only if not exists (skip duplicates)
            operations.append(
                UpdateOne(
                    {'_id': contact['_id']},
                    {'$setOnInsert': contact},
                    upsert=True
                )
            )
        else:
            # Update existing or insert new (preserving created_at for existing)
            operations.append(
                UpdateOne(
                    {'_id': contact['_id']},
                    {
                        '$set': {k: v for k, v in contact.items() if k != 'created_at'},
                        '$setOnInsert': {'created_at': contact['created_at']}
                    },
                    upsert=True
                )
            )

    # Execute bulk write
    print(f"Executing bulk write operation...")
    try:
        result = collection.bulk_write(operations, ordered=False)

        stats['inserted'] = result.upserted_count
        stats['updated'] = result.modified_count
        stats['skipped'] = stats['total'] - stats['inserted'] - stats['updated'] - stats['errors']

        print("Bulk write completed successfully")

    except BulkWriteError as e:
        print(f"Warning: Some operations failed during bulk write")
        # Get stats from the error details
        write_errors = e.details.get('writeErrors', [])
        stats['errors'] += len(write_errors)

        # Try to get successful operation counts
        if hasattr(e, 'details'):
            stats['inserted'] = e.details.get('nUpserted', 0)
            stats['updated'] = e.details.get('nModified', 0)

    except Exception as e:
        print(f"Error during bulk write: {e}")
        stats['errors'] = stats['total']

    return stats


def print_summary(stats: Dict[str, int], elapsed_time: float):
    """Print migration summary"""
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Total contacts:      {stats['total']}")
    print(f"Successfully inserted: {stats['inserted']}")
    print(f"Updated:             {stats['updated']}")
    print(f"Skipped:             {stats['skipped']}")
    print(f"Errors:              {stats['errors']}")
    print(f"Time elapsed:        {elapsed_time:.2f} seconds")
    print("=" * 60)

    if stats['errors'] > 0:
        print("\nWarning: Some contacts failed to migrate. Please check the logs above.")
        return False
    elif stats['inserted'] == 0 and stats['updated'] == 0:
        print("\nInfo: No new contacts were inserted or updated.")
        return True
    else:
        print("\nSuccess: Migration completed successfully!")
        return True


def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(
        description='Migrate contacts from JSON file to MongoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--json-file',
        default=r'C:\Users\darrk\Downloads\Contacts.json',
        help='Path to JSON file with contact data'
    )
    parser.add_argument(
        '--skip-duplicates',
        action='store_true',
        help='Skip duplicate contacts instead of updating them'
    )

    args = parser.parse_args()

    # Print header
    print("=" * 60)
    print("CONTACT MIGRATION SCRIPT")
    print("=" * 60)

    start_time = datetime.now()

    # Step 1: Load environment variables
    print("\nStep 1: Loading environment variables")
    load_env()

    # Step 2: Extract contacts from JSON
    print("\nStep 2: Extracting contacts from JSON file")
    contacts = extract_contacts_from_json(args.json_file)

    if not contacts:
        print("\nError: No contacts found. Migration aborted.")
        sys.exit(1)

    # Step 3: Connect to MongoDB
    print("\nStep 3: Connecting to MongoDB")
    client = connect_to_mongodb()

    if not client:
        print("\nError: Could not connect to MongoDB. Migration aborted.")
        sys.exit(1)

    try:
        # Step 4: Migrate contacts
        print("\nStep 4: Migrating contacts")
        stats = migrate_contacts(contacts, client, args.skip_duplicates)

        # Step 5: Print summary
        elapsed = (datetime.now() - start_time).total_seconds()
        success = print_summary(stats, elapsed)

        sys.exit(0 if success else 1)

    finally:
        # Close connection
        if client:
            client.close()
            print("\nMongoDB connection closed")


if __name__ == '__main__':
    main()
