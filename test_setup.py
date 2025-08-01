#!/usr/bin/env python3
"""
Test script to verify the Under Armour Scraper setup
"""

import os
import sys
from dotenv import load_dotenv
import airtable
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test if all required environment variables are set"""
    load_dotenv()
    
    required_vars = [
        'AIRTABLE_BASE',
        'AIRTABLE_TOKEN',
        'IMGBB_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        logger.info("✅ All environment variables are set")
        return True

def test_airtable_connection():
    """Test Airtable connection and table access"""
    try:
        airtable_base = os.getenv("AIRTABLE_BASE")
        airtable_token = os.getenv("AIRTABLE_TOKEN")
        
        at = airtable.Airtable(airtable_base, airtable_token)
        
        # Test connection by trying to get records from Products table
        products = at.get("Products", max_records=1)
        logger.info("✅ Successfully connected to Airtable Products table")
        
        # Test SKUs table
        skus = at.get("SKUs", max_records=1)
        logger.info("✅ Successfully connected to Airtable SKUs table")
        
        # Test Customer Reviews table
        reviews = at.get("Customer Reviews", max_records=1)
        logger.info("✅ Successfully connected to Airtable Customer Reviews table")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Airtable connection failed: {e}")
        return False

def test_file_structure():
    """Test if required files exist"""
    required_files = [
        'under_armour_scraper.py',
        'daily_update.py',
        'scheduler.py',
        'startup.py',
        'requirements.txt',
        'Procfile',
        'app.json',
        'runtime.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        logger.info("✅ All required files exist")
        return True

def test_scraped_links_file():
    """Test if scraped_product_links.txt exists and has content"""
    if not os.path.exists('scraped_product_links.txt'):
        logger.warning("⚠️ scraped_product_links.txt not found - you'll need to add product URLs for daily updates")
        return False
    
    with open('scraped_product_links.txt', 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    if not lines:
        logger.warning("⚠️ scraped_product_links.txt is empty - you'll need to add product URLs for daily updates")
        return False
    
    logger.info(f"✅ scraped_product_links.txt contains {len(lines)} product URLs")
    return True

def main():
    """Run all tests"""
    logger.info("🧪 Testing Under Armour Scraper Setup...")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("File Structure", test_file_structure),
        ("Airtable Connection", test_airtable_connection),
        ("Scraped Links File", test_scraped_links_file)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' failed with exception: {e}")
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Your setup is ready.")
        logger.info("\n📋 Next steps:")
        logger.info("1. For local development: python under_armour_scraper.py")
        logger.info("2. For Heroku deployment: Follow the README.md instructions")
        logger.info("3. For daily updates: python daily_update.py")
    else:
        logger.error("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 