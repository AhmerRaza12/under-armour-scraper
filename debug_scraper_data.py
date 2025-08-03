#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import airtable

load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_TOKEN")
at = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)

def test_scraper_data():
    """Test the exact data structure that the scraper would send"""
    print("🔍 Testing scraper data structure...")
    
    # Simulate the exact data structure from the scraper
    test_data = {
        "Name": "Test Product",
        "Source URL": "https://test.com",
        "Coming Soon": False,
        "New Release": False,
        "Excluded from Discounts": False,
        "SKU/Product ID": "TEST-123",
        "Description": "Test description",
        "Product Description": "<p>Test</p>",
        "SEO Title Tag": "Test Title",
        "Product Brand or Title": "Under Armour",
        "Color Name": "Test Color",
        "Price for Sorting": 100,
        "Percent Discount": "0%",
        "Scraper Update": "2025-01-01 00:00:00"
    }
    
    print("✅ Basic fields added")
    
    # Test with actual data that might be causing issues
    test_cases = [
        {
            "name": "Test with empty strings in linked fields",
            "data": {
                **test_data,
                "SKUs": [],
                "Filter Category/ies": [],
                "Model Name": [],
                "Brand": [],
                "Size Guide": []
            }
        },
        {
            "name": "Test with None values in linked fields",
            "data": {
                **test_data,
                "SKUs": None,
                "Filter Category/ies": None,
                "Model Name": None,
                "Brand": None,
                "Size Guide": None
            }
        },
        {
            "name": "Test with string values in linked fields (this should fail)",
            "data": {
                **test_data,
                "SKUs": "invalid_string",
                "Filter Category/ies": "invalid_string",
                "Model Name": "invalid_string",
                "Brand": "invalid_string",
                "Size Guide": "invalid_string"
            }
        },
        {
            "name": "Test with mixed valid/invalid data",
            "data": {
                **test_data,
                "SKUs": [],
                "Filter Category/ies": "invalid_string",  # This should cause error
                "Model Name": [],
                "Brand": [],
                "Size Guide": []
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        try:
            result = at.create("Products", test_case['data'])
            print(f"✅ SUCCESS: Record created: {result['id']}")
            # Clean up
            at.delete("Products", result['id'])
            print("✅ Test record deleted")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            print("This test case shows the problematic data structure!")

if __name__ == "__main__":
    test_scraper_data() 