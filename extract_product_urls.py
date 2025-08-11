#!/usr/bin/env python3
"""
Extract Product URLs from Airtable
This script extracts product source URLs from Airtable and overwrites scraped_product_links.txt
"""

import os
from dotenv import load_dotenv
import airtable

# Load environment variables
load_dotenv()

# Airtable configuration
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_TOKEN")
at = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)

def extract_product_urls():
    """Extract product source URLs from Airtable Products table"""
    print("[🔄] Starting to extract product URLs from Airtable...")
    
    try:
        all_urls = []
        offset = None
        
        while True:
            if offset:
                products = at.get("Products", offset=offset)
            else:
                products = at.get("Products")
            
            # Process each product record
            for product in products["records"]:
                fields = product.get("fields", {})
                product_name = fields.get("Name", "")
                source_url = fields.get("Source URL", "")
                
                # Skip if no source URL
                if not source_url:
                    continue
                
                # Skip the specific polo shirt
                if "Grey Under Armour Tech Polo Shirt​" in product_name:
                    print(f"[⏭️] Skipping polo shirt: {product_name}")
                    continue
                
                # Only include products with "Under Armour" in the name
                if "Under Armour" in product_name:
                    all_urls.append(source_url)
                    print(f"[✅] Added: {product_name}")
                else:
                    print(f"[⏭️] Skipping non-UA product: {product_name}")
            
            # Check if there are more records
            if "offset" in products:
                offset = products["offset"]
            else:
                break
        
        print(f"[📊] Found {len(all_urls)} Under Armour products with source URLs")
        return all_urls
        
    except Exception as e:
        print(f"[❌] Error extracting product URLs: {e}")
        return []

def overwrite_scraped_links_file(urls):
    """Overwrite scraped_product_links.txt with new URLs"""
    try:
        # Delete existing file if it exists
        if os.path.exists("scraped_product_links.txt"):
            os.remove("scraped_product_links.txt")
            print("[🗑️] Deleted existing scraped_product_links.txt")
        
        # Write new URLs to file
        with open("scraped_product_links.txt", "w") as file:
            for url in urls:
                file.write(url + "\n")
        
        print(f"[💾] Successfully wrote {len(urls)} URLs to scraped_product_links.txt")
        return True
        
    except Exception as e:
        print(f"[❌] Error writing to file: {e}")
        return False

def main():
    """Main function"""
    print("[🚀] Starting product URL extraction process...")
    
    # Check if environment variables are set
    if not AIRTABLE_BASE_ID or not AIRTABLE_API_KEY:
        print("[❌] Error: AIRTABLE_BASE and AIRTABLE_TOKEN environment variables must be set")
        return
    
    # Extract URLs from Airtable
    urls = extract_product_urls()
    
    if not urls:
        print("[⚠️] No URLs found, exiting")
        return
    
    # Overwrite the scraped links file
    if overwrite_scraped_links_file(urls):
        print(f"[🎉] Successfully extracted and saved {len(urls)} product URLs")
        
        # Show first few URLs as preview
        print("\n[📋] First 5 URLs preview:")
        for i, url in enumerate(urls[:5], 1):
            print(f"  {i}. {url}")
        
        if len(urls) > 5:
            print(f"  ... and {len(urls) - 5} more URLs")
    else:
        print("[❌] Failed to save URLs to file")

if __name__ == "__main__":
    main()
