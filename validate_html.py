#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple validation script to test HTML parsing without requiring MongoDB
"""

import sys
import json
import re
from html.parser import HTMLParser
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class ContactDataExtractor(HTMLParser):
    """HTML parser to extract JSON data from script tag with id='contactData'"""

    def __init__(self):
        super().__init__()
        self.in_contact_data = False
        self.contact_data = None

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            attrs_dict = dict(attrs)
            if attrs_dict.get('id') == 'contactData':
                self.in_contact_data = True

    def handle_endtag(self, tag):
        if tag == 'script' and self.in_contact_data:
            self.in_contact_data = False

    def handle_data(self, data):
        if self.in_contact_data:
            # Try to extract JSON from the script content
            json_match = re.search(r'(?:var|const|let)\s+\w+\s*=\s*(\[.*\]);?', data, re.DOTALL)
            if json_match:
                try:
                    self.contact_data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            else:
                # Try direct JSON parsing
                try:
                    self.contact_data = json.loads(data.strip())
                except json.JSONDecodeError:
                    pass


def main():
    print("=" * 60)
    print("HTML VALIDATION TEST")
    print("=" * 60)

    html_file = Path(__file__).parent / "sample_contacts.html"

    if not html_file.exists():
        print(f"\nError: Sample file not found at {html_file}")
        return 1

    print(f"\nReading: {html_file}")

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    parser = ContactDataExtractor()
    parser.feed(html_content)

    if parser.contact_data:
        print(f"\n[SUCCESS] Found {len(parser.contact_data)} contacts")
        print(f"\nFirst contact:")
        print(json.dumps(parser.contact_data[0], indent=2))

        # Validate structure
        print(f"\nValidating contact structure...")
        required_fields = ['id', 'name']
        optional_fields = ['extension', 'company', 'department', 'designation',
                          'mobile', 'landline', 'email', 'languages', 'tags']

        first_contact = parser.contact_data[0]
        for field in required_fields:
            if field in first_contact:
                print(f"  [OK] {field}: {first_contact[field]}")
            else:
                print(f"  [MISSING] Required field: {field}")

        print(f"\nOptional fields present:")
        for field in optional_fields:
            if field in first_contact:
                value = first_contact[field]
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                print(f"  [OK] {field}: {value}")

        print(f"\n[SUCCESS] HTML parsing works correctly!")
        print(f"[SUCCESS] Migration script should be able to read this file")
        return 0
    else:
        print(f"\n[FAILED] Could not extract contact data")
        return 1


if __name__ == '__main__':
    exit(main())
