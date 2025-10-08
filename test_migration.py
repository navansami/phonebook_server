#!/usr/bin/env python3
"""
Test script for the migration functionality
Tests the HTML parsing and data transformation without requiring MongoDB
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the extraction and transformation functions
try:
    from migrate_contacts import extract_contacts_from_html, transform_contact
except ImportError as e:
    print(f"Error importing migration functions: {e}")
    print("\nNote: This test can run without pymongo installed")
    print("It only tests the HTML parsing and data transformation logic")
    sys.exit(1)


def test_extraction():
    """Test HTML extraction"""
    print("Testing HTML extraction...")
    print("-" * 60)

    html_file = Path(__file__).parent / "sample_contacts.html"

    if not html_file.exists():
        print(f"Error: Sample file not found at {html_file}")
        return False

    contacts = extract_contacts_from_html(str(html_file))

    if not contacts:
        print("FAILED: Could not extract contacts")
        return False

    print(f"SUCCESS: Extracted {len(contacts)} contacts")
    print(f"\nFirst contact (raw):")
    print(json.dumps(contacts[0], indent=2))

    return True


def test_transformation():
    """Test data transformation"""
    print("\n\nTesting data transformation...")
    print("-" * 60)

    # Sample old format contact
    old_contact = {
        "id": "0001",
        "name": "John Doe",
        "extension": "3301",
        "company": "Fairmont The Palm",
        "department": "Executive Office",
        "designation": "General Manager",
        "mobile": "0501234567",
        "landline": "044573388",
        "email": "john.doe@fairmont.com",
        "website": "",
        "languages": "English, French, Arabic",
        "comments": "Available 24/7",
        "tags": "Executive Office, Higher Management",
        "expose": "all",
        "is_ert": True
    }

    print("Old format:")
    print(json.dumps(old_contact, indent=2))

    new_contact = transform_contact(old_contact)

    print("\n\nNew format:")
    print(json.dumps(new_contact, indent=2, default=str))

    # Validate transformation
    checks = [
        (new_contact['_id'] == '0001', "ID transformation"),
        (new_contact['name'] == 'John Doe', "Name field"),
        (isinstance(new_contact['languages'], list), "Languages is array"),
        (len(new_contact['languages']) == 3, "Languages parsed correctly"),
        ('English' in new_contact['languages'], "Languages contain English"),
        (isinstance(new_contact['tags'], list), "Tags is array"),
        (len(new_contact['tags']) == 2, "Tags parsed correctly"),
        (new_contact['is_ert'] == True, "is_ert field"),
        ('created_at' in new_contact, "created_at added"),
        ('updated_at' in new_contact, "updated_at added"),
    ]

    print("\n\nValidation:")
    all_passed = True
    for passed, description in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {description}")
        if not passed:
            all_passed = False

    return all_passed


def test_edge_cases():
    """Test edge cases in transformation"""
    print("\n\nTesting edge cases...")
    print("-" * 60)

    edge_cases = [
        {
            "name": "Empty fields test",
            "contact": {
                "id": "9999",
                "name": "Test User",
                "languages": "",
                "tags": "",
                "email": "",
                "comments": None,
            }
        },
        {
            "name": "Already array fields",
            "contact": {
                "id": "9998",
                "name": "Test User 2",
                "languages": ["English", "French"],
                "tags": ["Tag1", "Tag2"],
            }
        },
        {
            "name": "Whitespace handling",
            "contact": {
                "id": "9997",
                "name": "Test User 3",
                "languages": " English , French , Arabic ",
                "tags": "Tag1,  Tag2  , Tag3",
            }
        }
    ]

    all_passed = True
    for test_case in edge_cases:
        print(f"\nTest: {test_case['name']}")
        try:
            result = transform_contact(test_case['contact'])
            print(f"  ✓ Transformation successful")

            # Check arrays are always lists
            if not isinstance(result['languages'], list):
                print(f"  ✗ languages is not a list: {type(result['languages'])}")
                all_passed = False
            if not isinstance(result['tags'], list):
                print(f"  ✗ tags is not a list: {type(result['tags'])}")
                all_passed = False

        except Exception as e:
            print(f"  ✗ Failed: {e}")
            all_passed = False

    return all_passed


def main():
    """Run all tests"""
    print("=" * 60)
    print("MIGRATION SCRIPT TEST SUITE")
    print("=" * 60)

    tests = [
        ("HTML Extraction", test_extraction),
        ("Data Transformation", test_transformation),
        ("Edge Cases", test_edge_cases),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    print("=" * 60)
    if all_passed:
        print("\nAll tests passed! Migration script is ready to use.")
        return 0
    else:
        print("\nSome tests failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
