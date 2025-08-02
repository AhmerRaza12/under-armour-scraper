#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import airtable

load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_TOKEN")
at = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)

def test_airtable_fields():
    """Test each field individually to find the problematic one"""
    print("🔍 Testing Airtable fields...")
    
    # Test data - minimal product data
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
    
    # Test 1: Add SKUs field
    try:
        test_data_with_skus = test_data.copy()
        test_data_with_skus["SKUs"] = []  # Empty array
        print("✅ SKUs field (empty array) - OK")
    except Exception as e:
        print(f"❌ SKUs field error: {e}")
    
    # Test 2: Add Filter Category field
    try:
        test_data_with_categories = test_data.copy()
        test_data_with_categories["Filter Category/ies"] = []  # Empty array
        print("✅ Filter Category/ies field (empty array) - OK")
    except Exception as e:
        print(f"❌ Filter Category/ies field error: {e}")
    
    # Test 3: Add Model Name field
    try:
        test_data_with_model = test_data.copy()
        test_data_with_model["Model Name"] = []  # Empty array
        print("✅ Model Name field (empty array) - OK")
    except Exception as e:
        print(f"❌ Model Name field error: {e}")
    
    # Test 4: Add Brand field
    try:
        test_data_with_brand = test_data.copy()
        test_data_with_brand["Brand"] = []  # Empty array
        print("✅ Brand field (empty array) - OK")
    except Exception as e:
        print(f"❌ Brand field error: {e}")
    
    # Test 5: Add Size Guide field
    try:
        test_data_with_size_guide = test_data.copy()
        test_data_with_size_guide["Size Guide"] = []  # Empty array
        print("✅ Size Guide field (empty array) - OK")
    except Exception as e:
        print(f"❌ Size Guide field error: {e}")
    
    # Test 6: Try to create a record with all fields
    try:
        print("\n🔍 Testing record creation with all fields...")
        result = at.create("Products", test_data)
        print(f"✅ Record created successfully: {result['id']}")
        
        # Clean up - delete the test record
        at.delete("Products", result['id'])
        print("✅ Test record deleted")
        
    except Exception as e:
        print(f"❌ Record creation failed: {e}")
        print("This is the field causing the issue!")

if __name__ == "__main__":
    test_airtable_fields() 